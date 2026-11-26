from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.infrastructure.database.session import get_db
from app.models.user import User
from app.schemas.carrito import (
    CarritoActualizarCantidadRequest,
    CarritoAgregarRequest,
    CarritoResponse,
)
from app.services.carrito_service import CarritoError, CarritoService

# Crea el router del carrito. Como en v1/router.py se monta bajo /api/v1,
# estas rutas quedarán como /api/v1/carrito y /api/v1/carrito/{juego_id}.
router = APIRouter(
    prefix="/carrito",
    tags=["Carrito de compras"],
)


def _validar_gamer_y_obtener_id(current_user: User) -> int:
    """
    Revisa el rol del usuario autenticado (que viene del token JWT validado en get_current_user)
    y devuelve su id para que el carrito siempre pertenezca a quien hizo la petición.
    """
    rol_raw = getattr(current_user, "role", None) or getattr(current_user, "rol", None)
    rol_valor = rol_raw.value if hasattr(rol_raw, "value") else str(rol_raw or "").upper()

    # Aceptamos GAMER (según la matriz) y CLIENTE (el rol de cliente actual en el proyecto).
    # Si es otro rol (por ejemplo ADMIN o ESTETICISTA), devolvemos 403 Forbidden.
    if rol_valor not in {"GAMER", "CLIENTE"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los usuarios con rol gamer pueden gestionar el carrito.",
        )

    user_id = getattr(current_user, "id", None) or getattr(current_user, "idUsuario", None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no válida.",
        )

    return int(user_id)


@router.get("", response_model=CarritoResponse, status_code=status.HTTP_200_OK)
def consultar_carrito(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """E-021 / RF17: Consulta el carrito activo del usuario y su total calculado."""
    _validar_gamer_y_obtener_id(current_user)
    try:
        return CarritoService.obtener_carrito(db=db, current_user=current_user)
    except CarritoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("", response_model=CarritoResponse, status_code=status.HTTP_200_OK)
def agregar_juego_carrito(
    data: CarritoAgregarRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """E-022 / RF14: Agrega un juego al carrito (o suma cantidad hasta máximo 10)."""
    _validar_gamer_y_obtener_id(current_user)
    try:
        return CarritoService.agregar_juego(
            db=db,
            current_user=current_user,
            data=data,
        )
    except CarritoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.put(
    "/{juego_id}",
    response_model=CarritoResponse,
    status_code=status.HTTP_200_OK,
)
def actualizar_cantidad_juego(
    data: CarritoActualizarCantidadRequest,
    juego_id: int = Path(..., gt=0, description="ID del juego dentro del carrito"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """E-023 / RF15: Modifica la cantidad de un juego que ya está en el carrito."""
    _validar_gamer_y_obtener_id(current_user)
    try:
        return CarritoService.actualizar_cantidad(
            db=db,
            current_user=current_user,
            juego_id=juego_id,
            data=data,
        )
    except CarritoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.delete(
    "/{juego_id}",
    response_model=CarritoResponse,
    status_code=status.HTTP_200_OK,
)
def eliminar_juego_carrito(
    juego_id: int = Path(..., gt=0, description="ID del juego a quitar del carrito"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """E-024 / RF16: Elimina un juego del carrito y recalcula el total."""
    _validar_gamer_y_obtener_id(current_user)
    try:
        return CarritoService.eliminar_juego(
            db=db,
            current_user=current_user,
            juego_id=juego_id,
        )
    except CarritoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)