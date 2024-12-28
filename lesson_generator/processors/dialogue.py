"""Dialogue generation processor."""

import json
import logging
import re
from typing import Dict, List

from ..core.base import PromptParser
from ..core.models import DialogueChunk, DialogueMessage

logger = logging.getLogger(__name__)


class DialogueProcessor(PromptParser):
    """対話生成の出力をパースしてPydanticモデルに変換するプロセッサ"""

    def __init__(self):
        super().__init__()
        self.required_sections = {"thinking", "content", "dialogue"}

    def parse(self, output: str) -> DialogueChunk:
        """
        対話生成の出力をパースしてDialogueChunkモデルに変換

        Args:
            output (str): パース対象の出力テキスト

        Returns:
            DialogueChunk: パース結果のPydanticモデル

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
            logger.error(f"Error in dialogue parsing: {e}")
            raise ValueError(f"Dialogue parsing failed: {e}")

    def parse_raw_dialogue(self, text: str) -> List[DialogueMessage]:
        """
        生の対話テキストをDialogueMessageのリストに変換

        Args:
            text (str): 対話テキスト

        Returns:
            List[DialogueMessage]: 対話メッセージのリスト
        """
        messages = []
        current_speaker = None
        current_content = []

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            # 新しい発話者を検出
            if ":" in line:
                # 前の発話を保存
                if current_speaker and current_content:
                    messages.append(
                        DialogueMessage(
                            speaker=current_speaker,
                            content="\n".join(current_content).strip(),
                        )
                    )
                    current_content = []

                # 新しい発話を開始
                speaker, content = line.split(":", 1)
                current_speaker = speaker.strip()
                if content.strip():
                    current_content.append(content.strip())
            else:
                # 現在の発話に行を追加
                if current_speaker:
                    current_content.append(line)

        # 最後の発話を保存
        if current_speaker and current_content:
            messages.append(
                DialogueMessage(
                    speaker=current_speaker,
                    content="\n".join(current_content).strip(),
                )
            )

        return messages

    def _parse_json_data(self, json_str: str) -> DialogueChunk:
        """JSONデータをDialogueChunkモデルに変換"""
        try:
            data = json.loads(json_str)

            # 必須フィールドの検証
            missing_fields = self.required_sections - set(data.keys())
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")

            # 対話の検証
            if not self._is_valid_dialogue_format(data["dialogue"]):
                raise ValueError("Invalid dialogue format")

            return DialogueChunk(
                thinking=data["thinking"],
                content=data["content"],
                dialogue=data["dialogue"],
                requires_continuation=data.get("requires_continuation", True),
                key_points_covered=self._normalize_key_points(
                    data.get("key_points_covered", [])
                ),
            )
        except Exception as e:
            logger.error(f"Error parsing JSON data: {e}")
            raise

    def _parse_text_output(self, text: str) -> DialogueChunk:
        """テキスト形式の出力をパース"""
        # タグベースのセクション抽出
        thinking = self._extract_tag_content(text, "thinking")
        content = self._extract_tag_content(text, "content")
        dialogue = self._extract_tag_content(text, "dialogue")

        if not all([thinking, content, dialogue]):
            # タグが見つからない場合はセクションベースで抽出
            sections = self._split_into_sections(text)
            thinking = thinking or sections.get("thinking", "")
            content = content or sections.get("content", "")
            dialogue = dialogue or sections.get("dialogue", "")

        # 必須フィールドの検証
        if not all([thinking, content, dialogue]):
            missing = []
            if not thinking:
                missing.append("thinking")
            if not content:
                missing.append("content")
            if not dialogue:
                missing.append("dialogue")
            raise ValueError(f"Missing required sections: {', '.join(missing)}")

        # 対話形式の検証
        if not self._is_valid_dialogue_format(dialogue):
            raise ValueError("Invalid dialogue format")

        # 継続フラグの判定
        requires_continuation = self._determine_continuation_status(text)

        # カバーされたポイントの抽出
        key_points = self._extract_key_points(text)

        return DialogueChunk(
            thinking=thinking,
            content=content,
            dialogue=dialogue,
            requires_continuation=requires_continuation,
            key_points_covered=key_points,
        )

    def _extract_tag_content(self, text: str, tag: str) -> str:
        """指定されたタグの内容を抽出"""
        pattern = f"<{tag}>(.*?)</{tag}>"
        matches = re.findall(pattern, text, re.DOTALL)
        return matches[0].strip() if matches else ""

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

    def _is_valid_dialogue_format(self, text: str) -> bool:
        """対話形式の妥当性チェック"""
        # 最低2回以上の対話があることを確認
        exchanges = 0
        lines = text.split("\n")

        for line in lines:
            if ":" in line:
                exchanges += 1
                if not self._check_dialogue_line_format(line):
                    return False

        return exchanges >= 2

    def _check_dialogue_line_format(self, line: str) -> bool:
        """対話行の形式チェック"""
        parts = line.split(":", 1)
        if len(parts) != 2:
            return False

        speaker, content = parts
        return bool(speaker.strip() and content.strip())

    def _determine_continuation_status(self, text: str) -> bool:
        """継続フラグの判定"""
        if re.search(r"<CONTINUE>", text, re.IGNORECASE):
            return True
        if re.search(r"<END>", text, re.IGNORECASE):
            return False
        return True

    def _extract_key_points(self, text: str) -> List[str]:
        """カバーされたポイントの抽出"""
        points = []

        # タグベースの抽出
        tag_content = self._extract_tag_content(text, "key_points")
        if tag_content:
            points.extend(self._parse_list_items(tag_content))

        # セクションベースの抽出
        sections = self._split_into_sections(text)
        if "key_points" in sections:
            points.extend(self._parse_list_items(sections["key_points"]))

        return self._normalize_key_points(points)

    def _parse_list_items(self, text: str) -> List[str]:
        """リストアイテムの抽出"""
        items = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith(("-", "*", "•", "·")):
                item = line[1:].strip()
                if item:
                    items.append(item)
        return items

    def _normalize_key_points(self, points: List[str]) -> List[str]:
        """キーポイントの正規化"""
        normalized = list(set(point.strip() for point in points if point.strip()))
        return [
            point if len(point) <= 100 else point[:97] + "..." for point in normalized
        ]
