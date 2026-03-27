import pytest


@pytest.mark.integration
class TestProductsAvecFaker:
    def test_creation_donnees_faker(self, client, fake_product_data):
        response = client.post("/products/", json=fake_product_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == fake_product_data["name"]
        assert data["price"] == fake_product_data["price"]

    def test_liste_avec_multiple_produits(self, client, multiple_products):
        response = client.get("/products/")
        assert response.status_code == 200

        ids_liste = [p["id"] for p in response.json()]
        for p in multiple_products:
            assert p["id"] in ids_liste

    @pytest.mark.parametrize(
        "prix,attendu_422",
        [
            (0.0, True),
            (-1.0, True),
            (0.01, False),
            (9999.99, False),
        ],
    )
    def test_validation_prix(self, client, prix, attendu_422):
        response = client.post(
            "/products/",
            json={"name": "Test", "price": prix, "stock": 1},
        )

        if attendu_422:
            assert response.status_code == 422
        else:
            assert response.status_code == 201

    def test_noms_longs(self, client):
        response_101 = client.post(
            "/products/",
            json={"name": "A" * 101, "price": 10.0, "stock": 1},
        )
        assert response_101.status_code == 422
        assert "name" in response_101.text

        response_100 = client.post(
            "/products/",
            json={"name": "A" * 100, "price": 10.0, "stock": 1},
        )
        assert response_100.status_code == 201