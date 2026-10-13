from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from pydantic_model import (
    Signup,
    TicketCreate,
    Login,
    TicketReject
)

from models import User, Ticket

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_employee,
    require_manager,
    require_it_head
)

from database import get_db
from escalation import escalate_overdue_tickets


def login_user(
    data: Login,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user or not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
        user_id=user.id
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "Logged in successfully!"
    }


def signup(
    data: Signup,
    db: Session = Depends(get_db)
):
    if not data.name.strip() or not data.email.strip() or not data.password:
        raise HTTPException(
            status_code=400,
            detail="Please enter all details"
        )

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if user:
        raise HTTPException(
            status_code=409,
            detail="User already exists"
        )

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="employee"
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
            "role": user.role
        }
    }


def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }


def create_ticket(
    data: TicketCreate,
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db)
):
    ticket = Ticket(
        title=data.title,
        description=data.description,
        employee_id=current_user.id,
        status="PENDING"
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return {
        "message": "Ticket created successfully!",
        "data": ticket
    }


def get_my_tickets(
    current_user: User = Depends(require_employee),
    db: Session = Depends(get_db)
):
    result = db.scalars(
        select(Ticket).where(
            Ticket.employee_id == current_user.id
        )
    ).all()

    return {
        "message": "Tickets retrieved successfully!",
        "data": result
    }


def get_ticket_by_id(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if (
        current_user.role == "employee"
        and ticket.employee_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot view this ticket"
        )

    return {
        "message": "Ticket found",
        "data": ticket
    }


def get_manager_tickets(
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    result = db.scalars(
        select(Ticket).where(
            Ticket.status == "PENDING"
        )
    ).all()

    return {
        "message": "Pending tickets retrieved successfully!",
        "data": result
    }


def accept_ticket(
    ticket_id: int,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if ticket.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Only pending tickets can be accepted"
        )

    ticket.status = "ACCEPTED"
    ticket.manager_id = current_user.id
    ticket.manager_responded_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return {
        "message": "Ticket accepted successfully!",
        "data": ticket
    }


def reject_ticket(
    ticket_id: int,
    data: TicketReject,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if ticket.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Only pending tickets can be rejected"
        )

    if not data.reason.strip():
        raise HTTPException(
            status_code=400,
            detail="Rejection reason is required"
        )

    ticket.status = "REJECTED"
    ticket.manager_id = current_user.id
    ticket.manager_reason = data.reason.strip()
    ticket.manager_responded_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return {
        "message": "Ticket rejected successfully!",
        "data": ticket
    }


def get_escalated_tickets(
    current_user: User = Depends(require_it_head),
    db: Session = Depends(get_db)
):
    # Check for overdue tickets before returning the results.
    escalate_overdue_tickets(db)

    result = db.scalars(
        select(Ticket).where(
            Ticket.is_escalated.is_(True)
        )
    ).all()

    return {
        "message": "Escalated tickets retrieved successfully!",
        "data": result
    }