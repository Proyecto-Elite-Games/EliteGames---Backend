from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.inventario import Inventario
from app.models.juego import Juego
from app.models.user import User
from app.schemas.juego import (
    JuegoCatalogoResponse,
    JuegoCreate,
    JuegoResponse,
    JuegoUpdate,
)

router = APIRouter(prefix="/juegos", tags=["Catálogo"])

STOCK_BAJO_UMBRAL = 5


def _check_admin_role(user: User) -> None:
    role_value = (
        getattr(user, "role", None)
        or getattr(user, "rol", None)
        or getattr(user, "tipo_usuario", None)
    )
    if role_value is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para administrar el catálogo.",
        )

    raw_role = (
        getattr(role_value, "value", None)
        or getattr(role_value, "name", None)
        or str(role_value)
    )
    normalized_role = str(raw_role).strip().upper()
    allowed_roles = {"ADMIN", "ADMINISTRADOR", "SUPER_ADMIN", "PROVEEDOR", "PROVIDER"}

    if normalized_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para administrar el catálogo.",
        )


def _serialize_juego(juego: Juego, stock_disponible: int | None) -> JuegoResponse:
    return JuegoResponse(
        idJuego=juego.idJuego,
        nombre=juego.nombre,
        descripcion=juego.descripcion,
        desarrollador=juego.desarrollador,
        fecha_lanzamiento=juego.fecha_lanzamiento,
        imagen_url=juego.imagen_url,
        idProveedor=juego.idProveedor,
        idCategoria=juego.idCategoria,
        stock_disponible=stock_disponible if stock_disponible is not None else 0,
    )


@router.get("", response_model=JuegoCatalogoResponse)
def listar_juegos(
    idCategoria: int | None = Query(default=None, gt=0),
    idProveedor: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Juego, Inventario.stock_disponible)
        .outerjoin(Inventario, Inventario.idJuego == Juego.idJuego)
        .order_by(Juego.idJuego.desc())
    )

    if idCategoria is not None:
        stmt = stmt.where(Juego.idCategoria == idCategoria)
    if idProveedor is not None:
        stmt = stmt.where(Juego.idProveedor == idProveedor)

    rows = db.execute(stmt).all()
    items = [_serialize_juego(juego, stock) for juego, stock in rows]
    stock_bajo_count = sum(1 for item in items if item.stock_disponible <= STOCK_BAJO_UMBRAL)

    return JuegoCatalogoResponse(
        items=items,
        total=len(items),
        stock_bajo_count=stock_bajo_count,
    )


@router.get("/buscar", response_model=JuegoCatalogoResponse)
def buscar_juegos(
    q: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db),
):
    pattern = f"%{q.strip()}%"
    stmt = (
        select(Juego, Inventario.stock_disponible)
        .outerjoin(Inventario, Inventario.idJuego == Juego.idJuego)
        .where(
            Juego.nombre.ilike(pattern)
            | Juego.desarrollador.ilike(pattern)
            | Juego.descripcion.ilike(pattern)
        )
        .order_by(Juego.idJuego.desc())
    )

    rows = db.execute(stmt).all()
    items = [_serialize_juego(juego, stock) for juego, stock in rows]
    stock_bajo_count = sum(1 for item in items if item.stock_disponible <= STOCK_BAJO_UMBRAL)

    return JuegoCatalogoResponse(
        items=items,
        total=len(items),
        stock_bajo_count=stock_bajo_count,
    )


@router.get("/{idJuego}", response_model=JuegoResponse)
def obtener_juego(idJuego: int, db: Session = Depends(get_db)):
    row = db.execute(
        select(Juego, Inventario.stock_disponible)
        .outerjoin(Inventario, Inventario.idJuego == Juego.idJuego)
        .where(Juego.idJuego == idJuego)
    ).first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Juego no encontrado.",
        )

    juego, stock = row
    return _serialize_juego(juego, stock)


@router.post("", response_model=JuegoResponse, status_code=status.HTTP_201_CREATED)
def crear_juego(
    payload: JuegoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_admin_role(current_user)

    existente = db.execute(
        select(Juego).where(func.lower(Juego.nombre) == payload.nombre.strip().lower())
    ).scalar_one_or_none()
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un juego registrado con ese nombre.",
        )

    nuevo_juego = Juego(
        nombre=payload.nombre.strip(),
        descripcion=payload.descripcion.strip() if payload.descripcion else None,
        desarrollador=payload.desarrollador.strip() if payload.desarrollador else None,
        fecha_lanzamiento=payload.fecha_lanzamiento,
        imagen_url=payload.imagen_url.strip() if payload.imagen_url else None,
        idProveedor=payload.idProveedor,
        idCategoria=payload.idCategoria,
    )
    db.add(nuevo_juego)
    db.flush()

    inventario = Inventario(
        idJuego=nuevo_juego.idJuego,
        stock_disponible=payload.stock_disponible,
    )
    db.add(inventario)
    db.commit()
    db.refresh(nuevo_juego)

    return _serialize_juego(nuevo_juego, payload.stock_disponible)


@router.put("/{idJuego}", response_model=JuegoResponse)
def actualizar_juego(
    idJuego: int,
    payload: JuegoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_admin_role(current_user)

    juego = db.execute(select(Juego).where(Juego.idJuego == idJuego)).scalar_one_or_none()
    if juego is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Juego no encontrado.",
        )

    updates = payload.model_dump(exclude_unset=True)
    stock_nuevo = updates.pop("stock_disponible", None)

    for field, value in updates.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(juego, field, value)

    inventario = db.execute(
        select(Inventario).where(Inventario.idJuego == idJuego)
    ).scalar_one_or_none()

    if stock_nuevo is not None:
        if inventario is None:
            inventario = Inventario(idJuego=idJuego, stock_disponible=stock_nuevo)
            db.add(inventario)
        else:
            inventario.stock_disponible = stock_nuevo

    db.commit()
    db.refresh(juego)
    stock_actual = inventario.stock_disponible if inventario is not None else 0

    return _serialize_juego(juego, stock_actual)


@router.delete("/{idJuego}", status_code=status.HTTP_200_OK)
def eliminar_juego(
    idJuego: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_admin_role(current_user)

    juego = db.execute(select(Juego).where(Juego.idJuego == idJuego)).scalar_one_or_none()
    if juego is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Juego no encontrado.",
        )

    db.delete(juego)
    db.commit()
    return {"message": "Juego eliminado correctamente."}