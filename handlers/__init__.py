from .admin_handlers import router as admin_router
from .customer_handlers import router as customer_router
from .payment_handlers import router as payment_router

# Wir bündeln die Router in einer Liste für einen noch saubereren Import in der main.py
all_handlers = [
    admin_router,
    customer_router,
    payment_router
]

__all__ = [
    "admin_router",
    "customer_router",
    "payment_router",
    "all_handlers"
]
