"""Lesson content generator using Gemini API."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import google.generativeai as genai
from dotenv import load_dotenv

from .core.models import DialogueChunk, Topic
from .processors.content import ContentAnalysisProcessor
from .processors.dialogue import DialogueProcessor
from .processors.validation import ValidationProcessor
from .templates.prompts import (
    CONTENT_ANALYSIS_PROMPT,
    DIALOGUE_GENERATION_PROMPT,
    TOPIC_EXTRACTION_PROMPT,
)


class LessonGenerator:
    """対話形式の授業コンテンツを生成するジェネレーター"""

    DEFAULT_MODEL = "gemini-exp-1206"

    def __init__(
        self,
        teacher_persona: Dict[str, str],
        student_persona: Dict[str, str],
        dialogue_style: str = "casual",
        min_exchanges_per_chunk: int = 50,
        max_tokens_per_chunk: int = 8192,
        output_format: str = "both",  # "structured", "raw", or "both"
        env_file: str = ".env",
    ):
        self._setup_logging()
        self._load_environment(env_file)
        self._initialize_api()
        self._setup_personas(teacher_persona, student_persona, dialogue_style)
        self._setup_generation_params(min_exchanges_per_chunk, max_tokens_per_chunk)
        self.output_format = output_format
        self.topic_counter = 1

        # プロセッサーの初期化
        self.content_processor = ContentAnalysisProcessor()
        self.dialogue_processor = DialogueProcessor()
        self.validation_processor = ValidationProcessor()

    def _setup_logging(self):
        """ロギングの設定"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)

            # ファイルハンドラーの設定
            log_file = log_dir / f"lesson_gen_{datetime.now():%Y%m%d_%H%M%S}.log"
            fh = logging.FileHandler(log_file)
            fh.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            self.logger.addHandler(fh)

            # コンソールハンドラーの設定
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            self.logger.addHandler(ch)

    def _load_environment(self, env_file: str):
        """環境変数の読み込み"""
        if not os.path.exists(env_file):
            raise FileNotFoundError(f"Environment file not found: {env_file}")

        load_dotenv(env_file)
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment file")

        # オプション設定の読み込み
        self.output_dir = os.getenv("OUTPUT_DIR", "output")
        self.max_topics = int(os.getenv("MAX_TOPICS_PER_LESSON", "3"))
        self.model_name = os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)

    def _initialize_api(self):
        """API初期化"""
        try:
            genai.configure(api_key=self.api_key)

            # 生成設定
            self.base_config = {
                "temperature": float(os.getenv("TEMPERATURE", "1.0")),
                "top_p": float(os.getenv("TOP_P", "0.95")),
                "top_k": int(os.getenv("TOP_K", "64")),
                "max_output_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "8192")),
            }

            # モデルの初期化
            self.model = genai.GenerativeModel(self.model_name)
            self.logger.info(
                f"Successfully initialized Gemini API with model: {self.model_name}"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini API: {e}")
            raise

    def _setup_personas(
        self,
        teacher_persona: Dict[str, str],
        student_persona: Dict[str, str],
        dialogue_style: str,
    ):
        """ペルソナ設定の初期化"""
        self.teacher = teacher_persona
        self.student = student_persona
        self.dialogue_style = dialogue_style

    def _setup_generation_params(self, min_exchanges: int, max_tokens: int):
        """生成パラメータの設定"""
        self.min_exchanges_per_chunk = min_exchanges
        self.max_tokens_per_chunk = max_tokens

    async def _generate_with_retry(
        self, prompt: str, schema: Optional[Any] = None, max_retries: int = 3
    ) -> str:
        """リトライ機能付きでプロンプトを生成"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Generation attempt {attempt + 1}/{max_retries}")

                # スキーマが指定されている場合は設定を更新
                if schema:
                    config = {**self.base_config, "response_schema": schema}
                    self.model.generation_config = config
                else:
                    self.model.generation_config = self.base_config

                response = self.model.generate_content(prompt)
                self.logger.info("Generation completed")
                self.logger.debug(f"Raw response: {response.text}")

                return response.text

            except Exception as e:
                self.logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise

    async def generate_lesson(
        self, input_file: str = "input.md", output_dir: str = "output"
    ) -> None:
        """レッスンの生成"""
        self.logger.info(f"Starting lesson generation from {input_file}")

        try:
            # 入力ファイルの読み込み
            content = self._read_input_file(input_file)

            # コンテンツ分析
            self.logger.info("Analyzing content structure")
            analysis_prompt = CONTENT_ANALYSIS_PROMPT.format(content=content)
            analysis_response = await self._generate_with_retry(
                analysis_prompt, CONTENT_ANALYSIS_PROMPT.response_schema
            )

            # 構造の解析
            content_structure = self.content_processor.parse(analysis_response)
            self.logger.info(
                f"Successfully parsed content structure with {len(content_structure.main_themes)} main themes"
            )

            # トピックごとの処理
            os.makedirs(output_dir, exist_ok=True)
            combined_content = []
            dialogue_outputs = []
            raw_dialogues = []  # 生の対話テキストを保持するリスト

            self.topic_counter = 1  # カウンターをリセット

            for theme in content_structure.main_themes:
                self.logger.info(f"Processing theme: {theme.title}")

                # トピック抽出と対話生成
                result = await self._process_theme(theme, content, content_structure)

                if result:
                    topic_content, dialogue_content = result
                    # 個別ファイルの出力（番号付き）
                    topic_filename = f"topic{self.topic_counter:02d}_{self._sanitize_filename(theme.title)}.md"
                    dialogue_filename = f"dialogue{self.topic_counter:02d}_{self._sanitize_filename(theme.title)}.md"

                    output_path = os.path.join(output_dir, topic_filename)
                    dialogue_path = os.path.join(output_dir, dialogue_filename)

                    self._write_output(output_path, topic_content)
                    self._write_output(dialogue_path, dialogue_content)

                    combined_content.append(topic_content)
                    dialogue_outputs.append(dialogue_content)

                    # 生の対話テキストを抽出
                    dialogue_text = self._extract_dialogue_text(dialogue_content)
                    if dialogue_text:
                        raw_dialogues.append(dialogue_text)

                    self.topic_counter += 1

            # 全体ファイルの出力
            if combined_content:
                output_path = os.path.join(output_dir, "combined_lessons.md")
                self._write_output(
                    output_path, "\n\n" + "=" * 50 + "\n\n".join(combined_content)
                )

            # 対話全体の出力（対話部分のみを結合）
            if raw_dialogues:
                combined_dialogue = self._combine_dialogues(raw_dialogues)
                dialogue_output_path = os.path.join(output_dir, "combined_dialogues.md")
                self._write_output(dialogue_output_path, combined_dialogue)

            self.logger.info("Lesson generation completed successfully")

        except Exception as e:
            self.logger.error(f"Error during lesson generation: {e}")
            raise

    def _extract_dialogue_text(self, dialogue_content: str) -> str:
        """対話テキスト部分のみを抽出"""
        import re

        # <dialogue>タグ内のテキストを探す
        dialogue_match = re.search(
            r"<dialogue>(.*?)</dialogue>", dialogue_content, re.DOTALL
        )
        if dialogue_match:
            return dialogue_match.group(1).strip()

        # タグがない場合は「対話内容」セクションを探す
        dialogue_section = re.search(
            r"## 対話内容\n\n(.*?)(?=\n\n##|\Z)", dialogue_content, re.DOTALL
        )
        if dialogue_section:
            return dialogue_section.group(1).strip()

        return ""

    def _combine_dialogues(self, dialogues: list[str]) -> str:
        """対話テキストを結合して整形"""
        combined = "# 完全な対話内容\n\n"

        # 各対話をセクションとして結合
        for i, dialogue in enumerate(dialogues, 1):
            combined += f"## セクション {i}\n\n{dialogue}\n\n"

            # セクション間の区切り（最後のセクション以外）
            if i < len(dialogues):
                combined += "---\n\n"

        return combined

    def _sanitize_filename(self, text: str) -> str:
        """ファイル名として安全な文字列に変換"""
        # 非ASCII文字と特殊文字を処理
        filename = "".join(c if c.isalnum() or c in "-_" else "_" for c in text)
        return filename.lower()

    async def _process_theme(
        self, theme: Any, content: str, structure: Any
    ) -> Optional[Tuple[str, str]]:
        """テーマの処理"""
        self.logger.info(f"Processing theme: {theme.title}")

        try:
            # トピック抽出
            topic_prompt = TOPIC_EXTRACTION_PROMPT.format(
                content=content,
                main_theme=theme.title,
                structure=structure.model_dump_json(),
            )

            self.logger.debug(f"Generated topic prompt for theme: {theme.title}")

            topic_response = await self._generate_with_retry(
                topic_prompt, TOPIC_EXTRACTION_PROMPT.response_schema
            )

            self.logger.debug(
                f"Raw topic response: {topic_response[:200]}..."
            )  # 最初の200文字のみログ出力

            # ContentAnalysisProcessorを使ってトピックとして解析
            try:
                topic = self.content_processor.parse(topic_response)
                if not isinstance(topic, Topic):
                    self.logger.error(f"Invalid topic data type: {type(topic)}")
                    return None

                # トピックの基本検証
                if not hasattr(topic, "title") or not topic.title:
                    self.logger.error("Invalid topic: missing title")
                    return None

                if (
                    not hasattr(topic, "learning_objectives")
                    or not topic.learning_objectives
                ):
                    self.logger.error("Invalid topic: missing learning objectives")
                    return None

                self.logger.info(f"Successfully parsed topic: {topic.title}")

            except Exception as e:
                self.logger.error(f"Error parsing topic data: {str(e)}")
                self.logger.debug(f"Parse error details: {type(e).__name__}: {str(e)}")
                return None

            # 対話生成
            try:
                dialogue_prompt = DIALOGUE_GENERATION_PROMPT.format(
                    original_content=content,  # 元の文書内容を追加
                    topic_info=topic.model_dump_json(),
                    content_structure=structure.model_dump_json(),  # 構造情報を追加
                    current_theme=theme.model_dump_json(),  # 現在のテーマ情報を追加
                    teacher_name=self.teacher["name"],
                    teacher_personality=self.teacher["personality"],
                    student_name=self.student["name"],
                    student_personality=self.student["personality"],
                    dialogue_style=self.dialogue_style,
                    min_exchanges=self.min_exchanges_per_chunk,
                )

                self.logger.debug("Generated dialogue prompt with full context")

                dialogue_response = await self._generate_with_retry(
                    dialogue_prompt,
                    None,  # スキーマは不要
                )

                self.logger.debug(
                    f"Raw dialogue response length: {len(dialogue_response)}"
                )

                # 出力フォーマットに応じた処理
                if self.output_format == "structured":
                    dialogue_data = self.dialogue_processor.parse(dialogue_response)
                    return self._format_topic_content(
                        topic
                    ), self._format_structured_dialogue(dialogue_data)

                elif self.output_format == "raw":
                    return self._format_topic_content(topic), dialogue_response

                else:  # "both"
                    try:
                        dialogue_data = self.dialogue_processor.parse(dialogue_response)
                        formatted_dialogue = self._format_structured_dialogue(
                            dialogue_data
                        )
                        return (
                            self._format_topic_content(topic),
                            f"{formatted_dialogue}\n\n原文:\n{dialogue_response}",
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"Error processing structured dialogue: {e}"
                        )
                        self.logger.info("Falling back to raw dialogue output")
                        return self._format_topic_content(topic), dialogue_response

            except Exception as e:
                self.logger.error(f"Error generating dialogue: {str(e)}")
                return None

        except Exception as e:
            self.logger.error(f"Error processing theme {theme.title}: {str(e)}")
            self.logger.debug(f"Processing error details: {type(e).__name__}: {str(e)}")
            return None

    def _format_topic_content(self, topic: Topic) -> str:
        """トピックの内容をMarkdown形式に整形"""
        try:
            lines = [
                f"# {topic.title}\n",
                "## 学習目標",
                "\n".join(
                    [
                        f"- {obj.objective}\n  - 達成基準: {', '.join(obj.success_criteria)}\n  - 評価方法: {obj.evaluation_method}"
                        for obj in topic.learning_objectives
                    ]
                ),
                "\n## 重要ポイント",
                "\n".join([f"- {point}" for point in topic.key_points]),
                "\n## アウトライン",
                "\n".join([f"1. {item}" for item in topic.outline])
                if topic.outline
                else "（アウトラインなし）",
                f"\n予想所要時間: {topic.estimated_duration}",
            ]

            return "\n\n".join(lines)

        except Exception as e:
            self.logger.error(f"Error formatting topic content: {str(e)}")
            raise

    def _format_structured_dialogue(self, dialogue: DialogueChunk) -> str:
        """対話の構造化データをMarkdown形式に整形"""
        lines = [
            "# 対話の構造化データ",
            "\n## 思考プロセス",
            dialogue.thinking,
            "\n## コンテンツ概要",
            dialogue.content,
            "\n## 対話内容",
            dialogue.dialogue,
            "\n## カバーされたポイント",
            "\n".join([f"- {point}" for point in dialogue.key_points_covered]),
            f"\n続きが必要: {'はい' if dialogue.requires_continuation else 'いいえ'}",
        ]
        return "\n\n".join(lines)

    def _read_input_file(self, file_path: str) -> str:
        """入力ファイルの読み込み"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.logger.info(
                    f"Successfully read input file: {len(content)} characters"
                )
                return content
        except Exception as e:
            self.logger.error(f"Failed to read input file: {e}")
            raise

    def _write_output(self, path: str, content: str) -> None:
        """出力ファイルの書き込み"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.info(f"Successfully wrote output to {path}")
        except Exception as e:
            self.logger.error(f"Failed to write output file: {e}")
            raise

    def _sanitize_filename(self, text: str) -> str:
        """ファイル名として安全な文字列に変換"""
        # 非ASCII文字と特殊文字を処理
        filename = "".join(c if c.isalnum() or c in "-_" else "_" for c in text)
        return filename.lower()
