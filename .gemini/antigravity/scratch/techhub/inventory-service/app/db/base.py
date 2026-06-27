# Import all the models, so that Base has them before being
# imported by Alembic env.py
from app.db.base_class import Base  # noqa
from app.models.inventory import Inventory  # noqa
from app.models.history import InventoryHistory  # noqa
