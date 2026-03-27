import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import products, cart, orders, coupons

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ShopFlow démarrage — création des tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables créées. API prête.")
    yield
    logger.info("ShopFlow arrêt.")


app = FastAPI(
    title="ShopFlow API",
    description="API e-commerce pédagogique — Fil rouge Automatisation des Tests",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(coupons.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "version": "0.1.0", "db": "sqlite"}


@app.get("/", tags=["health"])
def root():
    return {"message": "ShopFlow API — /docs pour la documentation"}