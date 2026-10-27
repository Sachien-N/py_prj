"""CRUD for smart sockets and their monitored appliances."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from errors import AppError
from models import Socket
from schemas import SocketCreate, SocketUpdate
from services.common import dec
from services.reading_service import serialize_socket


def _duplicate_name(db: Session, name: str, exclude_id: int | None = None) -> bool:
    stmt = select(Socket.id).where(func.lower(Socket.name) == name.lower())
    if exclude_id:
        stmt = stmt.where(Socket.id != exclude_id)
    return db.scalar(stmt) is not None


def create_socket(db: Session, payload: SocketCreate) -> Socket:
    if _duplicate_name(db, payload.name):
        raise AppError("A socket with that name already exists", status_code=409)
    socket = Socket(
        name=payload.name,
        appliance=payload.appliance,
        rated_power_w=dec(payload.rated_power_w),
        location=payload.location,
        is_active=payload.is_active,
        adapter_type=payload.adapter_type,
        is_demo=False,
    )
    db.add(socket)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError("A socket with that name already exists", status_code=409)
    db.refresh(socket)
    return socket


def update_socket(db: Session, socket_id: int, payload: SocketUpdate) -> Socket:
    socket = db.get(Socket, socket_id)
    if not socket:
        raise AppError("Socket not found", status_code=404)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        if _duplicate_name(db, data["name"], exclude_id=socket.id):
            raise AppError("A socket with that name already exists", status_code=409)
    for field in ("name", "appliance", "location", "is_active", "adapter_type"):
        if field in data and data[field] is not None:
            setattr(socket, field, data[field])
    if "rated_power_w" in data and data["rated_power_w"] is not None:
        socket.rated_power_w = dec(data["rated_power_w"])
    db.commit()
    db.refresh(socket)
    return socket


def delete_socket(db: Session, socket_id: int) -> None:
    socket = db.get(Socket, socket_id)
    if not socket:
        raise AppError("Socket not found", status_code=404)
    db.delete(socket)
    db.commit()


def socket_detail(db: Session, socket_id: int) -> dict:
    socket = db.get(Socket, socket_id)
    if not socket:
        raise AppError("Socket not found", status_code=404)
    return serialize_socket(socket)
