"""Reading ingestion, interval energy calculations, aggregation and coverage."""

from __future__ import annotations

import calendar
import math
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from config import settings
from database import from_naive_utc, local_day_bounds, to_naive_utc, utcnow
from errors import AppError
from models import ElectricityReading, Socket
from schemas import ReadingCreate
from services.common import (
    coverage_percent,
    dec,
    iso_z,
    kwh_str,
    local_date_of_utc,
    local_day_hours,
    money_str,
    month_bounds,
    month_key,
    range_hours,
)

WHOLE_HOUSE_WARNING = (
    "Socket readings may not cover the entire household. Coverage below reflects observed "
    "reading intervals, not every electrical load in the home."
)


def serialize_socket(socket: Socket) -> dict:
    return {
        "id": socket.id,
        "name": socket.name,
        "appliance": socket.appliance,
        "rated_power_w": f"{dec(socket.rated_power_w):.2f}",
        "location": socket.location,
        "is_active": socket.is_active,
        "adapter_type": socket.adapter_type,
        "is_demo": socket.is_demo,
        "created_at": socket.created_at,
        "updated_at": socket.updated_at,
    }


def serialize_reading(reading: ElectricityReading) -> dict:
    return {
        "id": reading.id,
        "socket_id": reading.socket_id,
        "socket_name": reading.socket.name if reading.socket else None,
        "reading_at": iso_z(reading.reading_at),
        "power_w": f"{dec(reading.power_w):.2f}",
        "cumulative_energy_kwh": (
            f"{dec(reading.cumulative_energy_kwh):.3f}"
            if reading.cumulative_energy_kwh is not None
            else None
        ),
        "source": reading.source,
        "is_simulated": reading.is_simulated,
        "quality_flag": reading.quality_flag,
        "out_of_order": reading.out_of_order,
        "notes": reading.notes,
        "created_at": reading.created_at,
    }


def get_socket(db: Session, socket_id: int) -> Socket:
    socket = db.get(Socket, socket_id)
    if not socket:
        raise AppError("Socket not found", status_code=404)
    return socket


def list_sockets(db: Session, include_inactive: bool = True) -> list[Socket]:
    stmt = select(Socket).order_by(Socket.name)
    if not include_inactive:
        stmt = stmt.where(Socket.is_active.is_(True))
    return list(db.scalars(stmt).all())


def create_reading(db: Session, payload: ReadingCreate) -> ElectricityReading:
    socket = get_socket(db, payload.socket_id)
    reading_at = to_naive_utc(payload.reading_at)
    duplicate = db.scalar(
        select(ElectricityReading).where(
            ElectricityReading.socket_id == socket.id,
            ElectricityReading.reading_at == reading_at,
        )
    )
    if duplicate:
        raise AppError(
            "A reading already exists for this socket and timestamp",
            status_code=409,
            details={"existing_reading_id": duplicate.id},
        )
    latest = db.scalar(
        select(ElectricityReading.reading_at)
        .where(ElectricityReading.socket_id == socket.id)
        .order_by(ElectricityReading.reading_at.desc())
        .limit(1)
    )
    out_of_order = bool(latest and reading_at < latest)
    power = dec(payload.power_w)
    quality = "ok"
    if power > dec(socket.rated_power_w):
        quality = "above_rated_power"
    reading = ElectricityReading(
        socket_id=socket.id,
        reading_at=reading_at,
        power_w=power,
        cumulative_energy_kwh=payload.cumulative_energy_kwh,
        source=payload.source,
        is_simulated=payload.source == "simulated",
        quality_flag=quality,
        out_of_order=out_of_order,
        notes=payload.notes,
    )
    db.add(reading)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError("Duplicate reading timestamp", status_code=409)
    db.refresh(reading)
    return reading


def list_readings(
    db: Session, socket_id: int | None = None, limit: int = 500
) -> list[ElectricityReading]:
    stmt = (
        select(ElectricityReading)
        .options(joinedload(ElectricityReading.socket))
        .order_by(ElectricityReading.reading_at.desc())
    )
    if socket_id:
        get_socket(db, socket_id)
        stmt = stmt.where(ElectricityReading.socket_id == socket_id)
    return list(db.scalars(stmt.limit(min(max(limit, 1), 5000))).unique().all())


