from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.carrito import router as carrito_router
from app.api.v1.juegos import router as juegos_router
from app.api.v1.users import router as users_router

api_router = APIRouter()

# Orden de grupos en Swagger: 1) Auth, 2) Gestión de usuarios, 3) Carrito, 4) Catálogo
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(carrito_router)
api_router.include_router(juegos_router)