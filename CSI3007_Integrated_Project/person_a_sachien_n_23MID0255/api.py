"""FastAPI backend for the Smart Expense Categorization and Budget Manager."""

from __future__ import annotations

import hmac
import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone

from fastapi import Body, Depends, FastAPI, File, Header, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import settings
from database import get_db, init_db
from errors import AppError
from models import Budget, Category, Expense
from schemas import (
    BudgetCreate,
    BudgetUpdate,
    CategoryCreate,
    CategoryUpdate,
    ElectricitySyncRequest,
    ExpenseCreate,
    ExpenseUpdate,
    SubscriptionSyncRequest,
)
from services import integration_service
from services.budget_service import (
    budget_overview,
    create_budget,
    delete_budget,
    list_budgets,
    serialize_budget,
    update_budget,
)
from services.category_service import (
    create_category,
    delete_category,
    list_categories,
    serialize_category,
    update_category,
)
from services.csv_service import export_csv, import_csv
from services.expense_service import (
    create_expense,
    delete_expense,
    expense_summary,
    get_expense,
    list_expenses,
    serialize_expense,
    update_expense,
)
from services.report_service import monthly_report

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("person_a.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logger.info("Person A database initialised at %s", settings.database_url)
    yield


app = FastAPI(
    title="Person A — Smart Expense API",
    description=(
        "Expense tracking, automatic categorization, budgets, CSV, and authenticated "
        "subscription/electricity integrations. Monetary values are decimal strings."
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
    logger.exception("Unhandled Person A API error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. No secret information was exposed."},
    )


def require_person_b_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or not hmac.compare_digest(
        x_api_key, settings.person_b_sync_api_key
    ):
        raise AppError("Invalid or missing integration API key", status_code=401)


def require_person_c_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or not hmac.compare_digest(
        x_api_key, settings.person_c_sync_api_key
    ):
        raise AppError("Invalid or missing integration API key", status_code=401)


@app.get("/health", tags=["system"])
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "service": "person_a_expense_manager",
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
        "description": (
            "Personal finance management with rule-based categorization, budgets, "
            "refunds, CSV import/export, and REST integrations."
        ),
        "api_docs": "/docs",
        "integrations": ["person_b_subscription_manager", "person_c_smart_electricity"],
    }


# ----------------------------- categories ---------------------------------


@app.get("/categories", tags=["categories"])
def categories(include_inactive: bool = False, db: Session = Depends(get_db)):
    return [serialize_category(item) for item in list_categories(db, include_inactive)]


@app.post("/categories", tags=["categories"], status_code=201)
def add_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    return serialize_category(create_category(db, payload))


@app.put("/categories/{category_id}", tags=["categories"])
def edit_category(
    category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)
):
    return serialize_category(update_category(db, category_id, payload))


@app.delete("/categories/{category_id}", tags=["categories"], status_code=204)
def remove_category(category_id: int, db: Session = Depends(get_db)):
    delete_category(db, category_id)
    return Response(status_code=204)


# ------------------------------ expenses ----------------------------------


@app.get("/expenses/summary", tags=["expenses"])
def summary(
    start_date: date | None = None,
    end_date: date | None = None,
    currency: str = Query(default="INR", min_length=3, max_length=3),
    db: Session = Depends(get_db),
):
    return expense_summary(
        db, start_date=start_date, end_date=end_date, currency=currency.upper()
    )


@app.get("/expenses/export.csv", tags=["expenses"])
def download_expenses_csv(
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    search: str | None = None,
    transaction_type: str | None = None,
    source_app: str | None = None,
    db: Session = Depends(get_db),
):
    content = export_csv(
        db,
        start_date=start_date,
        end_date=end_date,
        category=category,
        search=search,
        transaction_type=transaction_type,
        source_app=source_app,
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="expenses.csv"'},
    )


