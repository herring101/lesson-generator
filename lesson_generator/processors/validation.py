"""Validation processor for lesson content."""

import json
import logging
import re
from typing import Dict, List, Tuple

from ..core.base import PromptParser
from ..core.models import ValidationResult

logger = logging.getLogger(__name__)


class ValidationProcessor(PromptParser):
    """検証結果の出力をパースしてPydanticモデルに変換するプロセッサ"""

    def __init__(self):
        super().__init__()
        self.error_keywords = {
            "error",
            "invalid",
            "missing",
            "failed",
            "incorrect",
            "エラー",
            "無効",
            "欠落",
            "失敗",
            "不正",
        }
        self.warning_keywords = {
            "warning",
            "suggest",
            "recommend",
            "consider",
            "might",
            "警告",
            "提案",
            "推奨",
            "検討",
            "かもしれない",
        }

    def parse(self, output: str) -> ValidationResult:
        """
        検証結果の出力をパースしてValidationResultモデルに変換

        Args:
            output (str): パース対象の出力テキスト

        Returns:
            ValidationResult: パース結果のPydanticモデル

        Raises:
            ValueError: パースに失敗した場合
        """
        try:
            # まずJSONとしてのパースを試みる
            json_content = self._extract_json(output)
            if json_content:
                return self._parse_json_data(json_content)

            # JSON形式でない場合はテキストとしてパース
            return self._parse_text_output(output)

        except Exception as e:
            logger.error(f"Error in validation parsing: {e}")
            raise ValueError(f"Validation parsing failed: {e}")

    def _parse_json_data(self, json_str: str) -> ValidationResult:
        """JSONデータをValidationResultモデルに変換"""
        try:
            data = json.loads(json_str)

            # is_validの判定
            is_valid = data.get("is_valid", False)
            if isinstance(is_valid, str):
                is_valid = is_valid.lower() in {"true", "yes", "1"}

            return ValidationResult(
                is_valid=is_valid,
                errors=self._normalize_messages(data.get("errors", [])),
                warnings=self._normalize_messages(data.get("warnings", [])),
            )
        except Exception as e:
            logger.error(f"Error parsing JSON data: {e}")
            raise

    def _parse_text_output(self, text: str) -> ValidationResult:
        """テキスト形式の出力をパース"""
        # セクション分割
        sections = self._split_into_sections(text)

        # 結果の判定
        is_valid = self._determine_validation_result(text, sections)

        # エラーと警告の抽出
        errors = []
        warnings = []

        # タグベースの抽出
        errors.extend(self._extract_tagged_messages(text, "errors"))
        warnings.extend(self._extract_tagged_messages(text, "warnings"))

        # セクションベースの抽出
        if not errors and "errors" in sections:
            errors.extend(self._extract_list_items(sections["errors"]))
        if not warnings and "warnings" in sections:
            warnings.extend(self._extract_list_items(sections["warnings"]))

        # キーワードベースの分類
        if not errors and not warnings:
            errors, warnings = self._classify_messages(text)

        return ValidationResult(
            is_valid=is_valid,
            errors=self._normalize_messages(errors),
            warnings=self._normalize_messages(warnings),
        )

    def _determine_validation_result(self, text: str, sections: Dict[str, str]) -> bool:
        """検証結果の判定"""
        # 明示的な結果表明を探す
        result_patterns = [
            r"(検証結果|validation\s+result)[:：]\s*(成功|失敗|passed|failed)",
            r"(is_valid|valid|結果)[:：]?\s*(true|false|yes|no|はい|いいえ)",
            r"^(成功|失敗|passed|failed)$",
        ]

        text_lower = text.lower()
        for pattern in result_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                result = match.group(2).lower()
                return result in {"成功", "passed", "true", "yes", "はい"}

        # エラーメッセージの有無で判定
        has_errors = any(keyword in text_lower for keyword in self.error_keywords)

        return not has_errors

    def _extract_tagged_messages(self, text: str, tag: str) -> List[str]:
        """タグ付きメッセージの抽出"""
        pattern = f"<{tag}>(.*?)</{tag}>"
        matches = re.findall(pattern, text, re.DOTALL)

        messages = []
        for match in matches:
            messages.extend(self._extract_list_items(match))

        return messages

    def _classify_messages(self, text: str) -> Tuple[List[str], List[str]]:
        """メッセージの分類"""
        lines = text.split("\n")
        errors = []
        warnings = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            line_lower = line.lower()
            if any(keyword in line_lower for keyword in self.error_keywords):
                errors.append(line)
            elif any(keyword in line_lower for keyword in self.warning_keywords):
                warnings.append(line)

        return errors, warnings

    def _normalize_messages(self, messages: List[str]) -> List[str]:
        """メッセージの正規化"""
        normalized = []
        seen = set()

        for msg in messages:
            # 基本的なクリーニング
            cleaned = re.sub(r"\s+", " ", msg).strip()
            # 先頭の記号を削除
            cleaned = re.sub(r"^[-*•·]\s*", "", cleaned)

            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                normalized.append(cleaned)

        return normalized

    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """テキストをセクションに分割"""
        sections = {}
        current_section = None
        current_content = []

        for line in text.split("\n"):
            if line.strip().startswith("#"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line.lstrip("#").strip().lower()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _extract_list_items(self, text: str) -> List[str]:
        """リストアイテムの抽出"""
        items = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith(("-", "*", "•", "·")):
                item = re.sub(r"^[-*•·]\s*", "", line)
                if item:
                    items.append(item)
            elif line and not line.startswith("#"):
                items.append(line)
        return items
