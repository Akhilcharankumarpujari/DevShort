# Import all the models, so that Base has them before being
# imported by Alembic env.py
from app.db.base_class import Base  # noqa
from app.models.cart import CartItem  # noqa
from app.models.order import Order, OrderItem  # noqa
from app.models.history import OrderHistory  # noqa
