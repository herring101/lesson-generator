"""Prompt templates for various generation tasks."""

from ..core.base import PromptTemplate
from ..core.schemas import (
    CONTENT_ANALYSIS_SCHEMA,
    TOPIC_SCHEMA,
    VALIDATION_SCHEMA,
)

# コンテンツ分析プロンプト
CONTENT_ANALYSIS_PROMPT = PromptTemplate(
    template="""以下の文書から主要なテーマと時系列情報を抽出し、指定された形式でJSONを出力してください。

入力文書：
{content}

以下の形式でJSONを出力してください：

```json
{{
    "main_themes": [
        {{
            "title": "テーマの名称",
            "summary": "テーマの概要",
            "related_topics": [
                "関連するトピック1",
                "関連するトピック2"
            ]
        }}
    ],
    "timeline": [
        {{
            "period": "時代や時期",
            "events": [
                "出来事1",
                "出来事2"
            ]
        }}
    ]
}}
```

注意点：
1. 各テーマは明確で具体的なタイトルを付けてください
2. 概要は1-2文で簡潔にまとめてください
3. 関連トピックは他のテーマとの関連性を示してください
4. 時系列情報は重要な出来事を時代順に並べてください
""",
    required_variables=["content"],
    description="教育コンテンツの構造分析を行うためのプロンプト",
    response_schema=CONTENT_ANALYSIS_SCHEMA,
)

# トピック抽出プロンプト
TOPIC_EXTRACTION_PROMPT = PromptTemplate(
    template="""以下の文書からトピックの詳細情報を抽出し、指定された形式でJSONを出力してください。

# 入力文書
{content}

# 分析の観点
1. 主要テーマ: {main_theme}
2. 文書構造: {structure}

以下の形式でJSONを出力してください：

```json
{{
    "title": "トピックのタイトル",
    "key_points": [
        "重要なポイント1",
        "重要なポイント2"
    ],
    "learning_objectives": [
        {{
            "objective": "学習目標の説明",
            "success_criteria": [
                "達成基準1",
                "達成基準2"
            ],
            "evaluation_method": "評価方法"
        }}
    ],
    "outline": [
        "説明項目1",
        "説明項目2"
    ],
    "estimated_time": "15分"
}}
```

注意点：
1. タイトルは具体的で理解しやすいものにしてください
2. 重要ポイントは5-7個程度に収めてください
3. 各学習目標には必ず達成基準と評価方法を含めてください
4. アウトラインは論理的な順序で構成してください
5. 所要時間は5-30分の範囲で設定してください
""",
    required_variables=["content", "main_theme", "structure"],
    description="文書からトピックを抽出するためのプロンプト",
    response_schema=TOPIC_SCHEMA,
)

# 対話生成プロンプト
DIALOGUE_GENERATION_PROMPT = PromptTemplate(
    template="""以下の設定に基づいて教育的な対話を生成してください。

# 元の文書内容
{original_content}

# トピック情報
{topic_info}

# コンテンツ構造
{content_structure}

# 現在のテーマ
{current_theme}

# キャラクター設定
教師（{teacher_name}）:
{teacher_personality}

生徒（{student_name}）:
{student_personality}

対話スタイル: {dialogue_style}

# 展開要件
1. 各概念について以下の順序で展開してください：
   - 概念の導入（身近な例や比喩を使用）
   - 詳細な説明（具体例を交えながら）
   - 実践的な応用（どのように使えるか）
   - 関連する概念との繋がり
   - まとめと次の概念への橋渡し

2. 生徒の質問は以下のパターンを含めてください：
   - 理解確認の質問
   - 具体例を求める質問
   - 応用に関する質問
   - 関連概念についての質問
   - 前の説明との関連を確認する質問

3. 教師の説明は以下の要素を含めてください：
   - 概念の基本説明
   - 具体例（最低3つ）
   - 応用方法の説明
   - 関連する概念との関係性
   - 生徒の理解度確認

4. 対話の展開：
   - 1つの概念について最低10往復の対話
   - 各説明は段階的に深める
   - 定期的に前の内容を参照
   - 具体例を豊富に使用

# 出力形式
<thinking>
今から説明すべき内容や、どのように展開するかについての考察を書いてください。
特に、元の文書のどの部分を使用するかを明確にしてください。
</thinking>

<content>
この対話で扱う具体的な内容や重要なポイントを書いてください。
すべての内容が元の文書に基づいていることを確認してください。
</content>

<dialogue>
ここは非常に長く充実させてください。
{teacher_name}: （対話内容）
{student_name}: （対話内容）
{teacher_name}: （対話内容）
{student_name}: （対話内容）
...({min_exchanges}往復以上)
{teacher_name}: （対話内容）
{student_name}: （対話内容）
</dialogue>

# 注意点：
1. **対話は少なくとも{min_exchanges}往復以上含めてください**
2. キャラクターの個性を自然に表現してください
3. 各発言は文脈に沿った自然な流れにしてください
4. 説明は段階的で分かりやすくしてください
5. 生徒の質問は理解を深めるものにしてください
6. 文書に記載のない情報は使用しないでください
7. 一つの概念について十分に深掘りしてから次に進んでください
8. 具体例は必ず3つ以上含めてください
9. 定期的に前の説明を参照・復習してください

<key_points>
- 実際にカバーされた重要ポイントをリストアップしてください
- それぞれのポイントが元の文書のどの部分に基づいているかを明記してください
</key_points>

続きが必要な場合は<CONTINUE>タグ、完了の場合は<END>タグを付けてください。
""",
    required_variables=[
        "original_content",  # 追加: 元の文書内容
        "topic_info",
        "content_structure",  # 追加: コンテンツ全体の構造
        "current_theme",  # 追加: 現在のテーマ
        "teacher_name",
        "teacher_personality",
        "student_name",
        "student_personality",
        "dialogue_style",
        "min_exchanges",
    ],
    description="対話形式の教育コンテンツを生成するためのプロンプト",
)

# コンテンツ検証プロンプト
CONTENT_VALIDATION_PROMPT = PromptTemplate(
    template="""以下の対話内容を検証し、結果を出力してください。

# 対話内容
{dialogue_content}

# 検証基準
1. キャラクター性
- 教師（{teacher_name}）の特徴: {teacher_traits}
- 生徒（{student_name}）の特徴: {student_traits}

2. 学習目標
{learning_objectives}

3. 重要ポイント
{key_points}

以下の形式で出力してください：

# 全体評価
<is_valid>true/false</is_valid>
<quality>A/B/C/D</quality>

# キャラクター評価
<character_consistency>A/B/C/D</character_consistency>

<errors>
- 発見された問題点をリストアップ
</errors>

<warnings>
- 改善が望ましい点をリストアップ
</warnings>

# 内容評価
<covered_points>
- カバーされた目標や重要ポイントをリストアップ
</covered_points>

<missing_points>
- 不足している内容をリストアップ
</missing_points>

# 改善提案
<improvements>
- 具体的な改善提案をリストアップ
</improvements>

評価基準：
- A: 優れている（90-100点）
- B: 良好（80-89点）
- C: 改善の余地あり（70-79点）
- D: 要改善（69点以下）
""",
    required_variables=[
        "dialogue_content",
        "teacher_name",
        "teacher_traits",
        "student_name",
        "student_traits",
        "learning_objectives",
        "key_points",
    ],
    description="対話内容の検証を行うためのプロンプト",
    response_schema=VALIDATION_SCHEMA,
)
