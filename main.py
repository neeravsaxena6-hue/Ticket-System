import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import SessionLocal, engine
from models import Base
from routers import router
from escalation import escalate_overdue_tickets


async def escalation_loop():

    while True:
        db = SessionLocal()

        try:
            escalate_overdue_tickets(db)

        except Exception:
            db.rollback()

        finally:
            db.close()

        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):

    Base.metadata.create_all(
        bind=engine
    )

    task = asyncio.create_task(
        escalation_loop()
    )

    try:
        yield

    finally:
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Ticket Management System",
    lifespan=lifespan
)

app.include_router(router)