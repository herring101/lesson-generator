"""Lesson generator sample script."""

import asyncio
import logging
import os

from lesson_generator import LessonGenerator

# gRPCのwarningを抑制
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"
os.environ["GRPC_POLL_STRATEGY"] = "epoll1"

# ロギングの設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting lesson generation process")

    try:
        # ジェネレーターの初期化
        generator = LessonGenerator(
            teacher_persona={
                "name": "魔理沙",
                "personality": """
***ボケと知識を自在に操る解説役***

* 性格:
    * 自信家で、豊富な知識を持つ解説役
    * 分かりやすい解説を心がけるが、時折専門用語を多用
    * ボケをかますのが好き
    * 霊夢のツッコミをあしらうことも
* 口調:
    * 「～だぜ」「～なのぜ」を語尾につける
    * 自信に満ちた口調
    * ボケる時は大げさな表現を使用
""",
            },
            student_persona={
                "name": "霊夢",
                "personality": """
***素直でツッコミ役の常識人***

* 性格:
    * 基本的に常識的で真面目
    * 素直に質問し、理解するまで聞き返す
    * 魔理沙のボケに的確にツッコミを入れる
* 口調:
    * タメ口でフランク
    * 「それってどういうこと？」などの質問が多い
    * ツッコミ時は「はぁ？」などの強い口調も
""",
            },
            dialogue_style="casual",
            min_exchanges_per_chunk=5,
            output_format="both",  # 構造化データと生の対話の両方を出力
        )

        # 授業の生成
        logger.info("Generating lesson content")
        await generator.generate_lesson("input.md", "output")

        logger.info("Lesson generation completed successfully!")
        logger.info("Generated files:")
        logger.info("- output/combined_lessons.md (トピックの概要)")
        logger.info("- output/combined_dialogues.md (全対話内容)")
        logger.info("- output/topic_*.md (個別トピックファイル)")
        logger.info("- output/dialogue_*.md (個別対話ファイル)")

    except Exception as e:
        logger.error(f"Error during lesson generation: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
