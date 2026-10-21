
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from controllers import (
    login_user,
    signup,
    get_me,
    create_ticket,
    get_my_tickets,
    get_ticket_by_id,
    get_all_tickets_for_it_head,
    get_pending_tickets_for_it_head,
    accept_ticket,
    reject_ticket,
    get_escalated_tickets,
)
from auth import (
    get_current_user,
    require_employee,
    require_manager,
    require_it_head,
)
from database import get_db
from models import User
from pydantic_model import Signup, Login, TicketCreate, TicketReject

router = APIRouter()


# ---------------- AUTH ----------------

@router.post("/auth/signup")
def signup_route(
    data: Signup,
    db: Session = Depends(get_db),
):
    return signup(data, db)


@router.post("/auth/login")
def login_route(
    data: Login,
    db: Session = Depends(get_db),
):
    return login_user(data, db)


@router.get("/auth/me")
def get_current_user_details(
    current_user: User = Depends(get_current_user),
):
    return get_me(current_user)


# ---------------- EMPLOYEE ----------------

@router.post("/tickets")
def create_ticket_route(
    data: TicketCreate,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    return create_ticket(data, current_user, db)


@router.get("/tickets/my")
def get_my_tickets_route(
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    return get_my_tickets(current_user, db)


@router.get("/tickets/{ticket_id}")
def get_ticket_route(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_ticket_by_id(ticket_id, current_user, db)


# ---------------- IT HEAD ----------------

@router.get("/it-head/tickets")
def get_all_tickets_route(
    current_user: User = Depends(require_it_head),
    db: Session = Depends(get_db),
):
    return get_all_tickets_for_it_head(current_user, db)


@router.get("/it-head/tickets/pending")
def get_pending_tickets_route(
    current_user: User = Depends(require_it_head),
    db: Session = Depends(get_db),
):
    return get_pending_tickets_for_it_head(current_user, db)


@router.patch("/it-head/tickets/{ticket_id}/accept")
def accept_ticket_route(
    ticket_id: int,
    current_user: User = Depends(require_it_head),
    db: Session = Depends(get_db),
):
    return accept_ticket(ticket_id, current_user, db)


@router.patch("/it-head/tickets/{ticket_id}/reject")
def reject_ticket_route(
    ticket_id: int,
    data: TicketReject,
    current_user: User = Depends(require_it_head),
    db: Session = Depends(get_db),
):
    return reject_ticket(ticket_id, data, current_user, db)


# ---------------- MANAGER ----------------

@router.get("/manager/tickets/escalated")
def get_escalated_tickets_route(
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    return get_escalated_tickets(current_user, db)
