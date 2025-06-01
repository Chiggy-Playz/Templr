from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


class VariableDefinition(BaseModel):
    name: str = Field(..., description="Variable name")
    type: str = Field(..., description="Variable type: string, number, or date")
    required: bool = Field(default=True, description="Whether this variable is required")
    aliases: List[str] = Field(default_factory=list, description="Alternative names for this variable")


class TemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    slug: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    content: str = Field(..., min_length=1)
    variables: List[VariableDefinition] = Field(default_factory=list)


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    slug: Optional[str] = Field(None, min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    content: Optional[str] = Field(None, min_length=1)
    variables: Optional[List[VariableDefinition]] = None


class TemplateRead(TemplateBase):
    id: uuid.UUID
    owner_id: uuid.UUID

    class Config:
        from_attributes = True
