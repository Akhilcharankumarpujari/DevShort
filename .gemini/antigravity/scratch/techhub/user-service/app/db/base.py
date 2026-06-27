# Import all the models, so that Base has them before being
# imported by Alembic env.py
from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.token import RevokedToken  # noqa
