from .admin_handlers import router as admin_router
from .customer_handlers import router as customer_router
from .payment_handlers import router as payment_router
from .shop_settings import router as settings_router

# Wir bündeln alle Router in einer Liste für einen einfachen Import in der main.py
all_handlers = [
    admin_router,
    customer_router,
    payment_router,
    settings_router
]

__all__ = [
    "admin_router",
    "customer_router",
    "payment_router",
    "settings_router",
    "all_handlers"
]
