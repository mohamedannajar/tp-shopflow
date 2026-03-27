import pytest

from app.services.stock import verifier_stock, reserver_stock, liberer_stock

REDIS_MOCK_PATH = "app.services.stock.redis_client"


@pytest.mark.unit
class TestVerifierStock:
    def test_stock_suffisant(self, product_sample):
        assert verifier_stock(product_sample, 5) is True

    def test_stock_exact(self, product_sample):
        assert verifier_stock(product_sample, 10) is True

    def test_stock_insuffisant(self, product_sample):
        assert verifier_stock(product_sample, 11) is False

    def test_quantite_negative(self, product_sample):
        with pytest.raises(ValueError, match="Quantité invalide"):
            verifier_stock(product_sample, -1)


@pytest.mark.unit
class TestReserverStock:
    def test_reserver_stock_nominal(self, db_session, product_sample, mocker):
        redis_mock = mocker.patch(REDIS_MOCK_PATH)

        product = reserver_stock(product_sample, 3, db_session)

        assert product.stock == 7
        redis_mock.delete.assert_called_once_with(f"product:{product.id}:stock")

    def test_reserver_stock_exact(self, db_session, product_sample, mocker):
        redis_mock = mocker.patch(REDIS_MOCK_PATH)

        product = reserver_stock(product_sample, 10, db_session)

        assert product.stock == 0
        redis_mock.delete.assert_called_once_with(f"product:{product.id}:stock")

    def test_reserver_stock_insuffisant(self, db_session, product_sample, mocker):
        redis_mock = mocker.patch(REDIS_MOCK_PATH)

        with pytest.raises(ValueError, match="Stock insuffisant"):
            reserver_stock(product_sample, 11, db_session)

        redis_mock.delete.assert_not_called()

    def test_reserver_stock_quantite_negative(self, db_session, product_sample, mocker):
        redis_mock = mocker.patch(REDIS_MOCK_PATH)

        with pytest.raises(ValueError, match="Quantité invalide"):
            reserver_stock(product_sample, -1, db_session)

        redis_mock.delete.assert_not_called()


@pytest.mark.unit
class TestLibererStock:
    def test_liberer_stock_nominal(self, db_session, product_sample, mocker):
        redis_mock = mocker.patch(REDIS_MOCK_PATH)

        product = liberer_stock(product_sample, 2, db_session)

        assert product.stock == 12
        redis_mock.set.assert_called_once_with(f"product:{product.id}:stock", product.stock)

    def test_liberer_stock_quantite_negative(self, db_session, product_sample, mocker):
        redis_mock = mocker.patch(REDIS_MOCK_PATH)

        with pytest.raises(ValueError, match="Quantité invalide"):
            liberer_stock(product_sample, -2, db_session)

        redis_mock.set.assert_not_called()