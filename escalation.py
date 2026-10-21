from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Ticket


SLA_HOURS = 24


def escalate_overdue_tickets(
    db: Session
) -> int:

    now = datetime.utcnow()

    deadline = now - timedelta(
        hours=SLA_HOURS
    )

    tickets = db.scalars(
        select(Ticket).where(
            Ticket.status == "PENDING",
            Ticket.is_escalated.is_(False),
            Ticket.created_at <= deadline
        )
    ).all()

    for ticket in tickets:
        ticket.is_escalated = True
        ticket.escalated_at = now

    if tickets:
        db.commit()

    return len(tickets)