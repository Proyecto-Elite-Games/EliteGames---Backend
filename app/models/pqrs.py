from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base

TIPOS_PQRS = ("peticion", "queja", "reclamo", "sugerencia")
ESTADOS_PQRS = ("abierto", "en_proceso", "resuelto", "cerrado")
PRIORIDADES_PQRS = ("baja", "media", "alta", "urgente")


class Pqrs(Base):
    """Tabla `pqrs`."""

    __tablename__ = "pqrs"

    idPQRS: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nroRadicado: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    idUsuario: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.idUsuario", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(Enum(*TIPOS_PQRS, name="tipo_pqrs"), nullable=False)
    asunto: Mapped[str] = mapped_column(String(150), nullable=False)
    estado: Mapped[Optional[str]] = mapped_column(
        Enum(*ESTADOS_PQRS, name="estado_pqrs"),
        nullable=True,
        server_default=text("'abierto'"),
    )
    prioridad: Mapped[Optional[str]] = mapped_column(
        Enum(*PRIORIDADES_PQRS, name="prioridad_pqrs"),
        nullable=True,
        server_default=text("'media'"),
    )
    fecha_creacion: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP")
    )

    def __init__(
        self,
        nroRadicado: str,
        idUsuario: int,
        tipo: str,
        asunto: str,
        estado: Optional[str] = None,
        prioridad: Optional[str] = None,
        fecha_creacion: Optional[datetime] = None,
        idPQRS: Optional[int] = None,
    ):
        if idPQRS is not None:
            self.idPQRS = idPQRS
        self.nroRadicado = nroRadicado
        self.idUsuario = idUsuario
        self.tipo = tipo
        self.asunto = asunto
        if estado is not None:
            self.estado = estado
        if prioridad is not None:
            self.prioridad = prioridad
        if fecha_creacion is not None:
            self.fecha_creacion = fecha_creacion

    def json(self) -> dict:
        return {
            "idPQRS": self.idPQRS,
            "nroRadicado": self.nroRadicado,
            "idUsuario": self.idUsuario,
            "tipo": self.tipo,
            "asunto": self.asunto,
            "estado": self.estado,
            "prioridad": self.prioridad,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
        }

    def __str__(self) -> str:
        return (
            f"Pqrs(idPQRS={self.idPQRS}, nroRadicado={self.nroRadicado}, tipo={self.tipo}, "
            f"estado={self.estado}, prioridad={self.prioridad})"
        )