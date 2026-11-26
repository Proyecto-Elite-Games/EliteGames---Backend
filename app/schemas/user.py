from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.domain.enums.user_role import UserRole


class ClientProfileCreate(BaseModel):
    birth_date: date | None = None
    address: str | None = Field(default=None, max_length=255)


class EmployeeProfileCreate(BaseModel):
    job_title: str = Field(min_length=2, max_length=100)
    hire_date: date | None = None
    is_available: bool = True
    notes: str | None = None


class UserCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=12, max_length=128)
    role: UserRole

    client_profile: ClientProfileCreate | None = None
    employee_profile: EmployeeProfileCreate | None = None

    @model_validator(mode="after")
    def validate_role_profiles(self):
        if self.role == UserRole.SUPER_ADMIN:
            raise ValueError("El SUPER_ADMIN no se puede crear desde este endpoint.")

        if self.role == UserRole.CLIENTE:
            if self.client_profile is None:
                raise ValueError("El cliente debe tener un perfil de cliente.")
            if self.employee_profile is not None:
                raise ValueError("Un cliente no puede tener perfil de empleado.")

        elif self.role == UserRole.ADMIN:
            if self.employee_profile is None:
                raise ValueError("El empleado debe tener un perfil de empleado.")
            if self.client_profile is not None:
                raise ValueError("Un empleado no puede tener perfil de cliente.")

        return self


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserResponse(BaseModel):
    """
    Información pública de un usuario.

    No incluye password_hash ni otros datos privados.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime