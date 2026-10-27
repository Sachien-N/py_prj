"""FastAPI backend for the Smart Subscription Manager."""

from __future__ import annotations

import hmac
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from config import settings
from database import get_db, init_db
from errors import AppError
from models import Subscription
from schemas import PaymentCreate, SubscriptionCreate, SubscriptionUpdate
from services import integration_service, renewal_service
from services.payment_service import (
    create_payment,
    delete_payment,
    list_payments,
    serialize_payment,
)
from services.subscription_service import (
    advance_renewal,
    create_subscription,
    delete_subscription,
    export_csv,
    get_subscription,
    list_subscriptions,
    serialize_subscription,
    subscription_summary,
    update_subscription,
    upcoming_renewals,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("person_b.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logger.info("Person B database initialised at %s", settings.database_url)
    yield


app = FastAPI(
    title="Person B — Smart Subscription API",
    description=(
        "Recurring subscription tracking, billing-cycle projections, actual payment history, "
        "renewal reminders, CSV export, and an authenticated push integration to Person A. "
        "Monetary values are decimal strings."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):  # noqa: ANN001
    content = {"detail": exc.message}
    if exc.details:
        content["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def unhandled_error_handler(request, exc: Exception):  # noqa: ANN001
    logger.exception("Unhandled Person B API error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. No secret information was exposed."},
    )


def require_integration_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or not hmac.compare_digest(
        x_api_key, settings.person_a_sync_api_key
    ):
        raise AppError("Invalid or missing integration API key", status_code=401)


@app.get("/health", tags=["system"])
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "service": "person_b_subscription_manager",
        "app": settings.app_name,
        "owner": settings.owner_name,
        "registration_no": settings.owner_registration,
        "database": "ok",
        "time_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/project-info", tags=["system"])
def project_info():
    return {
        "project": settings.app_name,
        "owner": settings.owner_name,
        "registration_no": settings.owner_registration,
        "description": "Subscription lifecycle, billing projections, renewals and payments.",
        "api_docs": "/docs",
        "integration": "Authenticated push to Person A (subscription expenses).",
    }


@app.get("/meta/categories", tags=["subscriptions"])
def categories():
    return [
        "Entertainment",
        "Software",
        "Education",
        "Music",
        "Cloud storage",
        "Fitness",
        "Utilities",
        "News",
        "Gaming",
        "Other",
    ]


# ---------------------------- subscriptions -------------------------------


@app.get("/subscriptions/summary", tags=["subscriptions"])
def summary(db: Session = Depends(get_db)):
    return subscription_summary(db)


@app.get("/subscriptions/upcoming", tags=["subscriptions"])
def upcoming(days: int = Query(default=30, ge=0, le=365), db: Session = Depends(get_db)):
    return upcoming_renewals(db, days)


@app.get("/subscriptions/export.csv", tags=["subscriptions"])
def download_csv(db: Session = Depends(get_db)):
    return Response(
        content=export_csv(db),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="subscriptions.csv"'},
    )


@app.get("/subscriptions/payments", tags=["payments"])
def payments(
    subscription_id: int | None = Query(default=None, ge=1),
    billing_period: str | None = None,
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    return [
        serialize_payment(item)
        for item in list_payments(
            db,
            subscription_id=subscription_id,
            billing_period=billing_period,
            limit=limit,
        )
    ]


@app.post("/subscriptions/payments", tags=["payments"])
def record_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    payment, deduplicated = create_payment(db, payload)
    return {
        **serialize_payment(payment),
        "deduplicated": deduplicated,
        "created": not deduplicated,
        "note": (
            "No payment provider was contacted. This is a manually recorded actual payment."
        ),
    }


@app.delete("/subscriptions/payments/{payment_id}", tags=["payments"], status_code=204)
def remove_payment(payment_id: int, db: Session = Depends(get_db)):
    delete_payment(db, payment_id)
    return Response(status_code=204)


@app.post("/subscriptions/reminders/refresh", tags=["renewals"])
def refresh_reminders(db: Session = Depends(get_db)):
    return renewal_service.refresh_reminders(db)


@app.get("/subscriptions/reminders", tags=["renewals"])
def reminders(db: Session = Depends(get_db)):
    return renewal_service.pending_reminders(db)


@app.post("/subscriptions/reminders/{reminder_id}/dismiss", tags=["renewals"])
def dismiss(reminder_id: int, db: Session = Depends(get_db)):
    return renewal_service.serialize_reminder(
        renewal_service.dismiss_reminder(db, reminder_id)
    )


@app.get("/subscriptions", tags=["subscriptions"])
def subscriptions(
    status: str | None = Query(
        default=None, pattern="^(active|paused|cancelled|expired)$"
    ),
    category: str | None = None,
    search: str | None = None,
    sort_by: str = "next_renewal_date",
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    return [
        serialize_subscription(item)
        for item in list_subscriptions(
            db,
            status=status,
            category=category,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    ]


@app.post("/subscriptions", tags=["subscriptions"], status_code=201)
def add_subscription(payload: SubscriptionCreate, db: Session = Depends(get_db)):
    return serialize_subscription(create_subscription(db, payload))


@app.get("/subscriptions/{subscription_id}", tags=["subscriptions"])
def subscription_detail(subscription_id: int, db: Session = Depends(get_db)):
    return serialize_subscription(get_subscription(db, subscription_id))


@app.put("/subscriptions/{subscription_id}", tags=["subscriptions"])
def edit_subscription(
    subscription_id: int, payload: SubscriptionUpdate, db: Session = Depends(get_db)
):
    return serialize_subscription(update_subscription(db, subscription_id, payload))


@app.delete("/subscriptions/{subscription_id}", tags=["subscriptions"], status_code=204)
def remove_subscription(subscription_id: int, db: Session = Depends(get_db)):
    delete_subscription(db, subscription_id)
    return Response(status_code=204)


@app.post("/subscriptions/{subscription_id}/advance-renewal", tags=["renewals"])
def advance(subscription_id: int, db: Session = Depends(get_db)):
    return serialize_subscription(advance_renewal(db, subscription_id))


# ----------------------------- integration --------------------------------


@app.get("/integrations/person-a/status", tags=["integrations"])
def integration_status(check_remote: bool = False, db: Session = Depends(get_db)):
    return integration_service.integration_status(db, check_remote=check_remote)


@app.get(
    "/integrations/person-a/payload",
    tags=["integrations"],
    dependencies=[Depends(require_integration_key)],
)
def integration_payload(
    period: str | None = None, db: Session = Depends(get_db)
):
    """The documented JSON payload Person A uses when it pulls from Person B."""
    return integration_service.build_sync_payload(db, period)


@app.post(
    "/integrations/person-a/sync",
    tags=["integrations"],
    dependencies=[Depends(require_integration_key)],
)
def sync_person_a(
    period: str | None = None, db: Session = Depends(get_db)
):
    return integration_service.push_to_person_a(db, period)
