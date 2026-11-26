from pydantic import BaseModel, Field


class CarritoAgregarRequest(BaseModel):
    juegoId: int = Field(..., gt=0, description="ID del juego a agregar al carrito")
    cantidad: int = Field(default=1, ge=1, le=10, description="Cantidad de copias (1 a 10)")


class CarritoActualizarCantidadRequest(BaseModel):
    cantidad: int = Field(..., ge=1, le=10, description="Nueva cantidad de copias (1 a 10)")


class LineaCarritoResponse(BaseModel):
    juegoId: int
    nombre: str
    cantidad: int
    precioUnitario: int
    subtotalLinea: int


class CarritoResponse(BaseModel):
    pedidoId: int | None = None
    lineas: list[LineaCarritoResponse] = []
    subtotal: int = 0
    descuentos: int = 0
    iva: int = 0  # Pendiente de regla oficial de negocio (H-19)
    total: int = 0
    avisos: list[str] = []
    mensaje: str | None = None