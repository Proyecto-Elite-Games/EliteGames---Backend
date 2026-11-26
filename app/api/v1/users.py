"""
Rutas de gestión de usuarios de Elite Games.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.domain.enums.user_role import UserRole
from app.infrastructure.database.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserStatusUpdate, UserUpdate
from app.services.user_service import (
    UserAlreadyExistsError,
    UserNotFoundError,
    UserService,
    UserServiceError,
)

router = APIRouter(
    prefix="/users",
    tags=["Gestión de usuarios"],
)


class ProfileMeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para gestionar usuarios.",
        )
    return current_user


# =========================================================
# 1. PERFIL DEL USUARIO AUTENTICADO (/me)
# =========================================================


@router.get(
    "/me",
    response_model=UserResponse,
    summary="1. Consultar perfil propio",
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="2. Actualizar datos personales propios",
)
def update_my_profile(
    data: ProfileMeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.first_name is not None:
        current_user.first_name = data.first_name
    if data.last_name is not None:
        current_user.last_name = data.last_name
    if data.phone is not None:
        current_user.phone = data.phone

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="3. Desactivar cuenta propia (baja lógica)",
)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.is_active = False
    db.commit()
    return {"message": "Cuenta desactivada correctamente."}


# =========================================================
# 2. GESTIÓN ADMINISTRATIVA DE USUARIOS (SOLO SUPER_ADMIN)
# =========================================================


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="4. Crear usuario (ADMIN o CLIENTE)",
)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    try:
        return UserService.create_user(db, data)
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[UserResponse],
    summary="5. Listar usuarios (filtros y paginación)",
)
def list_users(
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return UserService.list_users(
        db=db,
        role=role,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="6. Consultar detalle de usuario por ID",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    try:
        return UserService.get_user(db, user_id)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="7. Actualizar datos de usuario por ID",
)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    try:
        return UserService.update_user(db, user_id, data)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="8. Activar o desactivar usuario por ID",
)
def change_user_status(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    try:
        return UserService.change_status(
            db=db,
            user_id=user_id,
            is_active=data.is_active,
            current_user_id=current_user.id,
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
    summary="9. Desactivar usuario por ID (baja lógica)",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    try:
        return UserService.change_status(
            db=db,
            user_id=user_id,
            is_active=False,
            current_user_id=current_user.id,
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )