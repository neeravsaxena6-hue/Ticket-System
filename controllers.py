
from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pydantic_model import Signup, TicketCreate, Login, TicketReject
from models import User, Ticket
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_employee,
    require_manager,
    require_it_head,
)
from database import get_db
from escalation import escalate_overdue_tickets


def login_user(
    data: Login,
    db: Session = Depends(get_db),
):
    # Email is case-insensitive; password remains case-sensitive.
    normalized_email = data.email.strip().lower()

    user = db.query(User).filter(
        func.lower(User.email) == normalized_email
    ).first()

    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(user_id=user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "Logged in successfully!",
    }


def signup(
    data: Signup,
    db: Session = Depends(get_db),
):
    name = data.name.strip()
    email = data.email.strip().lower()

    if not name or not email or not data.password:
        raise HTTPException(
            status_code=400,
            detail="Please enter all details",
        )

    existing_user = db.query(User).filter(
        func.lower(User.email) == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="User already exists",
        )

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(data.password),
        role="employee",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Signup successful!",
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }


def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }


def create_ticket(
    data: TicketCreate,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    ticket = Ticket(
        title=data.title.strip(),
        description=data.description.strip(),
        employee_id=current_user.id,
        status="PENDING",
    )

    if not ticket.title or not ticket.description:
        raise HTTPException(
            status_code=400,
            detail="Title and description are required",
        )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return {
        "message": "Ticket created successfully!",
        "data": ticket,
    }


def get_my_tickets(
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db),
):
    tickets = db.scalars(
        select(Ticket)
        .where(Ticket.employee_id == current_user.id)
        .order_by(Ticket.created_at.desc())
    ).all()

    return {
        "message": "Your tickets retrieved successfully!",
        "data": tickets,
    }


def get_ticket_by_id(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    # Employees may view only their own tickets.
    # IT Head and Manager can view any ticket.
    if (
        current_user.role == "employee"
        and ticket.employee_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot view this ticket",
        )

    return {
        "message": "Ticket retrieved successfully!",
        "data": ticket,
    }


def get_all_tickets_for_it_head(
    current_user: User = Depends(require_it_head),
    db: Session = Depends(get_db),
):
    # Update overdue flags before returning tickets.
    escalate_overdue_tickets(db)

    tickets = db.scalars(
        select(Ticket).order_by(Ticket.created_at.desc())
    ).all()

    return {
        "message": "All tickets retrieved successfully!",
        "data": tickets,
    }


def get_pending_tickets_for_it_head(
    current_user: User = Depends(require_it_head),
    db: Session = Depends(get_db),
):
    escalate_overdue_tickets(db)

    tickets = db.scalars(
        select(Ticket)
        .where(Ticket.status == "PENDING")
        .order_by(Ticket.created_at.asc())
    ).all()

    return {
        "message": "Pending tickets retrieved successfully!",
        "data": tickets,
    }


def accept_ticket(
    ticket_id: int,
    current_user: User = Depends(require_it_head),
    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    if ticket.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Only pending tickets can be accepted",
        )

    ticket.status = "ACCEPTED"
    ticket.manager_id = current_user.id
    ticket.manager_responded_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return {
        "message": "Ticket accepted successfully!",
        "data": ticket,
    }


def reject_ticket(
    ticket_id: int,
    data: TicketReject,
    current_user: User = Depends(require_it_head),
    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    if ticket.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Only pending tickets can be rejected",
        )

    reason = data.reason.strip()

    if not reason:
        raise HTTPException(
            status_code=400,
            detail="Rejection reason is required",
        )

    ticket.status = "REJECTED"
    ticket.manager_id = current_user.id
    ticket.manager_reason = reason
    ticket.manager_responded_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return {
        "message": "Ticket rejected successfully!",
        "data": ticket,
    }


def get_escalated_tickets(
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    # Mark pending tickets older than 24 hours as escalated.
    escalate_overdue_tickets(db)

    tickets = db.scalars(
        select(Ticket)
        .where(Ticket.is_escalated.is_(True))
        .order_by(Ticket.escalated_at.asc())
    ).all()

    return {
        "message": "Escalated tickets retrieved successfully!",
        "data": tickets,
    }
