from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class PqrsRespuesta(Base):
    """Tabla `pqrs_respuestas`."""

    __tablename__ = "pqrs_respuestas"

    idRespuesta: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idPQRS: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pqrs.idPQRS", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    idAdmin: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("administradores.idAdmin", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    idUsuario: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("usuarios.idUsuario", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_mensaje: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP")
    )

    def __init__(
        self,
        idPQRS: int,
        mensaje: str,
        idAdmin: Optional[int] = None,
        idUsuario: Optional[int] = None,
        fecha_mensaje: Optional[datetime] = None,
        idRespuesta: Optional[int] = None,
    ):
        if idRespuesta is not None:
            self.idRespuesta = idRespuesta
        self.idPQRS = idPQRS
        self.idAdmin = idAdmin
        self.idUsuario = idUsuario
        self.mensaje = mensaje
        if fecha_mensaje is not None:
            self.fecha_mensaje = fecha_mensaje

    def json(self) -> dict:
        return {
            "idRespuesta": self.idRespuesta,
            "idPQRS": self.idPQRS,
            "idAdmin": self.idAdmin,
            "idUsuario": self.idUsuario,
            "mensaje": self.mensaje,
            "fecha_mensaje": self.fecha_mensaje.isoformat() if self.fecha_mensaje else None,
        }

    def __str__(self) -> str:
        return (
            f"PqrsRespuesta(idRespuesta={self.idRespuesta}, idPQRS={self.idPQRS}, "
            f"idAdmin={self.idAdmin}, idUsuario={self.idUsuario})"
        )