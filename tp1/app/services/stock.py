import logging
from sqlalchemy.orm import Session
from app.models import Product
from app.cache import redis_client

logger = logging.getLogger(__name__)


def verifier_stock(product: Product, quantite: int) -> bool:
    if quantite <= 0:
        raise ValueError(f"Quantité invalide : {quantite}")
    return product.stock >= quantite


def liberer_stock(product: Product, quantite: int, session: Session) -> Product:
    if quantite <= 0:
        raise ValueError(f"Quantité invalide : {quantite}")

    product.stock += quantite
    session.commit()
    session.refresh(product)
    redis_client.set(f"product:{product.id}:stock", product.stock)
    return product


def reserver_stock(product: Product, quantite: int, session: Session) -> Product:
    if not verifier_stock(product, quantite):
        raise ValueError(
            f"Stock insuffisant pour '{product.name}' : "
            f"{product.stock} disponible(s), {quantite} demandé(s)."
        )

    product.stock -= quantite
    session.commit()
    session.refresh(product)
    redis_client.delete(f"product:{product.id}:stock")
    logger.info(f"Stock réservé : {product.id}, qty={quantite}")
    return product