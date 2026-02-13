from .admin_handlers import router as admin_router
from .customer_handlers import router as customer_router
from .payment_handlers import router as payment_router

__all__ = [
    "admin_router",
    "customer_router",
    "payment_router"
]
