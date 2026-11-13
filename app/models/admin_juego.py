from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class AdminJuego(Base):
    """Tabla `admin_juego` (PK compuesta: idAdmin + idJuego)."""

    __tablename__ = "admin_juego"

    idAdmin: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("administradores.idAdmin", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    idJuego: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("juegos.idJuego", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    def __init__(self, idAdmin: int, idJuego: int):
        self.idAdmin = idAdmin
        self.idJuego = idJuego

    def json(self) -> dict:
        return {
            "idAdmin": self.idAdmin,
            "idJuego": self.idJuego,
        }

    def __str__(self) -> str:
        return f"AdminJuego(idAdmin={self.idAdmin}, idJuego={self.idJuego})"