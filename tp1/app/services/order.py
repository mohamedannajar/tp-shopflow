from sqlalchemy.orm import Session, joinedload
from app.models import Cart, CartItem, Order, OrderItem, Coupon
from app.services.pricing import calcul_prix_ttc, appliquer_coupon
from app.services.stock import reserver_stock


VALID_TRANSITIONS = {
    "pending": ["confirmed"],
    "confirmed": ["shipped"],
    "shipped": []
}


def creer_commande(user_id: int, cart: Cart, db: Session, coupon: Coupon = None) -> Order:
    if not cart.items:
        raise ValueError("Panier vide")

    total_ht = 0.0

    for item in cart.items:
        reserver_stock(item.product, item.quantity, db)
        total_ht += item.product.price * item.quantity

    total_ttc = calcul_prix_ttc(total_ht)
    if coupon:
        total_ttc = appliquer_coupon(total_ttc, coupon)

    order = Order(
        user_id=user_id,
        total_ht=round(total_ht, 2),
        total_ttc=round(total_ttc, 2),
        coupon_code=coupon.code if coupon else None,
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    for item in cart.items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.product.price
        ))

    db.commit()

    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()

    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order.id)
        .first()
    )


def mettre_a_jour_statut(order_id: int, nouveau_statut: str, db: Session) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError(f"Commande {order_id} introuvable")

    if nouveau_statut not in VALID_TRANSITIONS.get(order.status, []):
        raise ValueError(f"Transition invalide : {order.status} -> {nouveau_statut}")

    order.status = nouveau_statut
    db.commit()
    db.refresh(order)
    return order