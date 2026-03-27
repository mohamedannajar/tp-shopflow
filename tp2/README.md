# ShopFlow — TP2

Fil rouge **Automatisation des tests** : ce dossier reprend la base du TP1 et ajoute des **tests d’intégration API**, des **données de test avec Faker**, et un **cache Redis** (avec repli si Redis est absent).

## Objectif du TP2

- Tester l’API FastAPI **de bout en bout** avec `TestClient` et une base **SQLite en mémoire**.
- Isoler la couche HTTP + dépendances (`get_db`) via des **fixtures** réutilisables.
- Renforcer la couverture avec des scénarios **produits**, **panier**, **commandes** et **santé de l’API**.
- Générer des jeux de données **variés** avec **Faker** (locale `fr_FR`).
- Mettre en place un **cache** pour la lecture détail d’un produit, avec invalidation à la mise à jour / suppression.

## Ce qui a été mis en place

### API

- **Produits** : liste avec filtres optionnels `category`, `min_price`, `max_price`, pagination `skip` / `limit` ; détail d’un produit avec **mise en cache** (clé `product:{id}`) et **invalidation** du cache lors d’un `PUT` ou d’un `DELETE` logique.
- **Cache** (`app/cache.py`) : client **Redis** si disponible (`REDIS_URL`, défaut `redis://localhost:6379`) ; sinon **repli** sur un mock pour ne pas bloquer les tests ni le dev local sans Redis.
- **Observabilité** : endpoints `/health`, `/`, documentation Swagger `/docs` et schéma OpenAPI `/openapi.json`.

### Tests

- **Unitaires** (hérités du TP1) : logique métier dans `tests/unit/` avec fixtures `db_session`, `product_sample`, etc.
- **Intégration** (`@pytest.mark.integration`) :
  - `tests/integration/test_health.py` — santé, racine, `/docs`, `/openapi.json`
  - `tests/integration/test_products_api.py` — liste, filtres, pagination, cache, erreurs 404
  - `tests/integration/test_cart_api.py` — ajout au panier, sous-total, erreurs stock
  - `tests/integration/test_orders_api.py` — création commande, totaux HT/TTC, stock, cas d’erreur
  - `tests/integration/test_faker_products.py` — données aléatoires cohérentes, validation des prix
- **Tests API regroupés** : `tests/test_api_routes.py` — scénarios transverses (produits, panier, commandes, coupons).

### Fixtures (`tests/conftest.py`)

- `client` : application testée avec **override** de `get_db` sur une base SQLite **:memory:** (scope `module`).
- `api_product` / `api_coupon` : création via l’API pour les tests qui en ont besoin.
- `fake_product_data` / `multiple_products` : jeux de données **Faker** pour stresser la liste et la validation.

### Configuration Pytest

- Marqueur `integration` déclaré dans `pytest.ini`.
- Couverture du package `app` avec rapport HTML + seuil `--cov-fail-under=80` (voir section ci‑dessous).

## Prérequis

- **Python 3.13** (recommandé pour ce projet ; SQLAlchemy est épinglé en **2.0.48** pour la compatibilité).
- Dépendances : `pip install -r requirements.txt` (idéalement dans un **venv** sous `tp2/venv`).

## Lancer l’API

```powershell
cd tp2
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Documentation interactive : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

*(Optionnel)* Redis en local pour activer le vrai cache : variable d’environnement `REDIS_URL` ou instance par défaut sur `localhost:6379`.

## Lancer les tests

Depuis `tp2`, avec le Python du venv :

```powershell
.\venv\Scripts\python.exe -m pytest
```

- Pour **uniquement les tests d’intégration** :

  ```powershell
  .\venv\Scripts\python.exe -m pytest -m integration
  ```

- Pour **lister les tests sans exécuter la couverture** (évite le seuil 80 % sur un simple inventaire) :

  ```powershell
  .\venv\Scripts\python.exe -m pytest --collect-only --no-cov
  ```

### PowerShell : activation du venv

Si `Activate.ps1` est bloqué par la stratégie d’exécution, pour la session courante :

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
.\venv\Scripts\Activate.ps1
```

Sinon, utilisez directement `.\venv\Scripts\python.exe -m pytest` sans activer le venv.

## Structure utile

```text
tp2/
  app/                 # Application FastAPI (routes, services, cache, DB)
  tests/
    unit/              # Tests unitaires métier
    integration/       # Tests d’intégration HTTP
    test_api_routes.py # Scénarios API regroupés
  pytest.ini
  requirements.txt
```

---

*TP1 : logique métier et tests unitaires de base — TP2 : intégration API, Faker, cache Redis et couverture renforcée.*
