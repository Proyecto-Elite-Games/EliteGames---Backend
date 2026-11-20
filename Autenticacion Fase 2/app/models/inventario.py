from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, FetchedValue, ForeignKey, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Inventario(Base):
    """Tabla `inventario`."""

    __tablename__ = "inventario"

    idInventario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idJuego: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("juegos.idJuego", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    stock_disponible: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, server_default=text("0")
    )
    # DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    fecha_actualizacion: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=FetchedValue(),
    )

    def __init__(
        self,
        idJuego: int,
        stock_disponible: Optional[int] = None,
        fecha_actualizacion: Optional[datetime] = None,
        idInventario: Optional[int] = None,
    ):
        if idInventario is not None:
            self.idInventario = idInventario
        self.idJuego = idJuego
        if stock_disponible is not None:
            self.stock_disponible = stock_disponible
        if fecha_actualizacion is not None:
            self.fecha_actualizacion = fecha_actualizacion

    def json(self) -> dict:
        return {
            "idInventario": self.idInventario,
            "idJuego": self.idJuego,
            "stock_disponible": self.stock_disponible,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
        }

    def __str__(self) -> str:
        return f"Inventario(idInventario={self.idInventario}, idJuego={self.idJuego}, stock_disponible={self.stock_disponible})"