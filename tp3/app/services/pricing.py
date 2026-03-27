from typing import Optional, List, Tuple
from app.models import Product, Coupon

TVA_RATE = 0.20


def calcul_prix_ttc(prix_ht: float) -> float:
    if prix_ht < 0:
        raise ValueError(f"Prix HT invalide : {prix_ht}")
    return round(prix_ht * (1 + TVA_RATE), 2)


def appliquer_coupon(prix: float, coupon: Coupon) -> float:
    if not coupon.actif:
        raise ValueError(f"Coupon inactif : {coupon.code}")
    if not 0 < coupon.reduction <= 100:
        raise ValueError(f"Réduction invalide : {coupon.reduction}")
    return round(prix * (1 - coupon.reduction / 100), 2)


def calculer_total(
    produits: List[Tuple[Product, int]],
    coupon: Optional[Coupon] = None
) -> float:
    if not produits:
        return 0.0

    total_ht = sum(p.price * q for p, q in produits)
    total_ttc = calcul_prix_ttc(total_ht)

    if coupon:
        total_ttc = appliquer_coupon(total_ttc, coupon)

    return total_ttc