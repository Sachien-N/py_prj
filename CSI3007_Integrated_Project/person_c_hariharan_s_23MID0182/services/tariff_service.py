"""Configurable tariff engine with effective dates, progressive slabs and components.

The engine has no UI dependency and every result identifies the tariff configuration
used. A configured tariff is never assumed to be an official TNEB tariff.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from errors import AppError
from models import TariffComponent, TariffConfig, TariffSlab
from schemas import TariffCreate, TariffUpdate
from services.common import dec, money, money_str

DEMO_TARIFF_NAME = "Illustrative domestic tariff (DEMO — not official TNEB)"


def seed_demo_tariff(db: Session) -> None:
    existing = db.scalar(
        select(TariffConfig).where(TariffConfig.name == DEMO_TARIFF_NAME)
    )
    if existing:
        return
    tariff = TariffConfig(
        name=DEMO_TARIFF_NAME,
        category="domestic",
        currency="INR",
        effective_from=date(2025, 1, 1),
        effective_to=None,
        source=(
            "DEMONSTRATION CONFIGURATION created for this academic project. "
            "It is not an official TNEB/TANGEDCO tariff order. Verify the current tariff, "
            "subsidy and charge components with the utility before relying on any estimate."
        ),
        source_url="",
        is_verified=False,
        is_active=True,
        notes=(
            "Illustrative progressive slabs and components only. Replace or add a verified "
            "configuration before real bill verification."
        ),
    )
    tariff.slabs = [
        TariffSlab(from_units=Decimal("0"), to_units=Decimal("100"), rate_per_unit=Decimal("4.50")),
        TariffSlab(from_units=Decimal("100"), to_units=Decimal("200"), rate_per_unit=Decimal("6.00")),
        TariffSlab(from_units=Decimal("200"), to_units=Decimal("500"), rate_per_unit=Decimal("8.00")),
        TariffSlab(from_units=Decimal("500"), to_units=None, rate_per_unit=Decimal("9.00")),
    ]
    tariff.components = [
        TariffComponent(
            name="Illustrative fixed monthly charge",
            charge_type="fixed_monthly",
            amount=Decimal("50"),
            sort_order=1,
        ),
        TariffComponent(
            name="Illustrative electricity duty",
            charge_type="percent_of_energy",
            amount=Decimal("5"),
            sort_order=2,
        ),
    ]
    db.add(tariff)
    db.commit()


def serialize_tariff(tariff: TariffConfig) -> dict:
    return {
        "id": tariff.id,
        "name": tariff.name,
        "category": tariff.category,
        "currency": tariff.currency,
        "effective_from": tariff.effective_from,
        "effective_to": tariff.effective_to,
        "source": tariff.source,
        "source_url": tariff.source_url,
        "is_verified": tariff.is_verified,
        "is_active": tariff.is_active,
        "notes": tariff.notes,
        "slabs": [
            {
                "from_units": f"{dec(slab.from_units):.2f}",
                "to_units": f"{dec(slab.to_units):.2f}" if slab.to_units is not None else None,
                "rate_per_unit": f"{dec(slab.rate_per_unit):.4f}",
            }
            for slab in sorted(tariff.slabs, key=lambda item: item.from_units)
        ],
        "components": [
            {
                "name": component.name,
                "charge_type": component.charge_type,
                "amount": f"{dec(component.amount):.4f}",
                "sort_order": component.sort_order,
            }
            for component in sorted(tariff.components, key=lambda item: item.sort_order)
        ],
        "created_at": tariff.created_at,
    }


def list_tariffs(db: Session, include_inactive: bool = True) -> list[TariffConfig]:
    stmt = (
        select(TariffConfig)
        .options(selectinload(TariffConfig.slabs), selectinload(TariffConfig.components))
        .order_by(TariffConfig.effective_from.desc(), TariffConfig.id.desc())
    )
    if not include_inactive:
        stmt = stmt.where(TariffConfig.is_active.is_(True))
    return list(db.scalars(stmt).unique().all())


def get_tariff(db: Session, tariff_id: int) -> TariffConfig:
    tariff = db.scalar(
        select(TariffConfig)
        .options(selectinload(TariffConfig.slabs), selectinload(TariffConfig.components))
        .where(TariffConfig.id == tariff_id)
    )
    if not tariff:
        raise AppError("Tariff configuration not found", status_code=404)
    return tariff


def create_tariff(db: Session, payload: TariffCreate) -> TariffConfig:
    if db.scalar(select(TariffConfig).where(TariffConfig.name == payload.name)):
        raise AppError("A tariff with that name already exists", status_code=409)
    tariff = TariffConfig(
        name=payload.name,
        category=payload.category.lower(),
        currency=payload.currency,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        source=payload.source,
        source_url=payload.source_url,
        is_verified=payload.is_verified,
        is_active=payload.is_active,
        notes=payload.notes,
    )
    tariff.slabs = [
        TariffSlab(
            from_units=dec(slab.from_units),
            to_units=dec(slab.to_units) if slab.to_units is not None else None,
            rate_per_unit=dec(slab.rate_per_unit),
        )
        for slab in payload.slabs
    ]
    tariff.components = [
        TariffComponent(
            name=component.name,
            charge_type=component.charge_type,
            amount=dec(component.amount),
            sort_order=component.sort_order,
        )
        for component in payload.components
    ]
    db.add(tariff)
    db.commit()
    db.refresh(tariff)
    return get_tariff(db, tariff.id)


def update_tariff(db: Session, tariff_id: int, payload: TariffUpdate) -> TariffConfig:
    tariff = get_tariff(db, tariff_id)
    data = payload.model_dump(exclude_unset=True)
    for key in ("is_active", "is_verified", "source", "source_url", "notes"):
        if key in data and data[key] is not None:
            setattr(tariff, key, data[key])
    if "effective_to" in data:
        if data["effective_to"] is not None and data["effective_to"] < tariff.effective_from:
            raise AppError("effective_to cannot be before effective_from", 422)
        tariff.effective_to = data["effective_to"]
    db.commit()
    return get_tariff(db, tariff.id)


def select_tariff(
    db: Session, on_date: date, category: str = "domestic"
) -> TariffConfig:
    stmt = (
        select(TariffConfig)
        .options(selectinload(TariffConfig.slabs), selectinload(TariffConfig.components))
        .where(
            TariffConfig.is_active.is_(True),
            TariffConfig.category == category.lower(),
            TariffConfig.effective_from <= on_date,
        )
        .order_by(TariffConfig.effective_from.desc(), TariffConfig.id.desc())
    )
    candidates = list(db.scalars(stmt).unique().all())
    for tariff in candidates:
        if tariff.effective_to is None or tariff.effective_to >= on_date:
            return tariff
    raise AppError(
        "No active tariff configuration covers that date and category. "
        "Add or activate a tariff configuration before estimating charges.",
        status_code=422,
        details={"date": on_date.isoformat(), "category": category},
    )


def calculate_estimate(
    db: Session,
    *,
    units: Decimal,
    on_date: date,
    category: str = "domestic",
    tariff_id: int | None = None,
) -> dict:
    units = dec(units)
    if units < 0:
        raise AppError("Units cannot be negative", status_code=422)
    tariff = get_tariff(db, tariff_id) if tariff_id else select_tariff(db, on_date, category)
    slabs = sorted(tariff.slabs, key=lambda item: item.from_units)
    if not slabs or dec(slabs[0].from_units) != 0:
        raise AppError("Tariff configuration must start its first slab at 0", 422)

    energy_charge = Decimal("0")
    breakdown = []
    for index, slab in enumerate(slabs):
        lower = dec(slab.from_units)
        upper = dec(slab.to_units) if slab.to_units is not None else units
        if upper < lower:
            continue
        slab_units = min(units, upper) - lower
        if slab_units < 0:
            slab_units = Decimal("0")
        charge = money(slab_units * dec(slab.rate_per_unit))
        if slab_units > 0:
            energy_charge += charge
        breakdown.append(
            {
                "from_units": f"{lower:.2f}",
                "to_units": f"{upper:.2f}" if slab.to_units is not None else None,
                "rate_per_unit": f"{dec(slab.rate_per_unit):.4f}",
                "units_in_slab": f"{slab_units:.2f}",
                "charge": money_str(charge),
            }
        )
        if slab.to_units is None:
            break
    final_upper = dec(slabs[-1].to_units) if slabs[-1].to_units is not None else None
    if final_upper is not None and units > final_upper:
        raise AppError(
            f"The configured tariff only covers up to {final_upper} units; "
            "the charge cannot be calculated reliably.",
            status_code=422,
        )

    component_rows = []
    component_total = Decimal("0")
    for component in sorted(tariff.components, key=lambda item: item.sort_order):
        amount = dec(component.amount)
        if component.charge_type == "fixed_monthly":
            charge = money(amount)
        elif component.charge_type == "per_unit":
            charge = money(amount * units)
        elif component.charge_type == "percent_of_energy":
            charge = money(energy_charge * amount / Decimal("100"))
        else:
            raise AppError("Unsupported tariff component type", status_code=422)
        component_total += charge
        component_rows.append(
            {
                "name": component.name,
                "charge_type": component.charge_type,
                "configured_amount": f"{amount:.4f}",
                "charge": money_str(charge),
            }
        )

    warnings = [
        "This is an estimate calculated from the configured tariff; it is not an official TNEB/TANGEDCO bill.",
        "Fixed monthly components are applied once per estimate, regardless of the number of days in the period.",
        "The estimate covers only monitored socket readings and may omit other household loads.",
    ]
    if not tariff.is_verified:
        warnings.insert(
            1,
            "The selected tariff is not marked as verified against an official tariff order. "
            "Verify rates, slabs, fixed charges, duties and effective dates.",
        )
    return {
        "tariff": {
            "id": tariff.id,
            "name": tariff.name,
            "category": tariff.category,
            "effective_from": tariff.effective_from,
            "effective_to": tariff.effective_to,
            "source": tariff.source,
            "source_url": tariff.source_url,
            "is_verified": tariff.is_verified,
            "currency": tariff.currency,
        },
        "units": f"{units:.2f}",
        "slab_breakdown": breakdown,
        "energy_charge": money_str(energy_charge),
        "components": component_rows,
        "component_total": money_str(component_total),
        "total_cost": money_str(energy_charge + component_total),
        "currency": tariff.currency,
        "is_estimate": True,
        "is_verified_tariff": tariff.is_verified,
        "assumptions": [
            "Progressive slab boundaries use cumulative units; a slab's from_units is its lower cumulative bound.",
            "Billing category assumed to be domestic unless configured otherwise.",
            "Only charge components stored in the tariff configuration are included.",
        ],
        "warnings": warnings,
    }
