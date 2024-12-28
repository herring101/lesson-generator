"""Data models for lesson generation."""

from typing import List, Optional

from pydantic import BaseModel, Field, validator


class BaseSchema(BaseModel):
    """基本スキーマ"""

    class Config:
        extra = "allow"
        populate_by_name = True


class Theme(BaseSchema):
    """テーマ情報"""

    title: str
    summary: str
    related_topics: Optional[List[str]] = Field(default_factory=list)

    @validator("title")
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class TimelineEvent(BaseSchema):
    """時系列イベント"""

    period: str
    events: List[str]

    @validator("events")
    def validate_events(cls, v):
        if not v:
            raise ValueError("Events list cannot be empty")
        return v


class ContentStructure(BaseSchema):
    """コンテンツ構造"""

    main_themes: List[Theme]
    timeline: Optional[List[TimelineEvent]] = Field(default_factory=list)


class LearningObjective(BaseSchema):
    """学習目標"""

    objective: str  # descriptionからobjectiveに変更
    success_criteria: List[str]
    evaluation_method: Optional[str] = Field(default="口頭での確認")

    @validator("success_criteria")
    def validate_criteria(cls, v):
        if not v:
            raise ValueError("At least one success criterion is required")
        return v

    @validator("objective")
    def validate_objective(cls, v):
        if not v.strip():
            raise ValueError("Objective cannot be empty")
        return v.strip()


class Topic(BaseSchema):
    """トピック情報"""

    title: str
    key_points: List[str]
    learning_objectives: List[LearningObjective]
    outline: Optional[List[str]] = Field(default_factory=list, alias="content_outline")
    estimated_duration: str = Field(alias="estimated_time")

    @validator("key_points")
    def validate_key_points(cls, v):
        if not v:
            raise ValueError("At least one key point is required")
        return v

    @validator("learning_objectives")
    def validate_objectives(cls, v):
        if not v:
            raise ValueError("At least one learning objective is required")
        return v

    @validator("estimated_duration")
    def validate_duration(cls, v):
        if not v.strip():
            raise ValueError("Estimated duration cannot be empty")
        return v.strip()


class DialogueChunk(BaseSchema):
    """対話チャンク"""

    thinking: str = Field(..., min_length=10)
    content: str = Field(..., min_length=10)
    dialogue: str = Field(..., min_length=20)
    requires_continuation: bool = Field(...)
    key_points_covered: List[str] = Field(..., min_items=1)

    @validator("key_points_covered")
    def validate_key_points_covered(cls, v):
        if not v:
            raise ValueError("At least one covered key point is required")
        return v


class ValidationResult(BaseSchema):
    """検証結果"""

    is_valid: bool = Field(...)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# 対話生成用の新しいモデル
class DialogueMessage(BaseSchema):
    """対話メッセージ"""

    speaker: str
    content: str

    @validator("content")
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()


class DialogueSection(BaseSchema):
    """対話セクション"""

    title: str
    messages: List[DialogueMessage]
    summary: Optional[str] = None

    @validator("messages")
    def validate_messages(cls, v):
        if not v:
            raise ValueError("At least one message is required")
        return v


class CompleteLessonContent(BaseSchema):
    """完全なレッスンコンテンツ"""

    title: str
    overview: str
    objectives: List[str]
    dialogues: List[DialogueSection]
    summary: str
    key_points: List[str]
    additional_notes: Optional[List[str]] = Field(default_factory=list)
