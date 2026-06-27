# Import all the models, so that Base has them before being
# imported by Alembic env.py
from app.db.base_class import Base  # noqa
from app.models.payment import Payment  # noqa
from app.models.history import PaymentHistory  # noqa
