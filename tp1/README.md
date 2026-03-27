# ShopFlow — TP1

Fil rouge **Automatisation des tests** : première étape avec une API **FastAPI** e-commerce, persistance **SQLite** (SQLAlchemy), et une base solide de **tests unitaires** sur la logique métier, complétée par des **tests API** dans un fichier dédié.

## Objectif du TP1

- Mettre en place le **domaine** (produits, panier, commandes, coupons, stock, tarification).
- Couvrir les **services** avec des tests **unitaires** isolés (session DB en mémoire par test).
- Vérifier les **routes HTTP** essentielles avec **FastAPI `TestClient`** et **override** de la dépendance `get_db`.
- Introduire un **cache Redis** (avec repli si Redis est indisponible) pour la lecture détail d’un produit.

## Ce qui est en place

### Application

- **FastAPI** avec routes `products`, `cart`, `orders`, `coupons`, CORS, création des tables au démarrage.
- **Endpoints** : `/health`, `/`, documentation sur `/docs`.
- **Produits** : liste avec filtres `category`, `min_price`, `max_price`, pagination `skip` / `limit` ; détail avec **mise en cache** Redis (clé `product:{id}`) et invalidation sur mise à jour / suppression logique.
- **Cache** (`app/cache.py`) : connexion **Redis** si disponible (`REDIS_URL`) ; sinon comportement dégradé pour le développement et les tests.

### Tests

- **Unitaires** (`tests/unit/`) : panier, commande, prix TTC / coupons, stock — avec fixtures `db_session`, `product_sample`, `coupon_sample`.
- **API** (`tests/test_api_routes.py`) : scénarios regroupés (santé, produits + cache, panier, commandes, coupons). Le fixture `client` s’appuie sur la même **session SQLite en mémoire** que les tests unitaires (`override` de `get_db`).

> Le TP1 ne contient **pas** le dossier `tests/integration/` ni les jeux de données **Faker** du TP2 : la séparation marqueur `integration` et les tests par module arrivent dans **`tp2/`**.

### Configuration Pytest (`pytest.ini`)

- Couverture du package `app` avec rapport HTML et seuil `--cov-fail-under=80`.
- Marqueurs déclarés (`unit`, `integration`, etc.) pour préparer la suite du fil rouge.

## Prérequis

- **Python 3.11+** ou **3.13** (avec **SQLAlchemy ≥ 2.0.37** recommandé pour Python 3.13 — voir `requirements.txt`).
- Installer les dépendances dans un **venv** :

  ```powershell
  cd tp1
  python -m venv venv
  .\venv\Scripts\python.exe -m pip install -r requirements.txt
  ```

## Lancer l’API

```powershell
cd tp1
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Documentation : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Lancer les tests

```powershell
cd tp1
.\venv\Scripts\python.exe -m pytest
```

- Inventaire des tests sans appliquer la couverture (évite le seuil 80 % sur `--collect-only`) :

  ```powershell
  .\venv\Scripts\python.exe -m pytest --collect-only --no-cov
  ```

### PowerShell et scripts d’activation

Si `Activate.ps1` est bloqué :

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
.\venv\Scripts\Activate.ps1
```

Sinon, utilisez directement `.\venv\Scripts\python.exe -m pytest`.

## Structure utile

```text
tp1/
  app/
    routes/          # Endpoints REST
    services/      # Logique métier (panier, commande, prix, stock)
    models.py, schemas.py, database.py, cache.py, main.py
  tests/
    unit/          # Tests unitaires par module métier
    test_api_routes.py
    conftest.py    # db_engine, db_session, échantillons produit / coupon
  pytest.ini
  requirements.txt
```

---

*TP1 : fondations API + tests unitaires + premiers tests HTTP — TP2 (`../tp2/`) : intégration structurée, Faker et dossier `tests/integration/`.*
