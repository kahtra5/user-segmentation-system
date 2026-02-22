# Pydantic schemas
from pydantic import BaseModel
from typing import List, Optional, Any
from uuid import UUID


class Rule(BaseModel):
    field: str
    operator: str
    value: Any


class RuleGroup(BaseModel):
    operator: str  # AND / OR
    rules: List[Rule]


class SegmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rule_definition: RuleGroup


class SegmentResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    rule_definition: dict
    is_active: bool

    class Config:
        from_attributes = True