def delete_reading(db: Session, reading_id: int) -> None:
    reading = db.get(ElectricityReading, reading_id)
    if not reading:
        raise AppError("Reading not found", status_code=404)
    db.delete(reading)
    db.commit()


def _validate_range(start_date: date, end_date: date, *, max_days: int = 366) -> None:
    if start_date > end_date:
        raise AppError("start_date cannot be after end_date", status_code=422)
    if (end_date - start_date).days + 1 > max_days:
        raise AppError(
            f"Requested range exceeds the {max_days}-day limit", status_code=422
        )


def _build_segments(
    db: Session, start_date: date, end_date: date, socket_id: int | None = None
) -> tuple[list[dict], list[dict]]:
    """Build interval segments, splitting at local midnight.

    Intervals longer than the configured maximum gap are excluded and reported
    as missing data rather than silently manufacturing energy.
    """
    range_start, range_end = local_day_bounds(start_date, end_date)
    stmt = (
        select(ElectricityReading)
        .options(joinedload(ElectricityReading.socket))
        .where(ElectricityReading.reading_at <= range_end)
        .order_by(ElectricityReading.socket_id, ElectricityReading.reading_at)
    )
    if socket_id:
        get_socket(db, socket_id)
        stmt = stmt.where(ElectricityReading.socket_id == socket_id)
    readings = list(db.scalars(stmt).unique().all())
    by_socket: dict[int, list[ElectricityReading]] = {}
    for reading in readings:
        by_socket.setdefault(reading.socket_id, []).append(reading)

    segments: list[dict] = []
    gaps: list[dict] = []
    max_gap_hours = settings.max_reading_gap_hours
    for current_socket_id, items in by_socket.items():
        for previous, current in zip(items, items[1:]):
            interval_start = previous.reading_at
            interval_end = current.reading_at
            duration = (interval_end - interval_start).total_seconds() / 3600
            if duration <= 0:
                continue
            if duration > max_gap_hours:
                if interval_end >= range_start and interval_start <= range_end:
                    gaps.append(
                        {
                            "socket_id": current_socket_id,
                            "socket_name": previous.socket.name if previous.socket else None,
                            "gap_start": iso_z(interval_start),
                            "gap_end": iso_z(interval_end),
                            "gap_hours": round(duration, 2),
                        }
                    )
                continue
            a = max(interval_start, range_start)
            b = min(interval_end, range_end)
            if a >= b:
                continue
            while a < b:
                local_day = local_date_of_utc(a)
                next_midnight_local = datetime.combine(
                    local_day + timedelta(days=1),
                    datetime.min.time(),
                    tzinfo=settings.timezone,
                )
                boundary = to_naive_utc(next_midnight_local)
                segment_end = min(b, boundary)
                segment_hours = (segment_end - a).total_seconds() / 3600
                if segment_hours <= 0:
                    break
                energy = dec(previous.power_w) * dec(str(segment_hours)) / Decimal("1000")
                segments.append(
                    {
                        "socket_id": current_socket_id,
                        "socket_name": previous.socket.name if previous.socket else None,
                        "appliance": previous.socket.appliance if previous.socket else None,
                        "date": local_day,
                        "start_utc": a,
                        "end_utc": segment_end,
                        "energy_kwh": energy,
                        "power_w": dec(previous.power_w),
                        "is_simulated": previous.is_simulated,
                        "quality_flag": previous.quality_flag,
                    }
                )
                a = segment_end
    return segments, gaps


def _warnings(
    segments: list[dict], gaps: list[dict], coverage: float, *, simulated: bool
) -> list[str]:
    warnings = [WHOLE_HOUSE_WARNING]
    if not segments:
        warnings.append(
            "No usable reading intervals in this period. Missing data is not replaced with estimates."
        )
    elif coverage < 95:
        warnings.append(
            f"Reading intervals cover {coverage:.2f}% of the requested period; "
            "some consumption may be unobserved."
        )
    if gaps:
        warnings.append(
            f"{len(gaps)} reading gap(s) longer than {settings.max_reading_gap_hours:g} "
            "hours were excluded from energy calculations."
        )
    if simulated:
        warnings.append("This result includes simulated readings and must be labelled as simulated.")
    return warnings


def _simulated_flag(segments: list[dict]) -> bool:
    return any(segment["is_simulated"] for segment in segments)


def _union_for_segments(segments: list[dict]) -> list[tuple[datetime, datetime]]:
    return [(segment["start_utc"], segment["end_utc"]) for segment in segments]


