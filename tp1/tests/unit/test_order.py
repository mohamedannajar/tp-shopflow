import pytest

from app.models import Product, CartItem, OrderItem, Order, Coupon
from app.services.cart import get_or_create_cart, ajouter_au_panier
from app.services.order import creer_commande, mettre_a_jour_statut


@pytest.mark.unit
class TestCreerCommande:
    def test_creer_commande_panier_vide(self, db_session):
        cart = get_or_create_cart(42, db_session)

        with pytest.raises(ValueError, match="Panier vide"):
            creer_commande(42, cart, db_session)

    def test_creer_commande_sans_coupon(self, db_session):
        product = Product(name="Produit A", price=100.0, stock=10, active=True)
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        cart = ajouter_au_panier(product, 2, 42, db_session)

        order = creer_commande(42, cart, db_session)

        assert order is not None
        assert order.user_id == 42
        assert order.total_ht == 200.0
        assert order.total_ttc == 240.0
        assert order.coupon_code is None
        assert order.status == "pending"
        assert len(order.items) == 1
        assert order.items[0].product_id == product.id
        assert order.items[0].quantity == 2
        assert order.items[0].unit_price == 100.0

    def test_creer_commande_avec_coupon(self, db_session):
        product = Product(name="Produit A", price=100.0, stock=10, active=True)
        coupon = Coupon(code="PROMO20", reduction=20.0, actif=True)

        db_session.add_all([product, coupon])
        db_session.commit()
        db_session.refresh(product)
        db_session.refresh(coupon)

        cart = ajouter_au_panier(product, 2, 42, db_session)

        order = creer_commande(42, cart, db_session, coupon)

        assert order.total_ht == 200.0
        assert order.total_ttc == 192.0
        assert order.coupon_code == "PROMO20"
        assert order.status == "pending"
        assert len(order.items) == 1

    def test_creer_commande_diminue_stock(self, db_session):
        product = Product(name="Produit A", price=50.0, stock=10, active=True)
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        cart = ajouter_au_panier(product, 3, 42, db_session)
        creer_commande(42, cart, db_session)

        db_session.refresh(product)
        assert product.stock == 7

    def test_creer_commande_vide_panier(self, db_session):
        product = Product(name="Produit A", price=50.0, stock=10, active=True)
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        cart = ajouter_au_panier(product, 2, 42, db_session)
        creer_commande(42, cart, db_session)

        cart_items = db_session.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        assert len(cart_items) == 0

    def test_creer_commande_cree_order_items(self, db_session):
        p1 = Product(name="Produit A", price=50.0, stock=10, active=True)
        p2 = Product(name="Produit B", price=30.0, stock=10, active=True)
        db_session.add_all([p1, p2])
        db_session.commit()
        db_session.refresh(p1)
        db_session.refresh(p2)

        cart = ajouter_au_panier(p1, 1, 42, db_session)
        cart = ajouter_au_panier(p2, 2, 42, db_session)

        order = creer_commande(42, cart, db_session)

        order_items = db_session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        assert len(order_items) == 2


@pytest.mark.unit
class TestMettreAJourStatut:
    def test_mettre_a_jour_statut_commande_introuvable(self, db_session):
        with pytest.raises(ValueError, match="Commande 999 introuvable"):
            mettre_a_jour_statut(999, "confirmed", db_session)

    def test_mettre_a_jour_statut_pending_vers_confirmed(self, db_session):
        order = Order(user_id=42, total_ht=100.0, total_ttc=120.0, status="pending")
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        updated = mettre_a_jour_statut(order.id, "confirmed", db_session)

        assert updated.status == "confirmed"

    def test_mettre_a_jour_statut_confirmed_vers_shipped(self, db_session):
        order = Order(user_id=42, total_ht=100.0, total_ttc=120.0, status="confirmed")
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        updated = mettre_a_jour_statut(order.id, "shipped", db_session)

        assert updated.status == "shipped"

    def test_mettre_a_jour_statut_transition_invalide(self, db_session):
        order = Order(user_id=42, total_ht=100.0, total_ttc=120.0, status="pending")
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        with pytest.raises(ValueError, match="Transition invalide"):
            mettre_a_jour_statut(order.id, "shipped", db_session)

    def test_mettre_a_jour_statut_depuis_shipped_impossible(self, db_session):
        order = Order(user_id=42, total_ht=100.0, total_ttc=120.0, status="shipped")
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        with pytest.raises(ValueError, match="Transition invalide"):
            mettre_a_jour_statut(order.id, "confirmed", db_session)