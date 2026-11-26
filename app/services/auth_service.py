"""
Servicio de autenticación de Elite Games.
"""

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import json
import random
import smtplib
from urllib import error, request
from uuid import uuid4

import jwt
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.domain.enums.user_role import UserRole
from app.models.user import User
from app.models.user_session import UserSession

# Almacén temporal en memoria para registros pendientes de verificación:
# { email_lower: {"code": "123456", "expires_at": datetime, "data": dict} }
_PENDING_REGISTRATIONS: dict[str, dict] = {}

# Almacén temporal en memoria para códigos de recuperación de contraseña:
# { email_lower: {"code": "123456", "expires_at": datetime} }
_PENDING_PASSWORD_RESETS: dict[str, dict] = {}


class AuthenticationError(Exception):
    """Error cuando las credenciales no son válidas."""


class AuthFlowError(Exception):
    """Error controlado en flujos de registro, verificación o recuperación."""


def _send_via_resend(to_email: str, subject: str, body: str, from_addr: str) -> None:
    """Envía correo mediante la API HTTP de Resend."""
    api_key = getattr(settings, "RESEND_API_KEY", None)
    if not api_key:
        raise RuntimeError("RESEND_API_KEY no configurada.")

    payload = json.dumps(
        {
            "from": from_addr,
            "to": [to_email],
            "subject": subject,
            "text": body,
        }
    ).encode("utf-8")

    req = request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "EliteGames-API/1.0",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=15) as resp:
        if resp.status not in (200, 201, 202):
            raise RuntimeError(f"Resend respondió con estado {resp.status}")


def _send_email(to_email: str, subject: str, body: str) -> None:
    """Envía correo por Resend API o SMTP (587 STARTTLS / 465 SSL); si falla, imprime en consola."""
    smtp_host = getattr(settings, "SMTP_HOST", None)
    smtp_port = int(getattr(settings, "SMTP_PORT", 587))
    smtp_user = getattr(settings, "SMTP_USER", None)
    smtp_password = getattr(settings, "SMTP_PASSWORD", None)
    smtp_from_name = getattr(settings, "SMTP_FROM_NAME", "Elite Games")
    smtp_from_email = getattr(settings, "SMTP_FROM_EMAIL", None) or smtp_user
    resend_api_key = getattr(settings, "RESEND_API_KEY", None)
    resend_from_email = getattr(settings, "RESEND_FROM_EMAIL", None) or "onboarding@resend.dev"

    try:
        if resend_api_key:
            from_addr = (
                f"{smtp_from_name} <{resend_from_email}>"
                if "<" not in str(resend_from_email)
                else str(resend_from_email)
            )
            _send_via_resend(to_email, subject, body, from_addr)
            return

        if (
            not smtp_host
            or not smtp_user
            or not smtp_password
            or "AQUI_TU_CONTRASEÑA" in str(smtp_password)
        ):
            print(f"[DEV MAIL -> {to_email}] {subject}\n{body}")
            return

        from_addr = (
            f"{smtp_from_name} <{smtp_from_email}>"
            if "<" not in str(smtp_from_email)
            else str(smtp_from_email)
        )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_email
        msg.set_content(body)

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
    except (smtplib.SMTPException, error.URLError, OSError, RuntimeError) as exc:
        print(f"[DEV MAIL FALLBACK ({exc}) -> {to_email}] {subject}\n{body}")


