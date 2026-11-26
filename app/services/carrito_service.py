from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.detalle_pedido import DetallePedido
from app.models.juego import Juego
from app.models.pedido import Pedido
from app.models.user import User
from app.models.usuario import Usuario
from app.repositories.carrito_repository import CarritoRepository
from app.schemas.carrito import (
    CarritoActualizarCantidadRequest,
    CarritoAgregarRequest,
    CarritoResponse,
    LineaCarritoResponse,
)


class CarritoError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CarritoService:
    MAX_COPIAS_POR_JUEGO = 10

    @staticmethod
    def _redondear_cop(valor: Decimal | int | float) -> int:
        return int(Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def resolver_id_usuario_dominio(db: Session, current_user: User) -> int:
        """
        Asegura que exista un registro en `usuarios` vinculado al `User` autenticado,
        ya que `pedidos.idUsuario` referencia a `usuarios.idUsuario`.
        """
        email = current_user.email.strip().lower()
        usuario = db.scalar(select(Usuario).where(Usuario.email == email))

        if usuario is None:
            usuario = Usuario(
                nombre=current_user.first_name,
                apellido=current_user.last_name,
                email=email,
                contrasena=current_user.password_hash or hash_password("Temporal123!"),
            )
            db.add(usuario)
            db.flush()

        return usuario.idUsuario

    @staticmethod
    def _estado_juego(
        db: Session,
        juego: Juego | None,
        detalle: DetallePedido | None = None,
    ) -> tuple[bool, int]:
        """
        Retorna (disponible, precio_unitario_cop) consultando `inventario` y `juego_plataforma`.
        """
        if juego is None:
            return False, 0

        stock = CarritoRepository.get_stock_juego(db, juego.idJuego)
        if stock is not None and stock <= 0:
            return False, 0

        precio_bd = CarritoRepository.get_precio_juego(db, juego.idJuego)
        if precio_bd is not None and precio_bd > 0:
            return True, CarritoService._redondear_cop(precio_bd)

        if (
            detalle is not None
            and detalle.precio_unitario is not None
            and detalle.precio_unitario > 0
        ):
            return True, CarritoService._redondear_cop(detalle.precio_unitario)

        return True, 0

    @staticmethod
    def _construir_respuesta(
        db: Session,
        carrito: Pedido | None,
        retirar_no_disponibles: bool = False,
        mensaje_extra: str | None = None,
    ) -> CarritoResponse:
        if carrito is None:
            return CarritoResponse(
                pedidoId=None,
                lineas=[],
                subtotal=0,
                descuentos=0,
                iva=0,
                total=0,
                avisos=[],
                mensaje=mensaje_extra or "Tu carrito está vacío",
            )

        detalles = CarritoRepository.get_detalles(db, carrito.idPedido)
        lineas_resp: list[LineaCarritoResponse] = []
        avisos: list[str] = []
        subtotal = 0

        for det in detalles:
            juego = CarritoRepository.get_juego(db, det.idJuego)
            disponible, precio_cop = CarritoService._estado_juego(db, juego, det)

            if not disponible:
                aviso = (
                    f"El juego '{juego.nombre}' ya no está disponible"
                    if juego is not None
                    else f"El juego con ID {det.idJuego} ya no está disponible"
                )
                avisos.append(aviso)
                if retirar_no_disponibles:
                    db.delete(det)
                continue

            if precio_cop > 0:
                det.precio_unitario = Decimal(precio_cop)

            subtotal_linea = precio_cop * det.cantidad
            subtotal += subtotal_linea

            lineas_resp.append(
                LineaCarritoResponse(
                    juegoId=det.idJuego,
                    nombre=juego.nombre if juego else f"Juego #{det.idJuego}",
                    cantidad=det.cantidad,
                    precioUnitario=precio_cop,
                    subtotalLinea=subtotal_linea,
                )
            )

        descuentos = 0
        iva = 0  # Sin definir en el negocio aún (H-19)
        total = max(0, subtotal - descuentos + iva)
        carrito.total = Decimal(total)

        mensaje = (
            mensaje_extra
            if mensaje_extra
            else ("Tu carrito está vacío" if not lineas_resp else None)
        )

        return CarritoResponse(
            pedidoId=carrito.idPedido,
            lineas=lineas_resp,
            subtotal=subtotal,
            descuentos=descuentos,
            iva=iva,
            total=total,
            avisos=avisos,
            mensaje=mensaje,
        )

    @staticmethod
    def obtener_carrito(db: Session, current_user: User) -> CarritoResponse:
        id_usuario = CarritoService.resolver_id_usuario_dominio(db, current_user)
        carrito = CarritoRepository.get_carrito_pendiente(db, id_usuario)
        resp = CarritoService._construir_respuesta(
            db=db,
            carrito=carrito,
            retirar_no_disponibles=True,
        )
        db.commit()
        return resp

    @staticmethod
    def agregar_juego(
        db: Session, current_user: User, data: CarritoAgregarRequest
    ) -> CarritoResponse:
        id_usuario = CarritoService.resolver_id_usuario_dominio(db, current_user)

        juego = CarritoRepository.get_juego(db, data.juegoId)
        disponible, precio_cop = CarritoService._estado_juego(db, juego)
        if not disponible or juego is None:
            raise CarritoError("El juego ya no está disponible", status_code=404)

        carrito = CarritoRepository.get_or_create_carrito_pendiente(db, id_usuario)
        detalle = CarritoRepository.get_detalle_by_juego(
            db, carrito.idPedido, data.juegoId
        )

        cantidad_actual = detalle.cantidad if detalle is not None else 0
        nueva_cantidad = cantidad_actual + data.cantidad

        if nueva_cantidad > CarritoService.MAX_COPIAS_POR_JUEGO:
            raise CarritoError("Máximo 10 copias por juego", status_code=400)

        if detalle is None:
            detalle = DetallePedido(
                idPedido=carrito.idPedido,
                idJuego=data.juegoId,
                cantidad=nueva_cantidad,
                precio_unitario=Decimal(precio_cop),
            )
            db.add(detalle)
        else:
            detalle.cantidad = nueva_cantidad
            if precio_cop > 0:
                detalle.precio_unitario = Decimal(precio_cop)

        resp = CarritoService._construir_respuesta(
            db=db,
            carrito=carrito,
            retirar_no_disponibles=False,
            mensaje_extra="Juego agregado al carrito",
        )
        db.commit()
        return resp

    @staticmethod
    def actualizar_cantidad(
        db: Session,
        current_user: User,
        juego_id: int,
        data: CarritoActualizarCantidadRequest,
    ) -> CarritoResponse:
        id_usuario = CarritoService.resolver_id_usuario_dominio(db, current_user)
        carrito = CarritoRepository.get_carrito_pendiente(db, id_usuario)
        if carrito is None:
            raise CarritoError("El juego no está en tu carrito", status_code=404)

        detalle = CarritoRepository.get_detalle_by_juego(db, carrito.idPedido, juego_id)
        if detalle is None:
            raise CarritoError("El juego no está en tu carrito", status_code=404)

        juego = CarritoRepository.get_juego(db, juego_id)
        disponible, precio_cop = CarritoService._estado_juego(db, juego, detalle)
        if not disponible:
            db.delete(detalle)
            CarritoService._construir_respuesta(
                db, carrito, retirar_no_disponibles=True
            )
            db.commit()
            raise CarritoError(
                "El juego ya no está disponible y fue retirado del carrito",
                status_code=409,
            )

        if detalle.cantidad == data.cantidad:
            return CarritoService._construir_respuesta(
                db=db,
                carrito=carrito,
                retirar_no_disponibles=False,
                mensaje_extra="Cantidad sin cambios",
            )

        detalle.cantidad = data.cantidad
        if precio_cop > 0:
            detalle.precio_unitario = Decimal(precio_cop)

        resp = CarritoService._construir_respuesta(
            db=db,
            carrito=carrito,
            retirar_no_disponibles=False,
            mensaje_extra="Cantidad actualizada",
        )
        db.commit()
        return resp

    @staticmethod
    def eliminar_juego(
        db: Session, current_user: User, juego_id: int
    ) -> CarritoResponse:
        id_usuario = CarritoService.resolver_id_usuario_dominio(db, current_user)
        carrito = CarritoRepository.get_carrito_pendiente(db, id_usuario)
        if carrito is None:
            raise CarritoError("El juego no está en tu carrito", status_code=404)

        detalle = CarritoRepository.get_detalle_by_juego(db, carrito.idPedido, juego_id)
        if detalle is None:
            raise CarritoError("El juego no está en tu carrito", status_code=404)

        db.delete(detalle)
        db.flush()

        resp = CarritoService._construir_respuesta(
            db=db,
            carrito=carrito,
            retirar_no_disponibles=False,
            mensaje_extra="Juego eliminado del carrito",
        )
        db.commit()
        return resp