import uuid

from pydantic import BaseModel, Field, field_validator


class VariableDefinition(BaseModel):
    name: str = Field(..., description="Variable name")
    type: str = Field(..., description="Variable type: string, number, or date")
    required: bool = Field(default=True, description="Whether this variable is required")
    aliases: list[str] = Field(default_factory=list, description="Alternative names for this variable")


class TemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    slug: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_/-]+$")
    content: str = Field(..., min_length=1)
    variables: list[VariableDefinition] = Field(default_factory=list)
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if v.endswith('/'):
            raise ValueError('Slug cannot end with a forward slash')
        if v.startswith('/'):
            raise ValueError('Slug cannot start with a forward slash')
        return v


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    slug: str | None = Field(None, min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_/-]+$")
    content: str | None = Field(None, min_length=1)
    variables: list | VariableDefinition | None = None
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v.endswith('/'):
            raise ValueError('Slug cannot end with a forward slash')
        if v.startswith('/'):
            raise ValueError('Slug cannot start with a forward slash')
        return v


class TemplateRead(TemplateBase):
    id: uuid.UUID
    owner_id: uuid.UUID

    class Config:
        from_attributes = True
