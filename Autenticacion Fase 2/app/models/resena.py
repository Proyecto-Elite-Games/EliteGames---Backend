from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Resena(Base):
    """Tabla `resenas`."""

    __tablename__ = "resenas"
    __table_args__ = (
        CheckConstraint("calificacion BETWEEN 1 AND 5", name="ck_resenas_calificacion"),
    )

    idResena: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idUsuario: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.idUsuario", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    idJuego: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("juegos.idJuego", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    calificacion: Mapped[int] = mapped_column(TINYINT, nullable=False)
    comentario: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_resena: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP")
    )

    def __init__(
        self,
        idUsuario: int,
        idJuego: int,
        calificacion: int,
        comentario: Optional[str] = None,
        fecha_resena: Optional[datetime] = None,
        idResena: Optional[int] = None,
    ):
        if idResena is not None:
            self.idResena = idResena
        self.idUsuario = idUsuario
        self.idJuego = idJuego
        self.calificacion = calificacion
        self.comentario = comentario
        if fecha_resena is not None:
            self.fecha_resena = fecha_resena

    def json(self) -> dict:
        return {
            "idResena": self.idResena,
            "idUsuario": self.idUsuario,
            "idJuego": self.idJuego,
            "calificacion": self.calificacion,
            "comentario": self.comentario,
            "fecha_resena": self.fecha_resena.isoformat() if self.fecha_resena else None,
        }

    def __str__(self) -> str:
        return (
            f"Resena(idResena={self.idResena}, idUsuario={self.idUsuario}, "
            f"idJuego={self.idJuego}, calificacion={self.calificacion})"
        )