from datetime import datetime
from decimal import Decimal
from typing import Optional, Union

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base

# Valores del ENUM tal como están en el CREATE TABLE.
ESTADOS_PEDIDO = ("pendiente", "completado", "cancelado", "enviado")


class Pedido(Base):
    """Tabla `pedidos`."""

    __tablename__ = "pedidos"

    idPedido: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idUsuario: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.idUsuario", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    fecha_pedido: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP")
    )
    total: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True, server_default=text("0.00")
    )
    estado: Mapped[Optional[str]] = mapped_column(
        Enum(*ESTADOS_PEDIDO, name="estado_pedido"),
        nullable=True,
        server_default=text("'pendiente'"),
    )

    def __init__(
        self,
        idUsuario: int,
        fecha_pedido: Optional[datetime] = None,
        total: Optional[Union[Decimal, float, int, str]] = None,
        estado: Optional[str] = None,
        idPedido: Optional[int] = None,
    ):
        if idPedido is not None:
            self.idPedido = idPedido
        self.idUsuario = idUsuario
        if fecha_pedido is not None:
            self.fecha_pedido = fecha_pedido
        if total is not None:
            self.total = total
        if estado is not None:
            self.estado = estado

    def json(self) -> dict:
        return {
            "idPedido": self.idPedido,
            "idUsuario": self.idUsuario,
            "fecha_pedido": self.fecha_pedido.isoformat() if self.fecha_pedido else None,
            "total": float(self.total) if self.total is not None else None,
            "estado": self.estado,
        }

    def __str__(self) -> str:
        return f"Pedido(idPedido={self.idPedido}, idUsuario={self.idUsuario}, total={self.total}, estado={self.estado})"