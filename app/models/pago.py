from datetime import datetime
from decimal import Decimal
from typing import Optional, Union

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base

ESTADOS_PAGO = ("pendiente", "aprobado", "rechazado")


class Pago(Base):
    """Tabla `pagos`."""

    __tablename__ = "pagos"

    idPago: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idPedido: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pedidos.idPedido", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    metodo_pago: Mapped[str] = mapped_column(String(50), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    estado_pago: Mapped[Optional[str]] = mapped_column(
        Enum(*ESTADOS_PAGO, name="estado_pago"),
        nullable=True,
        server_default=text("'pendiente'"),
    )
    referencia: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    fecha_pago: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP")
    )

    def __init__(
        self,
        idPedido: int,
        metodo_pago: str,
        monto: Union[Decimal, float, int, str],
        estado_pago: Optional[str] = None,
        referencia: Optional[str] = None,
        fecha_pago: Optional[datetime] = None,
        idPago: Optional[int] = None,
    ):
        if idPago is not None:
            self.idPago = idPago
        self.idPedido = idPedido
        self.metodo_pago = metodo_pago
        self.monto = monto
        if estado_pago is not None:
            self.estado_pago = estado_pago
        self.referencia = referencia
        if fecha_pago is not None:
            self.fecha_pago = fecha_pago

    def json(self) -> dict:
        return {
            "idPago": self.idPago,
            "idPedido": self.idPedido,
            "metodo_pago": self.metodo_pago,
            "monto": float(self.monto) if self.monto is not None else None,
            "estado_pago": self.estado_pago,
            "referencia": self.referencia,
            "fecha_pago": self.fecha_pago.isoformat() if self.fecha_pago else None,
        }

    def __str__(self) -> str:
        return (
            f"Pago(idPago={self.idPago}, idPedido={self.idPedido}, metodo_pago={self.metodo_pago}, "
            f"monto={self.monto}, estado_pago={self.estado_pago})"
        )