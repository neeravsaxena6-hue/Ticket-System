from fastapi import APIRouter
router =APIRouter() 

from fastapi import APIRouter
from controllers import (
    login_user,
    create_ticket,
    get_my_tickets,
    get_ticket_by_id,
    get_manager_tickets,
    accept_ticket,
    reject_ticket,
    get_escalated_tickets,
)

router = APIRouter()


@router.post("/auth/login")
async def login():
    return await login_user()


@router.post("/tickets")
async def create():
    return await create_ticket()


@router.get("/tickets/my")
async def get_my():
    return await get_my_tickets()


@router.get("/tickets/{ticket_id}")
async def get_by_id(ticket_id: int):
    return await get_ticket_by_id()


@router.get("/manager/tickets")
async def get_tickets():
    return await get_manager_tickets()


@router.patch("/manager/tickets/{ticket_id}/accept")
async def accept(ticket_id: int):
    return await accept_ticket()


@router.patch("/manager/tickets/{ticket_id}/reject")
async def reject(ticket_id: int):
    return await reject_ticket()


@router.get("/it-head/tickets/escalated")
async def get_escalated():
    return await get_escalated_tickets()