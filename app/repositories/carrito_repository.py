from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.detalle_pedido import DetallePedido
from app.models.juego import Juego
from app.models.pedido import Pedido


class CarritoRepository:
    @staticmethod
    def get_carrito_pendiente(db: Session, id_usuario: int) -> Pedido | None:
        return db.scalar(
            select(Pedido)
            .where(
                Pedido.idUsuario == id_usuario,
                Pedido.estado == "pendiente",
            )
            .order_by(Pedido.idPedido.desc())
        )

    @staticmethod
    def get_or_create_carrito_pendiente(db: Session, id_usuario: int) -> Pedido:
        carrito = CarritoRepository.get_carrito_pendiente(db, id_usuario)
        if carrito is None:
            carrito = Pedido(
                idUsuario=id_usuario,
                total=Decimal("0.00"),
                estado="pendiente",
            )
            db.add(carrito)
            db.flush()
        return carrito

    @staticmethod
    def get_detalles(db: Session, id_pedido: int) -> list[DetallePedido]:
        return list(
            db.scalars(
                select(DetallePedido)
                .where(DetallePedido.idPedido == id_pedido)
                .order_by(DetallePedido.idDetalle.asc())
            ).all()
        )

    @staticmethod
    def get_detalle_by_juego(
        db: Session, id_pedido: int, id_juego: int
    ) -> DetallePedido | None:
        return db.scalar(
            select(DetallePedido).where(
                DetallePedido.idPedido == id_pedido,
                DetallePedido.idJuego == id_juego,
            )
        )

    @staticmethod
    def get_juego(db: Session, id_juego: int) -> Juego | None:
        return db.scalar(select(Juego).where(Juego.idJuego == id_juego))