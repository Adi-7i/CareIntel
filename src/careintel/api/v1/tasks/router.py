"""
Tasks API Router.
"""

import uuid
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends

from careintel.api.deps import CurrentUserDep, DbSessionDep, get_case_service
from careintel.api.v1.tasks.schemas import AsyncTaskResponse
from careintel.application.case.case_service import CaseService
from careintel.application.workflow.task_service import AsyncTaskService
from careintel.core.errors import NotFoundError
from careintel.persistence.repositories.task_repo import AsyncTaskRepository

router = APIRouter(tags=["tasks"])


def get_task_service(session: DbSessionDep) -> AsyncTaskService:
    repo = AsyncTaskRepository(session)
    return AsyncTaskService(repo)


@router.get(
    "/tasks/{task_id}",
    response_model=AsyncTaskResponse,
    summary="Get Task Status",
)
async def get_task(
    task_id: uuid.UUID,
    actor: CurrentUserDep,
    case_service: Annotated[CaseService, Depends(get_case_service)],
    task_service: Annotated[AsyncTaskService, Depends(get_task_service)],
) -> AsyncTaskResponse:
    """Retrieve the status and metadata for a specific task."""
    task = await task_service.get_task(task_id)
    if not task:
        raise NotFoundError("Task not found")

    await case_service.get_case(task.case_id, actor)

    return AsyncTaskResponse.model_validate(task)


@router.get(
    "/cases/{case_id}/tasks",
    response_model=list[AsyncTaskResponse],
    summary="List Case Tasks",
)
async def list_case_tasks(
    case_id: uuid.UUID,
    actor: CurrentUserDep,
    case_service: Annotated[CaseService, Depends(get_case_service)],
    task_service: Annotated[AsyncTaskService, Depends(get_task_service)],
) -> Sequence[AsyncTaskResponse]:
    """Retrieve all tasks associated with a case."""
    await case_service.get_case(case_id, actor)
    tasks = await task_service.list_for_case(case_id)
    return [AsyncTaskResponse.model_validate(task) for task in tasks]
