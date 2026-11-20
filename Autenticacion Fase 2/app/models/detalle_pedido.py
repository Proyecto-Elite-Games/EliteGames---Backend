from decimal import Decimal
from typing import Optional, Union

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class DetallePedido(Base):
    """Tabla `detalle_pedido`."""

    __tablename__ = "detalle_pedido"

    idDetalle: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idPedido: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pedidos.idPedido", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    idJuego: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("juegos.idJuego", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    def __init__(
        self,
        idPedido: int,
        idJuego: int,
        cantidad: int,
        precio_unitario: Union[Decimal, float, int, str],
        idDetalle: Optional[int] = None,
    ):
        if idDetalle is not None:
            self.idDetalle = idDetalle
        self.idPedido = idPedido
        self.idJuego = idJuego
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario

    def json(self) -> dict:
        return {
            "idDetalle": self.idDetalle,
            "idPedido": self.idPedido,
            "idJuego": self.idJuego,
            "cantidad": self.cantidad,
            "precio_unitario": float(self.precio_unitario) if self.precio_unitario is not None else None,
        }

    def __str__(self) -> str:
        return (
            f"DetallePedido(idDetalle={self.idDetalle}, idPedido={self.idPedido}, "
            f"idJuego={self.idJuego}, cantidad={self.cantidad}, precio_unitario={self.precio_unitario})"
        )