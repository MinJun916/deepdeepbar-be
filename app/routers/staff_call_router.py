import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.staff_call_crud import delete_option, get_options, save_option
from app.database.connection import get_db
from app.dependencies.auth_dependency import require_admin
from app.schemas.staff_call_schema import (
    CreateStaffCallRequest,
    StaffCallOptionRequest,
    StaffCallOptionResponse,
    StaffCallResponse,
)
from app.services.staff_call_service import create_staff_call, get_current_calls

router = APIRouter(tags=["staff-calls"])
Database = Annotated[AsyncSession, Depends(get_db)]
Token = Annotated[str, Header(alias="X-Table-Session-Token", min_length=1)]


@router.get("/staff-call-options", response_model=list[StaffCallOptionResponse])
async def read_options(db: Database):
    return await get_options(db)


@router.get(
    "/staff-call-options/admin",
    response_model=list[StaffCallOptionResponse],
    dependencies=[Depends(require_admin)],
)
async def read_admin_options(db: Database):
    return await get_options(db, admin=True)


@router.post(
    "/staff-call-options",
    response_model=StaffCallOptionResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def add_option(data: StaffCallOptionRequest, db: Database):
    return await save_option(db, data)


@router.patch(
    "/staff-call-options/{option_id}",
    response_model=StaffCallOptionResponse,
    dependencies=[Depends(require_admin)],
)
async def edit_option(option_id: uuid.UUID, data: StaffCallOptionRequest, db: Database):
    return await save_option(db, data, option_id)


@router.delete(
    "/staff-call-options/{option_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
async def remove_option(option_id: uuid.UUID, db: Database):
    await delete_option(db, option_id)
    return Response(status_code=204)


@router.get("/staff-calls/current", response_model=list[StaffCallResponse])
async def read_current_calls(token: Token, db: Database):
    return await get_current_calls(db, token)


@router.post("/staff-calls/", response_model=StaffCallResponse)
async def add_staff_call(data: CreateStaffCallRequest, token: Token, db: Database):
    return await create_staff_call(db, token, data.option_id)
