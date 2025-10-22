from collections import defaultdict
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.folder import Folder
from app.models.user import User
from app.schemas.folder import FolderCreate, FolderRead, FolderUpdate

router = APIRouter(prefix="/folders", tags=["folders"])


def _build_folder_tree(folders: List[Folder]) -> List[FolderRead]:
    node_map: Dict[int, FolderRead] = {}
    children_map: Dict[int | None, List[FolderRead]] = defaultdict(list)

    for folder in folders:
        node = FolderRead.model_validate(folder, from_attributes=True)
        node.children = []
        node_map[folder.id] = node
        children_map[folder.parent_id].append(node)

    def attach_children(node: FolderRead):
        node.children = children_map.get(node.id, [])
        for child in node.children:
            attach_children(child)

    roots = children_map.get(None, [])
    for root in roots:
        attach_children(root)
    return roots


@router.get("/tree", response_model=list[FolderRead])
def get_folder_tree(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    folders = db.query(Folder).filter(Folder.owner_id == current_user.id).all()
    return _build_folder_tree(folders)


@router.post("", response_model=FolderRead, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.parent_id:
        parent = (
            db.query(Folder)
            .filter(Folder.id == payload.parent_id, Folder.owner_id == current_user.id)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent folder not found")

    folder = Folder(name=payload.name, parent_id=payload.parent_id, owner_id=current_user.id)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return FolderRead.model_validate(folder, from_attributes=True)


@router.patch("/{folder_id}", response_model=FolderRead)
def update_folder(
    folder_id: int,
    payload: FolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    folder = (
        db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == current_user.id).first()
    )
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if payload.name:
        folder.name = payload.name
    if payload.parent_id is not None:
        if payload.parent_id == folder.id:
            raise HTTPException(status_code=400, detail="Folder cannot be its own parent")
        parent = (
            db.query(Folder)
            .filter(Folder.id == payload.parent_id, Folder.owner_id == current_user.id)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent folder not found")
        folder.parent_id = payload.parent_id

    db.commit()
    db.refresh(folder)
    return FolderRead.model_validate(folder, from_attributes=True)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    folder = (
        db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == current_user.id).first()
    )
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    db.delete(folder)
    db.commit()