@app.post("/expenses/import/csv", tags=["expenses"])
def upload_expenses_csv(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise AppError("Only .csv files are accepted", status_code=415)
    if file.content_type not in {
        "text/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
        "text/plain",
    }:
        raise AppError("Unsupported upload content type", status_code=415)
    raw = file.file.read(2 * 1024 * 1024 + 1)
    return import_csv(db, raw)


@app.get("/expenses", tags=["expenses"])
def expenses(
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    search: str | None = None,
    transaction_type: str | None = Query(default=None, pattern="^(expense|refund)$"),
    source_app: str | None = None,
    limit: int = Query(default=500, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items = list_expenses(
        db,
        start_date=start_date,
        end_date=end_date,
        category=category,
        search=search,
        transaction_type=transaction_type,
        source_app=source_app,
        limit=limit,
        offset=offset,
    )
    return [serialize_expense(item) for item in items]


@app.post("/expenses", tags=["expenses"], status_code=201)
def add_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    return serialize_expense(create_expense(db, payload))


@app.get("/expenses/{expense_id}", tags=["expenses"])
def expense_detail(expense_id: int, db: Session = Depends(get_db)):
    return serialize_expense(get_expense(db, expense_id))


@app.put("/expenses/{expense_id}", tags=["expenses"])
def edit_expense(
    expense_id: int, payload: ExpenseUpdate, db: Session = Depends(get_db)
):
    return serialize_expense(update_expense(db, expense_id, payload))


@app.delete("/expenses/{expense_id}", tags=["expenses"], status_code=204)
def remove_expense(expense_id: int, db: Session = Depends(get_db)):
    delete_expense(db, expense_id)
    return Response(status_code=204)


# ------------------------------- budgets ----------------------------------


@app.get("/budgets", tags=["budgets"])
def budgets(month: str | None = None, db: Session = Depends(get_db)):
    if not month:
        month = date.today().strftime("%Y-%m")
    return budget_overview(db, month)


@app.post("/budgets", tags=["budgets"], status_code=201)
def add_budget(payload: BudgetCreate, db: Session = Depends(get_db)):
    return serialize_budget(db, create_budget(db, payload))


@app.put("/budgets/{budget_id}", tags=["budgets"])
def edit_budget(
    budget_id: int, payload: BudgetUpdate, db: Session = Depends(get_db)
):
    return serialize_budget(db, update_budget(db, budget_id, payload))


@app.delete("/budgets/{budget_id}", tags=["budgets"], status_code=204)
def remove_budget(budget_id: int, db: Session = Depends(get_db)):
    delete_budget(db, budget_id)
    return Response(status_code=204)


# ------------------------------- reports ----------------------------------


@app.get("/reports/monthly", tags=["reports"])
def report_monthly(month: str, months: int = Query(default=6, ge=1, le=24), db: Session = Depends(get_db)):
    return monthly_report(db, month, months)


# ----------------------------- integrations -------------------------------


@app.get("/integrations/status", tags=["integrations"])
def integrations_status(
    check_remote: bool = False, db: Session = Depends(get_db)
):
    return integration_service.integration_status(db, check_remote=check_remote)


@app.post(
    "/integrations/subscriptions/sync",
    tags=["integrations"],
    dependencies=[Depends(require_person_b_key)],
)
def sync_subscriptions(
    payload: SubscriptionSyncRequest | None = Body(default=None),
    db: Session = Depends(get_db),
):
    """Accept a Person B push. With an empty body, pull Person B's payload instead."""
    return integration_service.sync_subscriptions(db, payload)


@app.post(
    "/integrations/electricity/sync",
    tags=["integrations"],
    dependencies=[Depends(require_person_c_key)],
)
def sync_electricity(
    payload: ElectricitySyncRequest | None = Body(default=None),
    db: Session = Depends(get_db),
):
    """Accept a Person C push. With an empty body, pull Person C's payload instead."""
    return integration_service.sync_electricity(db, payload)
