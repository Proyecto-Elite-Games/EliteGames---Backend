from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class JuegoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = Field(default=None, max_length=2000)
    desarrollador: Optional[str] = Field(default=None, max_length=200)
    fecha_lanzamiento: Optional[date] = None
    imagen_url: Optional[str] = Field(default=None, max_length=500)
    idProveedor: int = Field(..., gt=0)
    idCategoria: int = Field(..., gt=0)
    stock_disponible: int = Field(default=0, ge=0)


class JuegoUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=200)
    descripcion: Optional[str] = Field(default=None, max_length=2000)
    desarrollador: Optional[str] = Field(default=None, max_length=200)
    fecha_lanzamiento: Optional[date] = None
    imagen_url: Optional[str] = Field(default=None, max_length=500)
    idProveedor: Optional[int] = Field(default=None, gt=0)
    idCategoria: Optional[int] = Field(default=None, gt=0)
    stock_disponible: Optional[int] = Field(default=None, ge=0)


class JuegoResponse(BaseModel):
    idJuego: int
    nombre: str
    descripcion: Optional[str] = None
    desarrollador: Optional[str] = None
    fecha_lanzamiento: Optional[date] = None
    imagen_url: Optional[str] = None
    idProveedor: int
    idCategoria: int
    stock_disponible: int = 0

    class Config:
        from_attributes = True


class JuegoCatalogoResponse(BaseModel):
    items: list[JuegoResponse]
    total: int
    stock_bajo_count: int