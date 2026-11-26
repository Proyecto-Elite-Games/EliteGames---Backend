"""
Rutas de autenticación de Elite Games.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import bearer_scheme, get_current_user
from app.core.config import settings
from app.infrastructure.database.session import get_db
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendCodeRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyCodeRequest,
)
from app.schemas.user import UserResponse
from app.services.auth_service import (
    AuthFlowError,
    AuthenticationError,
    authenticate_user,
    register_gamer_request,
    request_password_reset,
    resend_verification_code,
    reset_password_with_code,
    verify_gamer_code,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# =========================================================
# 1. REGISTRO Y VERIFICACIÓN DE CUENTA GAMER (CLIENTE)
# =========================================================


@router.post(
    "/registro",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="1. Registrar cuenta gamer y enviar código",
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Registra una cuenta gamer pendiente y envía código de verificación."""
    try:
        msg = register_gamer_request(
            db=db,
            first_name=data.first_name,
            last_name=data.last_name,
            email=str(data.email),
            password=data.password,
            phone=data.phone,
        )
        return MessageResponse(message=msg)
    except AuthFlowError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/verificar",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="2. Verificar código y activar cuenta",
)
def verify_code(
    data: VerifyCodeRequest,
    db: Session = Depends(get_db),
):
    """Verifica la cuenta con el código de 6 dígitos y crea el usuario."""
    try:
        return verify_gamer_code(
            db=db,
            email=str(data.email),
            code=data.code,
        )
    except AuthFlowError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/reenviar-codigo",
    response_model=MessageResponse,
    summary="3. Reenviar código de verificación",
)
def resend_code(
    data: ResendCodeRequest,
    db: Session = Depends(get_db),
):
    """Genera y envía un nuevo código de verificación de 6 dígitos."""
    try:
        msg = resend_verification_code(
            db=db,
            email=str(data.email),
        )
        return MessageResponse(message=msg)
    except AuthFlowError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# =========================================================
# 2. INICIO DE SESIÓN Y RECUPERACIÓN DE CONTRASEÑA
# =========================================================


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="4. Iniciar sesión (obtener token JWT)",
)
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Autentica al usuario y devuelve su token."""
    try:
        access_token, expires_in = authenticate_user(
            db=db,
            email=str(data.email),
            password=data.password,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return TokenResponse(
            access_token=access_token,
            expires_in=expires_in,
        )
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos.",
        )


@router.post(
    "/recuperar",
    response_model=MessageResponse,
    summary="5. Solicitar código para recuperar contraseña",
)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """Solicita un código de 6 dígitos de recuperación de contraseña."""
    msg = request_password_reset(
        db=db,
        email=str(data.email),
    )
    return MessageResponse(message=msg)


@router.post(
    "/restablecer",
    response_model=MessageResponse,
    summary="6. Restablecer contraseña con código",
)
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Define una nueva contraseña usando el código de 6 dígitos."""
    try:
        msg = reset_password_with_code(
            db=db,
            email=str(data.email),
            code=data.code,
            new_password=data.new_password,
        )
        return MessageResponse(message=msg)
    except AuthFlowError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# =========================================================
# 3. SESIÓN ACTUAL (/me Y LOGOUT)
# =========================================================


@router.get(
    "/me",
    response_model=UserResponse,
    summary="7. Consultar sesión y usuario actual",
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """Devuelve el perfil del usuario autenticado."""
    return current_user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="8. Cerrar sesión actual (revocar token)",
)
def logout(
    credentials=Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoca únicamente la sesión del token actual."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autorizado.",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        )

    session_record = db.scalar(
        select(UserSession).where(
            UserSession.jti == payload["jti"],
            UserSession.user_id == current_user.id,
        )
    )

    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no encontrada.",
        )

    session_record.is_active = False
    session_record.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)