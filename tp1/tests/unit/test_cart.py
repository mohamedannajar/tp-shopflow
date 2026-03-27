import pytest

from app.models import CartItem
from app.services.cart import (
    get_or_create_cart,
    ajouter_au_panier,
    retirer_du_panier,
    vider_panier,
    calculer_total_ttc,
)


@pytest.mark.unit
class TestGetOrCreateCart:
    def test_create_cart_if_not_exists(self, db_session):
        cart = get_or_create_cart(42, db_session)

        assert cart is not None
        assert cart.user_id == 42
        assert cart.id is not None

    def test_get_existing_cart(self, db_session):
        cart1 = get_or_create_cart(42, db_session)
        cart2 = get_or_create_cart(42, db_session)

        assert cart1.id == cart2.id


@pytest.mark.unit
class TestAjouterAuPanier:
    def test_ajouter_produit_nouveau_panier(self, db_session, product_sample):
        cart = ajouter_au_panier(product_sample, 2, 42, db_session)

        assert cart.user_id == 42
        assert len(cart.items) == 1
        assert cart.items[0].product_id == product_sample.id
        assert cart.items[0].quantity == 2

    def test_ajouter_produit_panier_existant(self, db_session, product_sample):
        cart = ajouter_au_panier(product_sample, 2, 42, db_session)
        cart = ajouter_au_panier(product_sample, 3, 42, db_session)

        assert len(cart.items) == 1
        assert cart.items[0].quantity == 5

    def test_ajouter_quantite_invalide(self, db_session, product_sample):
        with pytest.raises(ValueError, match="quantité"):
            ajouter_au_panier(product_sample, 0, 42, db_session)


@pytest.mark.unit
class TestRetirerDuPanier:
    def test_retirer_produit_existant(self, db_session, product_sample):
        cart = ajouter_au_panier(product_sample, 2, 42, db_session)
        cart = retirer_du_panier(cart, product_sample.id, db_session)

        assert len(cart.items) == 0

    def test_retirer_produit_absent(self, db_session, product_sample):
        cart = get_or_create_cart(42, db_session)

        with pytest.raises(ValueError, match="absent du panier"):
            retirer_du_panier(cart, product_sample.id, db_session)


@pytest.mark.unit
class TestViderPanier:
    def test_vider_panier(self, db_session, product_sample):
        cart = ajouter_au_panier(product_sample, 2, 42, db_session)
        vider_panier(cart, db_session)

        items = db_session.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        assert len(items) == 0


@pytest.mark.unit
class TestCalculerTotalTtc:
    def test_calculer_total_ttc(self, db_session):
        from app.models import Product

        p1 = Product(name="Produit A", price=50.0, stock=10, active=True)
        p2 = Product(name="Produit B", price=30.0, stock=10, active=True)
        db_session.add_all([p1, p2])
        db_session.commit()
        db_session.refresh(p1)
        db_session.refresh(p2)

        cart = ajouter_au_panier(p1, 1, 42, db_session)
        cart = ajouter_au_panier(p2, 2, 42, db_session)

        total = calculer_total_ttc(cart)
        assert total == 132.0