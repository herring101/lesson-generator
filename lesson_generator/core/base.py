"""Base classes and utilities for the lesson generator."""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from google.ai.generativelanguage_v1beta.types import content
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class JSONExtractor:
    """JSON抽出のためのユーティリティクラス"""

    @staticmethod
    def extract_json(text: str) -> Optional[str]:
        """テキストからJSON部分を抽出"""
        # バックティックで囲まれたJSONを探す
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        # 単純な波括弧で囲まれた部分を探す
        braces_match = re.search(r"\{.*\}", text, re.DOTALL)
        if braces_match:
            return braces_match.group(0).strip()

        return None

    @staticmethod
    def clean_json_string(json_str: str) -> str:
        """JSONテキストのクリーニング"""
        cleaned = re.sub(r"\s+", " ", json_str)
        cleaned = re.sub(r'(?<!\\)"', '\\"', cleaned)
        return cleaned.strip()


@dataclass
class PromptTemplate:
    """プロンプトテンプレートの基本クラス"""

    template: str
    required_variables: List[str]
    example_input: Optional[Dict] = None
    example_output: Optional[str] = None
    description: Optional[str] = None
    response_schema: Optional[content.Schema] = None

    def format(self, **kwargs) -> str:
        """テンプレート変数を置換してプロンプトを生成"""
        try:
            # 必要な変数が全て提供されているか確認
            missing_vars = set(self.required_variables) - set(kwargs.keys())
            if missing_vars:
                raise ValueError(f"Missing required variables: {missing_vars}")

            # 変数の型チェック
            for var_name, var_value in kwargs.items():
                if var_value is None:
                    raise ValueError(f"Variable {var_name} cannot be None")

            # テンプレートのフォーマット
            formatted = self.template.format(**kwargs)
            return formatted

        except KeyError as e:
            logger.error(f"KeyError in prompt formatting: {e}")
            raise ValueError(f"Invalid variable name: {e}")
        except Exception as e:
            logger.error(f"Error formatting prompt: {e}")
            raise

    def with_schema(
        self, schema_model: Union[BaseModel, Dict[str, Any]]
    ) -> "PromptTemplate":
        """Pydanticモデルまたはスキーマ定義からレスポンススキーマを設定"""
        try:
            if isinstance(schema_model, BaseModel):
                schema_dict = schema_model.schema()
            else:
                schema_dict = schema_model

            self.response_schema = self._convert_to_gemini_schema(schema_dict)
            return self

        except Exception as e:
            logger.error(f"Failed to set response schema: {e}")
            raise

    def _convert_to_gemini_schema(self, schema_dict: Dict[str, Any]) -> content.Schema:
        """JSONスキーマをGemini APIのスキーマ形式に変換"""
        schema_type = schema_dict.get("type", "object")

        if schema_type == "object":
            properties = {}
            for prop_name, prop_schema in schema_dict.get("properties", {}).items():
                properties[prop_name] = self._convert_to_gemini_schema(prop_schema)

            return content.Schema(
                type=content.Type.OBJECT,
                properties=properties,
                required=schema_dict.get("required", []),
            )

        elif schema_type == "array":
            items_schema = self._convert_to_gemini_schema(schema_dict["items"])
            return content.Schema(type=content.Type.ARRAY, items=items_schema)

        elif schema_type == "string":
            return content.Schema(
                type=content.Type.STRING, enum=schema_dict.get("enum", [])
            )

        elif schema_type == "number":
            return content.Schema(
                type=content.Type.NUMBER,
                minimum=schema_dict.get("minimum"),
                maximum=schema_dict.get("maximum"),
            )

        elif schema_type == "integer":
            return content.Schema(
                type=content.Type.INTEGER,
                minimum=schema_dict.get("minimum"),
                maximum=schema_dict.get("maximum"),
            )

        elif schema_type == "boolean":
            return content.Schema(type=content.Type.BOOLEAN)

        else:
            raise ValueError(f"Unsupported schema type: {schema_type}")

    def get_gemini_config(self) -> Dict[str, Any]:
        """Gemini API用の設定を生成"""
        config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
        }

        if self.response_schema:
            config.update(
                {
                    "response_schema": self.response_schema,
                    "response_mime_type": "application/json",
                }
            )

        return config


class PromptParser(ABC):
    """プロンプト出力のパーサーの基本クラス"""

    def __init__(self):
        self.json_extractor = JSONExtractor()

    @abstractmethod
    def parse(self, output: str) -> Any:
        """出力をパースして構造化されたデータに変換"""
        pass

    def _extract_json(self, text: str) -> Optional[str]:
        """テキストからJSON部分を抽出"""
        return self.json_extractor.extract_json(text)

    def _clean_json_string(self, json_str: str) -> str:
        """JSONテキストのクリーニング"""
        return self.json_extractor.clean_json_string(json_str)

    def parse_with_raw(self, output: str) -> tuple[Any, str]:
        """構造化データと生のテキストの両方を返す"""
        try:
            parsed_data = self.parse(output)
            return parsed_data, output
        except (ValidationError, ValueError) as e:
            logger.error(f"Error parsing output: {e}")
            raise
