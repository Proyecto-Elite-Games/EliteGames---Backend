from typing import Optional

from sqlalchemy import Boolean, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Proveedor(Base):
    """Tabla `proveedores`."""

    __tablename__ = "proveedores"

    idProveedor: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    razon_social: Mapped[str] = mapped_column(String(200), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    pais: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # TINYINT(1) DEFAULT 1
    activo: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, server_default=text("1")
    )

    def __init__(
        self,
        razon_social: str,
        telefono: Optional[str] = None,
        pais: Optional[str] = None,
        activo: Optional[bool] = None,
        idProveedor: Optional[int] = None,
    ):
        if idProveedor is not None:
            self.idProveedor = idProveedor
        self.razon_social = razon_social
        self.telefono = telefono
        self.pais = pais
        if activo is not None:
            self.activo = activo

    def json(self) -> dict:
        return {
            "idProveedor": self.idProveedor,
            "razon_social": self.razon_social,
            "telefono": self.telefono,
            "pais": self.pais,
            "activo": self.activo,
        }

    def __str__(self) -> str:
        return f"Proveedor(idProveedor={self.idProveedor}, razon_social={self.razon_social}, pais={self.pais}, activo={self.activo})"