from fastapi import APIRouter

from arutech_api.api.v1.endpoints import (
    admin_rbac,
    admin_users,
    auth,
    cms,
    customers,
    dashboard,
    health,
    leads,
    lenders,
    loan_products,
    loans,
    notification_templates,
    public,
    settings,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(public.router)
api_router.include_router(leads.router)
api_router.include_router(customers.router)
api_router.include_router(loans.router)
api_router.include_router(dashboard.router)
api_router.include_router(admin_users.router)
api_router.include_router(admin_rbac.router)
api_router.include_router(lenders.router)
api_router.include_router(loan_products.router)
api_router.include_router(notification_templates.router)
api_router.include_router(cms.router)
api_router.include_router(settings.router)