def aggregate_range(db: Session, start_date: date, end_date: date) -> dict:
    _validate_range(start_date, end_date)
    segments, gaps = _build_segments(db, start_date, end_date)
    total_energy = sum((segment["energy_kwh"] for segment in segments), Decimal("0"))
    hours = range_hours(start_date, end_date)
    coverage = coverage_percent(_union_for_segments(segments), hours)
    sockets = sorted({segment["socket_id"] for segment in segments})
    simulated = _simulated_flag(segments)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "energy_kwh": kwh_str(total_energy),
        "coverage_pct": coverage,
        "covered_hours": round(
            sum(
                (end - start).total_seconds() / 3600
                for start, end in _merge_for_total(_union_for_segments(segments))
            ),
            2,
        ),
        "period_hours": round(hours, 2),
        "socket_ids_reporting": sockets,
        "socket_count_reporting": len(sockets),
        "interval_segments": len(segments),
        "simulated": simulated,
        "gaps": gaps,
        "warnings": _warnings(segments, gaps, coverage, simulated=simulated),
        "methodology": (
            "Interval energy = previous reading power (W) × observed interval duration (h) ÷ 1000. "
            "Intervals longer than the configured maximum gap are excluded and reported, not filled."
        ),
    }


def _merge_for_total(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def daily_consumption(
    db: Session, start_date: date, end_date: date, socket_id: int | None = None
) -> dict:
    _validate_range(start_date, end_date)
    segments, gaps = _build_segments(db, start_date, end_date, socket_id)
    by_day: dict[date, list[dict]] = {}
    for segment in segments:
        by_day.setdefault(segment["date"], []).append(segment)

    days = []
    cursor = start_date
    while cursor <= end_date:
        day_segments = by_day.get(cursor, [])
        intervals = _union_for_segments(day_segments)
        coverage = coverage_percent(intervals, local_day_hours(cursor))
        energy = sum(
            (segment["energy_kwh"] for segment in day_segments), Decimal("0")
        )
        days.append(
            {
                "date": cursor,
                "energy_kwh": kwh_str(energy) if day_segments else None,
                "coverage_pct": coverage,
                "sockets_reporting": len({item["socket_id"] for item in day_segments}),
                "simulated": _simulated_flag(day_segments),
            }
        )
        cursor += timedelta(days=1)
    total_energy = sum((segment["energy_kwh"] for segment in segments), Decimal("0"))
    coverage = coverage_percent(
        _union_for_segments(segments), range_hours(start_date, end_date)
    )
    simulated = _simulated_flag(segments)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "timezone": settings.timezone_name,
        "days": days,
        "total_energy_kwh": kwh_str(total_energy),
        "data_coverage_pct": coverage,
        "gaps": gaps,
        "simulated": simulated,
        "warnings": _warnings(segments, gaps, coverage, simulated=simulated),
        "methodology": (
            "Daily energy is the sum of socket interval estimates. A missing day has null energy, "
            "not a fabricated zero. Coverage is the union of observed reading intervals."
        ),
    }


def monthly_consumption(
    db: Session, start_date: date, end_date: date, socket_id: int | None = None
) -> dict:
    _validate_range(start_date, end_date, max_days=366 * 5)
    segments, gaps = _build_segments(db, start_date, end_date, socket_id)
    by_month: dict[str, list[dict]] = {}
    for segment in segments:
        by_month.setdefault(segment["date"].strftime("%Y-%m"), []).append(segment)

    months = []
    cursor = date(start_date.year, start_date.month, 1)
    while cursor <= end_date:
        month_start = max(cursor, start_date)
        month_end = min(
            date(
                cursor.year,
                cursor.month,
                calendar.monthrange(cursor.year, cursor.month)[1],
            ),
            end_date,
        )
        key = cursor.strftime("%Y-%m")
        month_segments = by_month.get(key, [])
        coverage = coverage_percent(
            _union_for_segments(month_segments),
            range_hours(month_start, month_end),
        )
        energy = sum(
            (segment["energy_kwh"] for segment in month_segments), Decimal("0")
        )
        months.append(
            {
                "month": key,
                "period_start": month_start,
                "period_end": month_end,
                "energy_kwh": kwh_str(energy) if month_segments else None,
                "coverage_pct": coverage,
                "sockets_reporting": len(
                    {item["socket_id"] for item in month_segments}
                ),
                "simulated": _simulated_flag(month_segments),
            }
        )
        cursor = (
            date(cursor.year + 1, 1, 1)
            if cursor.month == 12
            else date(cursor.year, cursor.month + 1, 1)
        )
    total_energy = sum((segment["energy_kwh"] for segment in segments), Decimal("0"))
    coverage = coverage_percent(
        _union_for_segments(segments), range_hours(start_date, end_date)
    )
    simulated = _simulated_flag(segments)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "months": months,
        "total_energy_kwh": kwh_str(total_energy),
        "data_coverage_pct": coverage,
        "gaps": gaps,
        "simulated": simulated,
        "warnings": _warnings(segments, gaps, coverage, simulated=simulated),
        "methodology": "Monthly energy sums the same interval segments used for daily calculations.",
    }


