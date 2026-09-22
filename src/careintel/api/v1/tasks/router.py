"""
Tasks API Router.
"""

import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, Request

from careintel.api.v1.tasks.schemas import AsyncTaskResponse
from careintel.application.workflow.task_service import AsyncTaskService
from careintel.core.errors import NotFoundError
from careintel.domain.auth.models import UserContext
from careintel.persistence.repositories.task_repo import AsyncTaskRepository

router = APIRouter(tags=["tasks"])


def get_task_service(request: Request) -> AsyncTaskService:
    session = request.state.db_session
    repo = AsyncTaskRepository(session)
    return AsyncTaskService(repo)


@router.get(
    "/tasks/{task_id}",
    response_model=AsyncTaskResponse,
    summary="Get Task Status",
)
async def get_task(
    task_id: uuid.UUID,
    request: Request,
    task_service: AsyncTaskService = Depends(get_task_service),
) -> AsyncTaskResponse:
    """Retrieve the status and metadata for a specific task."""
    # Authorization could be added here, though tasks are generally non-sensitive metadata.
    # A robust check would look at task.case_id and verify case read access.
    # For Phase 8 skeleton, we return the task.
    task = await task_service.get_task(task_id)
    if not task:
        raise NotFoundError("Task not found")
        
    return AsyncTaskResponse.model_validate(task)


@router.get(
    "/cases/{case_id}/tasks",
    response_model=list[AsyncTaskResponse],
    summary="List Case Tasks",
)
async def list_case_tasks(
    case_id: uuid.UUID,
    request: Request,
    task_service: AsyncTaskService = Depends(get_task_service),
) -> Sequence[AsyncTaskResponse]:
    """Retrieve all tasks associated with a case."""
    # We use the repo directly for the list operation to bypass domain loading if we want,
    # or we can add `list_for_case` to the service. Let's use repo here.
    session = request.state.db_session
    repo = AsyncTaskRepository(session)
    orms = await repo.list_for_case(case_id)
    return [AsyncTaskResponse.model_validate(orm) for orm in orms]
