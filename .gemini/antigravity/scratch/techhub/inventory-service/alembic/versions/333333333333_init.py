"""init

Revision ID: 333333333333
Revises: 
Create Date: 2026-06-27 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '333333333333'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create inventory table
    op.create_table(
        'inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.String(length=50), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('available_quantity', sa.Integer(), nullable=False),
        sa.Column('reserved_quantity', sa.Integer(), nullable=False),
        sa.Column('low_stock_threshold', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_id'), 'inventory', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_product_id'), 'inventory', ['product_id'], unique=True)
    op.create_index(op.f('ix_inventory_sku'), 'inventory', ['sku'], unique=True)
    op.create_index(op.f('ix_inventory_warehouse_id'), 'inventory', ['warehouse_id'], unique=False)

    # Create inventory_history table
    op.create_table(
        'inventory_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inventory_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('quantity_changed', sa.Integer(), nullable=False),
        sa.Column('old_available', sa.Integer(), nullable=False),
        sa.Column('new_available', sa.Integer(), nullable=False),
        sa.Column('old_reserved', sa.Integer(), nullable=False),
        sa.Column('new_reserved', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_history_id'), 'inventory_history', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_history_inventory_id'), 'inventory_history', ['inventory_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_history_inventory_id'), table_name='inventory_history')
    op.drop_index(op.f('ix_inventory_history_id'), table_name='inventory_history')
    op.drop_table('inventory_history')
    op.drop_index(op.f('ix_inventory_warehouse_id'), table_name='inventory')
    op.drop_index(op.f('ix_inventory_sku'), table_name='inventory')
    op.drop_index(op.f('ix_inventory_product_id'), table_name='inventory')
    op.drop_index(op.f('ix_inventory_id'), table_name='inventory')
    op.drop_table('inventory')