def consumption_by_socket(
    db: Session, start_date: date, end_date: date
) -> dict:
    _validate_range(start_date, end_date, max_days=366 * 5)
    segments, gaps = _build_segments(db, start_date, end_date)
    sockets = list(db.scalars(select(Socket).order_by(Socket.name)).all())
    total_hours = range_hours(start_date, end_date)
    rows = []
    for socket in sockets:
        socket_segments = [
            segment for segment in segments if segment["socket_id"] == socket.id
        ]
        energy = sum(
            (segment["energy_kwh"] for segment in socket_segments), Decimal("0")
        )
        coverage = coverage_percent(
            _union_for_segments(socket_segments), total_hours
        )
        rows.append(
            {
                **serialize_socket(socket),
                "energy_kwh": kwh_str(energy) if socket_segments else None,
                "coverage_pct": coverage,
                "simulated": _simulated_flag(socket_segments),
            }
        )
    all_energy = sum((segment["energy_kwh"] for segment in segments), Decimal("0"))
    return {
        "start_date": start_date,
        "end_date": end_date,
        "sockets": rows,
        "total_energy_kwh": kwh_str(all_energy),
        "gaps": gaps,
        "warnings": [WHOLE_HOUSE_WARNING],
        "methodology": "Each socket total uses its own consecutive readings only.",
    }


def simulate_socket_readings(
    db: Session,
    socket_id: int,
    *,
    days: int = 30,
    interval_minutes: int = 60,
) -> dict:
    """Generate clearly-labelled simulated readings for demonstrations."""
    socket = get_socket(db, socket_id)
    if days < 1 or days > 180:
        raise AppError("days must be between 1 and 180", status_code=422)
    if interval_minutes < 5 or interval_minutes > 720:
        raise AppError("interval_minutes must be between 5 and 720", status_code=422)
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start = now - timedelta(days=days)
    existing = set(
        db.scalars(
            select(ElectricityReading.reading_at).where(
                ElectricityReading.socket_id == socket.id,
                ElectricityReading.reading_at >= to_naive_utc(start),
            )
        ).all()
    )
    count = 0
    current = start
    rated = float(socket.rated_power_w)
    while current <= now:
        stored_time = to_naive_utc(current)
        if stored_time not in existing:
            local_hour = current.astimezone(settings.timezone).hour
            appliance = socket.appliance.lower()
            if "air" in appliance or "ac" in appliance:
                wave = (math.sin((local_hour - 13) / 24 * 2 * math.pi) + 1) / 2
                factor = 0.25 + 0.65 * wave
            elif "fridge" in appliance or "refrigerator" in appliance:
                factor = 0.28 + 0.12 * ((local_hour // 2) % 3 == 0)
            else:
                factor = 0.08 + 0.4 * max(
                    0, math.sin((local_hour - 7) / 24 * 2 * math.pi)
                )
            power = max(0.0, min(rated, rated * factor + socket.id * 1.7))
            reading = ElectricityReading(
                socket_id=socket.id,
                reading_at=stored_time,
                power_w=Decimal(str(round(power, 2))),
                cumulative_energy_kwh=None,
                source="simulated",
                is_simulated=True,
                quality_flag="ok",
                out_of_order=False,
                notes="Simulated demonstration reading",
            )
            db.add(reading)
            count += 1
        current += timedelta(minutes=interval_minutes)
    db.commit()
    return {
        "socket_id": socket.id,
        "created": count,
        "days": days,
        "interval_minutes": interval_minutes,
        "simulated": True,
        "note": "All generated readings are simulated and visibly labelled as such.",
    }