def authenticate_user(
    db: Session,
    email: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[str, int]:
    """Autentica al usuario y registra una sesión activa. Retorna (access_token, expires_in)."""
    normalized_email = email.lower().strip()
    user = db.scalar(select(User).where(User.email == normalized_email))

    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("Correo electrónico o contraseña incorrectos.")

    if not user.is_active:
        raise AuthenticationError("Correo electrónico o contraseña incorrectos.")

    now = datetime.now(timezone.utc)
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expires_at = now + timedelta(seconds=expires_in)
    jti = str(uuid4())

    payload = {
        "sub": str(user.id),
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }

    access_token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    session_record = UserSession(
        user_id=user.id,
        jti=jti,
        last_activity_at=now.replace(tzinfo=None),
        expires_at=expires_at.replace(tzinfo=None),
        is_active=True,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    try:
        db.add(session_record)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    return access_token, expires_in


def register_gamer_request(
    db: Session,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    phone: str | None = None,
) -> str:
    """Crea un registro pendiente y envía un código de verificación de 6 dígitos."""
    normalized_email = email.lower().strip()
    existing = db.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        raise AuthFlowError("El correo electrónico ya está registrado.")

    code = f"{random.randint(0, 999999):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    _PENDING_REGISTRATIONS[normalized_email] = {
        "code": code,
        "expires_at": expires_at,
        "data": {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": normalized_email,
            "phone": phone.strip() if phone else None,
            "password_hash": hash_password(password),
        },
    }

    _send_email(
        to_email=normalized_email,
        subject="Código de verificación - Elite Games",
        body=(
            f"Tu código de verificación de 6 dígitos es: {code}\n"
            "Expira en 15 minutos."
        ),
    )
    return "Código de verificación enviado al correo."


def verify_gamer_code(db: Session, email: str, code: str) -> User:
    """Valida el código de 6 dígitos y crea el usuario CLIENTE en MySQL."""
    normalized_email = email.lower().strip()
    pending = _PENDING_REGISTRATIONS.get(normalized_email)

    if pending is None:
        raise AuthFlowError("No hay un registro pendiente para este correo.")

    if datetime.now(timezone.utc) > pending["expires_at"]:
        _PENDING_REGISTRATIONS.pop(normalized_email, None)
        raise AuthFlowError("El código de verificación ha expirado.")

    if pending["code"] != code.strip():
        raise AuthFlowError("Código de verificación inválido.")

    existing = db.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        _PENDING_REGISTRATIONS.pop(normalized_email, None)
        raise AuthFlowError("El correo electrónico ya está registrado.")

    payload = pending["data"]
    user = User(
        first_name=payload["first_name"],
        last_name=payload["last_name"],
        email=payload["email"],
        phone=payload["phone"],
        password_hash=payload["password_hash"],
        role=UserRole.CLIENTE,
        is_active=True,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except SQLAlchemyError:
        db.rollback()
        raise

    _PENDING_REGISTRATIONS.pop(normalized_email, None)
    return user


def resend_verification_code(db: Session, email: str) -> str:
    """Genera y reenvía un nuevo código de 6 dígitos."""
    normalized_email = email.lower().strip()
    existing = db.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        raise AuthFlowError("Esta cuenta ya está registrada y activa.")

    pending = _PENDING_REGISTRATIONS.get(normalized_email)
    if pending is None:
        raise AuthFlowError("No hay un registro pendiente para reenviar código.")

    new_code = f"{random.randint(0, 999999):06d}"
    pending["code"] = new_code
    pending["expires_at"] = datetime.now(timezone.utc) + timedelta(minutes=15)

    _send_email(
        to_email=normalized_email,
        subject="Nuevo código de verificación - Elite Games",
        body=(
            f"Tu nuevo código de verificación es: {new_code}\n"
            "Expira en 15 minutos."
        ),
    )
    return "Nuevo código de verificación enviado."


def request_password_reset(db: Session, email: str) -> str:
    """Genera un código de 6 dígitos de recuperación y lo envía por correo."""
    normalized_email = email.lower().strip()
    user = db.scalar(select(User).where(User.email == normalized_email))

    if user is None or not user.is_active:
        return "Si el correo existe, se ha enviado un código de 6 dígitos."

    expire_minutes = int(getattr(settings, "RESET_TOKEN_EXPIRE_MINUTES", 15))
    code = f"{random.randint(0, 999999):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

    _PENDING_PASSWORD_RESETS[normalized_email] = {
        "code": code,
        "expires_at": expires_at,
    }

    _send_email(
        to_email=user.email,
        subject="Código de recuperación de contraseña - Elite Games",
        body=(
            "Solicitaste restablecer tu contraseña en Elite Games.\n"
            f"Tu código de 6 dígitos es: {code}\n"
            f"Expira en {expire_minutes} minutos."
        ),
    )
    return "Si el correo existe, se ha enviado un código de 6 dígitos."


def reset_password_with_code(
    db: Session,
    email: str,
    code: str,
    new_password: str,
) -> str:
    """Valida el código de 6 dígitos, actualiza password_hash y envía correo de confirmación."""
    normalized_email = email.lower().strip()
    clean_code = code.strip()

    pending = _PENDING_PASSWORD_RESETS.get(normalized_email)
    if pending is None:
        raise AuthFlowError("No hay una solicitud de recuperación activa para este correo.")

    if datetime.now(timezone.utc) > pending["expires_at"]:
        _PENDING_PASSWORD_RESETS.pop(normalized_email, None)
        raise AuthFlowError("El código de 6 dígitos ha expirado. Solicita uno nuevo.")

    if pending["code"] != clean_code:
        raise AuthFlowError("El código de 6 dígitos es inválido.")

    user = db.scalar(select(User).where(User.email == normalized_email))
    if user is None or not user.is_active:
        raise AuthFlowError("Usuario no válido.")

    user.password_hash = hash_password(new_password)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    _PENDING_PASSWORD_RESETS.pop(normalized_email, None)

    _send_email(
        to_email=user.email,
        subject="Contraseña modificada correctamente - Elite Games",
        body=(
            "Hola,\n\n"
            "Tu contraseña en Elite Games fue modificada correctamente.\n"
            "Si no realizaste este cambio, contacta de inmediato con soporte."
        ),
    )

    return "Contraseña actualizada correctamente."


def reset_password_with_token(db: Session, token: str, new_password: str) -> str:
    """Valida un token JWT de recuperación y actualiza password_hash (compatibilidad)."""
    clean_token = token.strip()
    try:
        payload = jwt.decode(
            clean_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.InvalidTokenError:
        raise AuthFlowError("Token de recuperación inválido o expirado.")

    if payload.get("purpose") != "password_reset" or not payload.get("sub"):
        raise AuthFlowError("Token de recuperación inválido.")

    user = db.scalar(select(User).where(User.id == int(payload["sub"])))
    if user is None or not user.is_active:
        raise AuthFlowError("Usuario no válido.")

    user.password_hash = hash_password(new_password)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    _send_email(
        to_email=user.email,
        subject="Contraseña modificada correctamente - Elite Games",
        body=(
            "Hola,\n\n"
            "Tu contraseña en Elite Games fue modificada correctamente.\n"
            "Si no realizaste este cambio, contacta de inmediato con soporte."
        ),
    )

    return "Contraseña actualizada correctamente."