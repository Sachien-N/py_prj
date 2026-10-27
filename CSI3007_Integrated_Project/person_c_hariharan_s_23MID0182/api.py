"""FastAPI backend for the Smart Home Electricity Monitoring project."""

from __future__ import annotations

import csv
import hmac
import io
import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import Body, Depends, FastAPI, File, Header, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from config import settings
from database import get_db, init_db
from errors import AppError
from models import BillComparison, ElectricityBill, Socket
from schemas import (
    BillCreate,
    DemoSeedRequest,
    ReadingCreate,
    SocketCreate,
    SocketUpdate,
    TariffCreate,
    TariffUpdate,
)
from services import bill_comparison_service, bill_service, demo_service, integration_service
from services.bill_comparison_service import compare_bill
from services.bill_service import (
    comparison_history_rows,
    create_bill,
    delete_bill,
    get_bill,
    import_bills_csv,
    list_bills,
    serialize_bill,
)
from services.common import money_str
from services.cost_service import estimate_period_cost, monthly_cost_series
from services.expense_service import (
    build_person_a_payload,
    default_expense_range,
    monthly_expense_records,
)
from services.historical_analysis_service import analyze_six_months
from services.reading_service import (
    consumption_by_socket,
    create_reading,
    daily_consumption,
    delete_reading,
    list_readings,
    list_sockets,
    monthly_consumption,
    serialize_reading,
    simulate_socket_readings,
)
from services.socket_service import (
    create_socket,
    delete_socket,
    socket_detail,
    update_socket,
)
from services.tariff_service import (
    calculate_estimate,
    create_tariff,
    get_tariff,
    list_tariffs,
    serialize_tariff,
    update_tariff,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("person_c.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logger.info("Person C database initialised at %s", settings.database_url)
    yield


app = FastAPI(
    title="Person C — Smart Electricity API",
    description=(
        "Smart-socket reading capture, interval-based kWh estimation, configurable "
        "progressive tariffs, actual bill verification, six-month evidence analysis, "
        "and an authenticated expense integration to Person A. All costs are estimates."
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
    logger.exception("Unhandled Person C API error on %s", request.url.path)
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
        "service": "person_c_smart_electricity",
        "app": settings.app_name,
        "owner": settings.owner_name,
        "registration_no": settings.owner_registration,
        "database": "ok",
        "timezone": settings.timezone_name,
        "time_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/project-info", tags=["system"])
def project_info():
    return {
        "project": settings.app_name,
        "owner": settings.owner_name,
        "registration_no": settings.owner_registration,
        "description": (
            "Socket energy monitoring, configurable tariff estimates, bill comparison "
            "and evidence-based historical analysis."
        ),
        "api_docs": "/docs",
        "warning": (
            "All calculated costs are estimates. The project never claims that TNEB/TANGEDCO "
            "issued an incorrect bill and socket readings may not cover the entire household."
        ),
    }


# ------------------------------- sockets ----------------------------------


@app.get("/sockets", tags=["sockets"])
def sockets(include_inactive: bool = True, db: Session = Depends(get_db)):
    from services.reading_service import serialize_socket

    return [
        serialize_socket(item) for item in list_sockets(db, include_inactive)
    ]


@app.post("/sockets", tags=["sockets"], status_code=201)
def add_socket(payload: SocketCreate, db: Session = Depends(get_db)):
    from services.reading_service import serialize_socket

    return serialize_socket(create_socket(db, payload))


@app.post("/sockets/readings", tags=["readings"], status_code=201)
def add_reading(payload: ReadingCreate, db: Session = Depends(get_db)):
    reading = create_reading(db, payload)
    result = serialize_reading(reading)
    result["note"] = (
        "Out-of-order readings are stored and included in sorted interval calculations."
        if reading.out_of_order
        else "Reading stored."
    )
    return result


@app.get("/sockets/readings", tags=["readings"])
def readings(
    socket_id: int | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    return [serialize_reading(item) for item in list_readings(db, socket_id, limit)]


@app.delete("/sockets/readings/{reading_id}", tags=["readings"], status_code=204)
def remove_reading(reading_id: int, db: Session = Depends(get_db)):
    delete_reading(db, reading_id)
    return Response(status_code=204)


@app.post("/sockets/{socket_id}/simulate", tags=["readings"])
def simulate(
    socket_id: int,
    days: int = Query(default=30, ge=1, le=180),
    interval_minutes: int = Query(default=60, ge=5, le=720),
    db: Session = Depends(get_db),
):
    return simulate_socket_readings(
        db, socket_id, days=days, interval_minutes=interval_minutes
    )


@app.get("/sockets/{socket_id}/readings", tags=["readings"])
def socket_readings(
    socket_id: int,
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    return [serialize_reading(item) for item in list_readings(db, socket_id, limit)]


@app.get("/sockets/{socket_id}", tags=["sockets"])
def socket_detail_route(socket_id: int, db: Session = Depends(get_db)):
    return socket_detail(db, socket_id)


@app.put("/sockets/{socket_id}", tags=["sockets"])
def edit_socket(
    socket_id: int, payload: SocketUpdate, db: Session = Depends(get_db)
):
    from services.reading_service import serialize_socket

    return serialize_socket(update_socket(db, socket_id, payload))


@app.delete("/sockets/{socket_id}", tags=["sockets"], status_code=204)
def remove_socket(socket_id: int, db: Session = Depends(get_db)):
    delete_socket(db, socket_id)
    return Response(status_code=204)


# ------------------------------ consumption -------------------------------


@app.get("/consumption/daily", tags=["consumption"])
def daily(
    start_date: date | None = None,
    end_date: date | None = None,
    socket_id: int | None = None,
    db: Session = Depends(get_db),
):
    today = date.today()
    start_date = start_date or today.replace(day=1)
    end_date = end_date or today
    return daily_consumption(db, start_date, end_date, socket_id)


@app.get("/consumption/monthly", tags=["consumption"])
def monthly(
    start_date: date | None = None,
    end_date: date | None = None,
    socket_id: int | None = None,
    db: Session = Depends(get_db),
):
    today = date.today()
    start_date = start_date or today.replace(month=1, day=1)
    end_date = end_date or today
    return monthly_consumption(db, start_date, end_date, socket_id)


@app.get("/consumption/estimate", tags=["consumption"])
def period_cost_estimate(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    today = date.today()
    return estimate_period_cost(
        db, start_date or today.replace(day=1), end_date or today
    )


@app.get("/consumption/monthly-costs", tags=["consumption"])
def monthly_costs(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    today = date.today()
    start = start_date or today.replace(month=1, day=1)
    end = end_date or today
    return monthly_cost_series(db, start, end)


@app.get("/consumption/by-socket", tags=["consumption"])
def by_socket(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    today = date.today()
    start_date = start_date or today.replace(day=1)
    end_date = end_date or today
    return consumption_by_socket(db, start_date, end_date)


# -------------------------------- tariffs ---------------------------------


@app.get("/tariffs", tags=["tariffs"])
def tariffs(include_inactive: bool = True, db: Session = Depends(get_db)):
    return [
        serialize_tariff(item) for item in list_tariffs(db, include_inactive)
    ]


@app.post("/tariffs", tags=["tariffs"], status_code=201)
def add_tariff(payload: TariffCreate, db: Session = Depends(get_db)):
    return serialize_tariff(create_tariff(db, payload))


@app.get("/tariffs/{tariff_id}", tags=["tariffs"])
def tariff_detail(tariff_id: int, db: Session = Depends(get_db)):
    return serialize_tariff(get_tariff(db, tariff_id))


@app.put("/tariffs/{tariff_id}", tags=["tariffs"])
def edit_tariff(
    tariff_id: int, payload: TariffUpdate, db: Session = Depends(get_db)
):
    return serialize_tariff(update_tariff(db, tariff_id, payload))


# ---------------------------------- bills ---------------------------------


@app.post("/bills/import/csv", tags=["bills"])
def upload_bills_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename or "").lower().endswith(".csv"):
        raise AppError("Only .csv files are accepted", status_code=415)
    if file.content_type not in {
        "text/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
        "text/plain",
    }:
        raise AppError("Unsupported upload content type", status_code=415)
    raw = file.file.read(2 * 1024 * 1024 + 1)
    return import_bills_csv(db, raw)


@app.get("/bills/compare/{bill_id}", tags=["bills"])
def bill_comparison(
    bill_id: int,
    tolerance_percent: float | None = Query(default=None, ge=0, le=100),
    tariff_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
):
    return compare_bill(
        db, bill_id, tolerance_percent=tolerance_percent, tariff_id=tariff_id
    )


@app.get("/bills", tags=["bills"])
def bills(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    return [serialize_bill(item) for item in list_bills(db, start_date, end_date)]


@app.post("/bills", tags=["bills"], status_code=201)
def add_bill(payload: BillCreate, db: Session = Depends(get_db)):
    return serialize_bill(create_bill(db, payload))


@app.get("/bills/{bill_id}", tags=["bills"])
def bill_detail(bill_id: int, db: Session = Depends(get_db)):
    return serialize_bill(get_bill(db, bill_id))


@app.delete("/bills/{bill_id}", tags=["bills"], status_code=204)
def remove_bill(bill_id: int, db: Session = Depends(get_db)):
    delete_bill(db, bill_id)
    return Response(status_code=204)


@app.get("/analysis/six-months", tags=["analysis"])
def six_months(
    bill_id: int = Query(ge=1),
    tolerance_percent: float | None = Query(default=None, ge=0, le=100),
    db: Session = Depends(get_db),
):
    comparison = compare_bill(
        db, bill_id, tolerance_percent=tolerance_percent
    )
    if comparison.get("six_month_analysis"):
        return comparison["six_month_analysis"]
    return analyze_six_months(db, bill_id, current_comparison=comparison)


# -------------------------------- expenses --------------------------------


@app.get("/expenses/electricity", tags=["integrations"])
def electricity_expenses(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    default_start, default_end = default_expense_range()
    return monthly_expense_records(
        db,
        start_date or default_start,
        end_date or default_end,
    )


# --------------------------------- exports --------------------------------


@app.get("/exports/consumption.csv", tags=["exports"])
def export_consumption_csv(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    today = date.today()
    start_date = start_date or today.replace(day=1)
    end_date = end_date or today
    data = daily_consumption(db, start_date, end_date)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["date", "energy_kwh", "coverage_pct", "sockets_reporting", "simulated"])
    for day in data["days"]:
        writer.writerow(
            [
                day["date"].isoformat(),
                day["energy_kwh"] if day["energy_kwh"] is not None else "",
                f"{day['coverage_pct']:.2f}",
                day["sockets_reporting"],
                "true" if day["simulated"] else "false",
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="consumption_{start_date}_{end_date}.csv"'
        },
    )


@app.get("/exports/bill-comparisons.csv", tags=["exports"])
def export_comparisons_csv(db: Session = Depends(get_db)):
    rows = comparison_history_rows(db)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    headers = [
        "bill_id",
        "bill_reference",
        "billing_period_start",
        "billing_period_end",
        "estimated_units",
        "actual_units",
        "estimated_cost",
        "actual_cost",
        "cost_deviation",
        "percentage_deviation",
        "tolerance_percent",
        "exceeds_tolerance",
        "coverage_pct",
    ]
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(header, "") for header in headers])
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="bill_comparisons.csv"'},
    )


# ------------------------------ demo data ---------------------------------


@app.post("/demo/seed", tags=["demo"])
def seed_demo(payload: DemoSeedRequest = Body(default=DemoSeedRequest()), db: Session = Depends(get_db)):
    return demo_service.seed_demo(db, months=payload.months, force=payload.force)


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
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    default_start, default_end = default_expense_range()
    return build_person_a_payload(
        db, start_date or default_start, end_date or default_end
    )


@app.post(
    "/integrations/person-a/sync",
    tags=["integrations"],
    dependencies=[Depends(require_integration_key)],
)
def sync_person_a(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    return integration_service.push_to_person_a(db, start_date, end_date)
