"""Gemini API schemas for lesson generation."""

from google.ai.generativelanguage_v1beta.types import content

# コンテンツ分析スキーマ
CONTENT_ANALYSIS_SCHEMA = content.Schema(
    type=content.Type.OBJECT,
    properties={
        "main_themes": content.Schema(
            type=content.Type.ARRAY,
            items=content.Schema(
                type=content.Type.OBJECT,
                properties={
                    "title": content.Schema(type=content.Type.STRING),
                    "summary": content.Schema(type=content.Type.STRING),
                    "related_topics": content.Schema(
                        type=content.Type.ARRAY,
                        items=content.Schema(type=content.Type.STRING),
                    ),
                },
            ),
        ),
        "timeline": content.Schema(
            type=content.Type.ARRAY,
            items=content.Schema(
                type=content.Type.OBJECT,
                properties={
                    "period": content.Schema(type=content.Type.STRING),
                    "events": content.Schema(
                        type=content.Type.ARRAY,
                        items=content.Schema(type=content.Type.STRING),
                    ),
                },
            ),
        ),
    },
)

# トピック抽出スキーマ
TOPIC_SCHEMA = content.Schema(
    type=content.Type.OBJECT,
    properties={
        "title": content.Schema(type=content.Type.STRING),
        "key_points": content.Schema(
            type=content.Type.ARRAY,
            items=content.Schema(type=content.Type.STRING),
        ),
        "learning_objectives": content.Schema(
            type=content.Type.ARRAY,
            items=content.Schema(
                type=content.Type.OBJECT,
                properties={
                    "objective": content.Schema(type=content.Type.STRING),
                    "success_criteria": content.Schema(
                        type=content.Type.ARRAY,
                        items=content.Schema(type=content.Type.STRING),
                    ),
                    "evaluation_method": content.Schema(type=content.Type.STRING),
                },
            ),
        ),
        "outline": content.Schema(
            type=content.Type.ARRAY,
            items=content.Schema(type=content.Type.STRING),
        ),
        "estimated_time": content.Schema(type=content.Type.STRING),
    },
)

# 対話生成スキーマ
DIALOGUE_SCHEMA = content.Schema(
    type=content.Type.OBJECT,
    properties={
        "thinking": content.Schema(type=content.Type.STRING),
        "content": content.Schema(type=content.Type.STRING),
        "dialogue": content.Schema(type=content.Type.STRING),
        "requires_continuation": content.Schema(type=content.Type.BOOLEAN),
        "key_points_covered": content.Schema(
            type=content.Type.ARRAY,
            items=content.Schema(type=content.Type.STRING),
        ),
    },
)

# 検証スキーマ
VALIDATION_SCHEMA = content.Schema(
    type=content.Type.OBJECT,
    properties={
        "overall_assessment": content.Schema(
            type=content.Type.OBJECT,
            properties={
                "is_valid": content.Schema(type=content.Type.BOOLEAN),
                "quality_score": content.Schema(type=content.Type.STRING),
            },
        ),
        "character_assessment": content.Schema(
            type=content.Type.OBJECT,
            properties={
                "consistency_score": content.Schema(type=content.Type.STRING),
                "issues": content.Schema(
                    type=content.Type.ARRAY,
                    items=content.Schema(type=content.Type.STRING),
                ),
            },
        ),
        "content_assessment": content.Schema(
            type=content.Type.OBJECT,
            properties={
                "covered_objectives": content.Schema(
                    type=content.Type.ARRAY,
                    items=content.Schema(type=content.Type.STRING),
                ),
                "missing_points": content.Schema(
                    type=content.Type.ARRAY,
                    items=content.Schema(type=content.Type.STRING),
                ),
            },
        ),
        "improvements": content.Schema(
            type=content.Type.ARRAY,
            items=content.Schema(type=content.Type.STRING),
        ),
    },
)
