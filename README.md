# Elite Games

Backend del sistema Elite Games: una API REST construida con **FastAPI**, **SQLAlchemy 2**, **PyMySQL** y **MySQL**.

## Requisitos

- Python 3.11 o superior
- MySQL 8 (solo a partir de la Fase 2, cuando se configuren las migraciones)

## Instalación

### 1. Crear el entorno virtual (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> Si PowerShell bloquea la ejecución del script de activación:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### 2. Instalar las dependencias

```powershell
pip install -r requirements.txt
```

### 3. Configurar las variables de entorno

```powershell
copy .env.example .env
```

Edita `.env` y ajusta `DATABASE_URL` con el usuario, la contraseña y el host de tu instalación local de MySQL.

### 4. Ejecutar la API

```powershell
uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000` y la documentación interactiva en `http://127.0.0.1:8000/docs`.

## Endpoints de salud

| Método | Ruta           | Descripción                                        |
|--------|----------------|----------------------------------------------------|
| GET    | `/health`      | Verifica que la API está activa.                   |
| GET    | `/health/ready`| Verifica que la API puede conectarse a MySQL.      |

## Pruebas

```powershell
pytest
```

## Estructura

```
app/
├── api/            # Routers de FastAPI (health, v1, ...)
├── core/           # Configuración y excepciones
├── domain/         # Entidades, enums e interfaces del dominio
├── infrastructure/ # Base de datos, engine y sesiones
├── models/         # Modelos SQLAlchemy
├── repositories/   # Acceso a datos
├── schemas/        # Schemas de Pydantic
├── services/       # Lógica de negocio
└── utils/          # Utilidades
```
