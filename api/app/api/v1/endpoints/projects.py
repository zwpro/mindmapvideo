"""项目 CRUD 端点。"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.project import Project, ProjectCreate, ProjectUpdate
from app.services import project_service

router = APIRouter()


@router.get("", response_model=list[Project], summary="项目列表")
async def list_projects() -> list[Project]:
    return project_service.list_projects()


@router.post(
    "",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
)
async def create_project(payload: ProjectCreate) -> Project:
    return project_service.create_project(payload)


@router.get("/{project_id}", response_model=Project, summary="项目详情")
async def get_project(project_id: str) -> Project:
    project = project_service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.patch("/{project_id}", response_model=Project, summary="更新项目")
async def update_project(project_id: str, payload: ProjectUpdate) -> Project:
    project = project_service.update_project(project_id, payload)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除项目",
)
async def delete_project(project_id: str) -> None:
    if not project_service.delete_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
