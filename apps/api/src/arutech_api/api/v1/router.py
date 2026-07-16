from fastapi import APIRouter

from arutech_api.api.v1.endpoints import auth, customers, health, leads, loans, public

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(public.router)
api_router.include_router(leads.router)
api_router.include_router(customers.router)
api_router.include_router(loans.router)
