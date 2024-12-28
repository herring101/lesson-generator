"""Content analysis processor."""

import json
import logging
from typing import Any, Dict, Union

from ..core.base import PromptParser
from ..core.models import ContentStructure, Topic

logger = logging.getLogger(__name__)


class ContentAnalysisProcessor(PromptParser):
    """コンテンツ分析の出力をパースしてPydanticモデルに変換するプロセッサ"""

    def parse(self, output: str) -> Union[ContentStructure, Topic]:
        """
        コンテンツ分析の出力をパースしてContentStructureまたはTopicモデルに変換

        Args:
            output (str): パース対象の出力テキスト

        Returns:
            Union[ContentStructure, Topic]: パース結果のPydanticモデル

        Raises:
            ValueError: パースに失敗した場合
        """
        try:
            # JSONの抽出
            json_content = self._extract_json(output)
            if not json_content:
                raise ValueError("No JSON content found in output")

            # JSONのパース
            data = self._parse_json_safely(json_content)

            # データ構造の判定とモデル変換
            if self._is_topic_data(data):
                return self._convert_to_topic(data)
            else:
                return self._convert_to_content_structure(data)

        except Exception as e:
            logger.error(f"Error in content analysis: {str(e)}")
            raise ValueError(f"Content analysis failed: {str(e)}")

    def _parse_json_safely(self, json_str: str) -> Dict[str, Any]:
        """JSONを安全にパースする"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            # JSON文字列のクリーニングを試みる
            cleaned_json = self._clean_json_string(json_str)
            return json.loads(cleaned_json)

    def _is_topic_data(self, data: Dict[str, Any]) -> bool:
        """データがトピック形式かどうかを判定"""
        topic_keys = {"title", "key_points", "learning_objectives", "estimated_time"}
        return all(key in data for key in topic_keys)

    def _convert_to_topic(self, data: Dict[str, Any]) -> Topic:
        """データをTopicモデルに変換"""
        # 必要に応じてデータの正規化
        if "outline" not in data:
            data["outline"] = []
        if "estimated_time" not in data:
            data["estimated_time"] = "30分"  # デフォルト値

        return Topic.parse_obj(data)

    def _convert_to_content_structure(self, data: Dict[str, Any]) -> ContentStructure:
        """データをContentStructureモデルに変換"""
        # main_themesが配列でない場合の処理
        if "main_themes" in data and not isinstance(data["main_themes"], list):
            data["main_themes"] = [data["main_themes"]]

        # timelineが存在しない場合の処理
        if "timeline" not in data:
            data["timeline"] = []

        return ContentStructure.parse_obj(data)

    def _clean_json_string(self, json_str: str) -> str:
        """JSONテキストのクリーニング"""
        # 基本的なクリーニング
        cleaned = super()._clean_json_string(json_str)

        # 追加のクリーニング処理
        cleaned = cleaned.replace("'", '"')  # シングルクォートをダブルクォートに置換
        cleaned = cleaned.replace("\\", "\\\\")  # バックスラッシュのエスケープ

        # 不正な制御文字の削除
        cleaned = "".join(
            char for char in cleaned if ord(char) >= 32 or char in "\n\r\t"
        )

        return cleaned
