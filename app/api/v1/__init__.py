from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, companies, catalogs, products, match, feedback, admin

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(companies.router)
api_router.include_router(catalogs.router)
api_router.include_router(products.router)
api_router.include_router(match.router)
api_router.include_router(feedback.router)
api_router.include_router(admin.router)
