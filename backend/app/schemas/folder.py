from typing import List, Optional

from pydantic import BaseModel, Field


class FolderBase(BaseModel):
    name: str
    parent_id: Optional[int] = None


class FolderCreate(FolderBase):
    pass


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None


class FolderRead(FolderBase):
    id: int
    children: List["FolderRead"] = Field(default_factory=list)

    class Config:
        from_attributes = True


FolderRead.model_rebuild()
