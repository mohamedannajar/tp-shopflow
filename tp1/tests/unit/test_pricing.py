import pytest

from app.models import Product
from app.services.pricing import calcul_prix_ttc, appliquer_coupon, calculer_total


@pytest.mark.unit
@pytest.mark.pricing
class TestCalculPrixTtc:
    def test_calcul_prix_ttc_nominal(self):
        assert calcul_prix_ttc(100.0) == 120.0

    def test_calcul_prix_ttc_zero(self):
        assert calcul_prix_ttc(0.0) == 0.0

    @pytest.mark.parametrize(
        "prix_ht, expected",
        [
            (10.0, 12.0),
            (50.0, 60.0),
            (99.99, 119.99),
            (1000.0, 1200.0),
        ],
    )
    def test_calcul_prix_ttc_parametrized(self, prix_ht, expected):
        assert calcul_prix_ttc(prix_ht) == expected

    def test_calcul_prix_ttc_negative(self):
        with pytest.raises(ValueError, match="Prix HT invalide"):
            calcul_prix_ttc(-1.0)


@pytest.mark.unit
@pytest.mark.pricing
class TestAppliquerCoupon:
    def test_appliquer_coupon_nominal(self, coupon_sample):
        assert appliquer_coupon(100.0, coupon_sample) == 80.0

    @pytest.mark.parametrize(
        "prix, reduction, expected",
        [
            (100.0, 10.0, 90.0),
            (100.0, 20.0, 80.0),
            (200.0, 50.0, 100.0),
            (80.0, 25.0, 60.0),
        ],
    )
    def test_appliquer_coupon_parametrized(self, prix, reduction, expected, db_session):
        from app.models import Coupon

        coupon = Coupon(code="TMP", reduction=reduction, actif=True)
        db_session.add(coupon)
        db_session.commit()
        assert appliquer_coupon(prix, coupon) == expected

    def test_appliquer_coupon_inactif(self, db_session):
        from app.models import Coupon

        coupon = Coupon(code="OFF", reduction=20.0, actif=False)
        db_session.add(coupon)
        db_session.commit()

        with pytest.raises(ValueError, match="Coupon inactif"):
            appliquer_coupon(100.0, coupon)

    @pytest.mark.parametrize("reduction", [0, -10, 101])
    def test_appliquer_coupon_reduction_invalide(self, reduction, db_session):
        from app.models import Coupon

        coupon = Coupon(code="BAD", reduction=reduction, actif=True)
        db_session.add(coupon)
        db_session.commit()

        with pytest.raises(ValueError, match="Réduction invalide"):
            appliquer_coupon(100.0, coupon)


@pytest.mark.unit
@pytest.mark.pricing
class TestCalculerTotal:
    def test_calculer_total_sans_coupon(self, db_session):
        p1 = Product(name="Produit A", price=50.0, stock=10, active=True)
        p2 = Product(name="Produit B", price=30.0, stock=5, active=True)
        db_session.add_all([p1, p2])
        db_session.commit()
        db_session.refresh(p1)
        db_session.refresh(p2)

        total = calculer_total([(p1, 1), (p2, 1)])
        assert total == 96.0

    def test_calculer_total_avec_coupon(self, db_session, coupon_sample):
        p1 = Product(name="Produit A", price=50.0, stock=10, active=True)
        p2 = Product(name="Produit B", price=30.0, stock=5, active=True)
        db_session.add_all([p1, p2])
        db_session.commit()
        db_session.refresh(p1)
        db_session.refresh(p2)

        total = calculer_total([(p1, 1), (p2, 1)], coupon_sample)
        assert total == 76.8

    def test_calculer_total_panier_vide(self):
        assert calculer_total([]) == 0.0