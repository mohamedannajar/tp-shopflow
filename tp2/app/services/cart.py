from sqlalchemy.orm import Session, joinedload
from app.models import Cart, CartItem, Product
from app.services.pricing import calcul_prix_ttc
from app.services.stock import verifier_stock


def get_or_create_cart(user_id: int, db: Session) -> Cart:
    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter(Cart.user_id == user_id)
        .first()
    )
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def ajouter_au_panier(product: Product, quantity: int, user_id: int, db: Session) -> Cart:
    if quantity <= 0:
        raise ValueError("La quantité doit être > 0")

    if not verifier_stock(product, quantity):
        raise ValueError("Stock insuffisant")

    cart = get_or_create_cart(user_id, db)

    existing_item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product.id)
        .first()
    )

    if existing_item:
        nouvelle_quantite = existing_item.quantity + quantity

        if not verifier_stock(product, nouvelle_quantite):
            raise ValueError("Stock insuffisant")

        existing_item.quantity = nouvelle_quantite
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity))

    db.commit()

    return (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter(Cart.id == cart.id)
        .first()
    )

def retirer_du_panier(cart: Cart, product_id: int, db: Session) -> Cart:
    item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        .first()
    )

    if not item:
        raise ValueError(f"Produit {product_id} absent du panier")

    db.delete(item)
    db.commit()

    return (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter(Cart.id == cart.id)
        .first()
    )


def vider_panier(cart: Cart, db: Session):
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()


def calculer_total_ttc(cart: Cart) -> float:
    total_ht = sum(item.product.price * item.quantity for item in cart.items if item.product)
    return calcul_prix_ttc(total_ht)