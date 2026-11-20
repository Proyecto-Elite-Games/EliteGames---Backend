from typing import Optional

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class PqrsReferencia(Base):
    """Tabla `pqrs_referencia`."""

    __tablename__ = "pqrs_referencia"

    idReferencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idPQRS: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pqrs.idPQRS", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    idPedido: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("pedidos.idPedido", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    idJuego: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("juegos.idJuego", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )

    def __init__(
        self,
        idPQRS: int,
        idPedido: Optional[int] = None,
        idJuego: Optional[int] = None,
        idReferencia: Optional[int] = None,
    ):
        if idReferencia is not None:
            self.idReferencia = idReferencia
        self.idPQRS = idPQRS
        self.idPedido = idPedido
        self.idJuego = idJuego

    def json(self) -> dict:
        return {
            "idReferencia": self.idReferencia,
            "idPQRS": self.idPQRS,
            "idPedido": self.idPedido,
            "idJuego": self.idJuego,
        }

    def __str__(self) -> str:
        return (
            f"PqrsReferencia(idReferencia={self.idReferencia}, idPQRS={self.idPQRS}, "
            f"idPedido={self.idPedido}, idJuego={self.idJuego})"
        )