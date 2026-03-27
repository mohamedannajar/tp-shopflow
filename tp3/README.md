# ShopFlow — TP3

Ce dossier est une **copie de travail du TP2** : même code, mêmes tests d’intégration, Faker et cache Redis. C’est ici que tu implémentes les **nouvelles exigences du TP3** sans modifier l’historique figé de `tp1/` et `tp2/`.

## Rapport avec les TPs précédents

| Dossier | Rôle |
|--------|------|
| `tp1/` | Base API + tests unitaires + premiers tests HTTP |
| `tp2/` | Intégration API structurée, Faker, dossier `tests/integration/` |
| **`tp3/`** | **Fil rouge actuel** — à partir de l’état du TP2 |

## Objectif du TP3

À compléter selon l’énoncé de ton cours (fonctionnalités, perf, CI, sécurité, etc.). Le point de départ fonctionnel est identique au TP2 décrit ci‑dessous.

### Rappel — ce que contient déjà cette base (héritée du TP2)

- **API** : produits (filtres, pagination, cache Redis sur le détail), panier, commandes, coupons ; `/health`, `/docs`, OpenAPI.
- **Tests** : unitaires `tests/unit/`, intégration `tests/integration/`, scénarios dans `tests/test_api_routes.py`.
- **Fixtures** : `client` SQLite en mémoire, Faker `fr_FR`, `api_product` / `api_coupon`, etc.

## Prérequis

- **Python 3.13** (recommandé) ; SQLAlchemy **2.0.48** dans `requirements.txt`.
- Créer un venv **dans `tp3/`** (le dossier `tp2/venv` n’est pas copié) :

  ```powershell
  cd tp3
  python -m venv venv
  .\venv\Scripts\python.exe -m pip install -r requirements.txt
  ```

## Lancer l’API

```powershell
cd tp3
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Documentation : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Lancer les tests

```powershell
cd tp3
.\venv\Scripts\python.exe -m pytest
```

- Tests d’intégration seuls : `.\venv\Scripts\python.exe -m pytest -m integration`
- Liste sans couverture : `.\venv\Scripts\python.exe -m pytest --collect-only --no-cov`

### PowerShell — `Activate.ps1` bloqué

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
.\venv\Scripts\Activate.ps1
```

## Structure utile

```text
tp3/
  app/
  tests/
    unit/
    integration/
    test_api_routes.py
  pytest.ini
  requirements.txt
```

---

*Après le TP3 : tu pourras taguer une release ou créer `tp4/` sur la même base si le fil rouge continue.*
