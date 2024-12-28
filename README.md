# Lesson Generator

LLMを使用して対話形式の授業コンテンツを生成するパッケージです。キャラクター設定に基づいた自然な対話形式で、教育コンテンツを自動生成します。

## 特徴

- 🎭 カスタマイズ可能なキャラクター設定
- 📚 構造化された学習コンテンツの生成
- 💬 自然な対話形式での内容説明
- ✅ 学習目標と達成基準の自動設定
- 📊 コンテンツの自動構造化と分析
- 🔄 継続的な対話生成

## インストール

```bash
git clone https://github.com/[username]/lesson-generator
cd lesson-generator
pip install -r requirements.txt
```

## 環境設定

1. `.env.example`を`.env`にコピー:
```bash
cp .env.example .env
```

2. `.env`ファイルを編集し、必要な設定を行います:
```plaintext
GEMINI_API_KEY=your_api_key_here  # Google Cloud GeminiのAPIキー

# オプション設定
OUTPUT_DIR=output                  # 出力ディレクトリ
MAX_TOPICS_PER_LESSON=5           # レッスンあたりの最大トピック数
GEMINI_MODEL=gemini-exp-1206     # 使用するモデル

# 生成パラメータ
TEMPERATURE=1.0
TOP_P=0.95
TOP_K=64
MAX_OUTPUT_TOKENS=8192
```

## 使用方法

1. 基本的な実行:
```bash
python main.py
```

2. カスタマイズした生成:
```python
from lesson_generator import LessonGenerator

generator = LessonGenerator(
    teacher_persona={
        "name": "先生の名前",
        "personality": "先生の性格設定"
    },
    student_persona={
        "name": "生徒の名前",
        "personality": "生徒の性格設定"
    },
    dialogue_style="casual"  # casual/formal/technical
)

await generator.generate_lesson("input.md", "output")
```

## 出力ファイル

生成されるファイル:
- `topic{XX}_{テーマ名}.md`: 各トピックの構造化された内容
- `dialogue{XX}_{テーマ名}.md`: 各トピックの対話形式の内容
- `combined_lessons.md`: すべてのトピックをまとめたファイル
- `combined_dialogues.md`: すべての対話をまとめたファイル

## 依存パッケージ

- python-dotenv
- google-generativeai
- pydantic

## ライセンス

[MIT License](LICENSE)

## 貢献

バグ報告や機能リクエストは、GitHubのIssueでお願いします。
プルリクエストも歓迎します。

## 作者

herring101
X: [@herring101](https://x.com/herring101426)