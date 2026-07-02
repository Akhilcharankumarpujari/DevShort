"""create booking service tables

Revision ID: c3d4e5f6g7h8
Revises: 
Create Date: 2026-06-30 20:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create bookings table
    op.create_table(
        'bookings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('booking_reference', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('movie_id', sa.String(length=36), nullable=False),
        sa.Column('theatre_id', sa.String(length=36), nullable=False),
        sa.Column('screen_id', sa.String(length=36), nullable=False),
        sa.Column('show_id', sa.String(length=36), nullable=False),
        sa.Column('booking_status', sa.String(length=50), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('payment_status', sa.String(length=50), nullable=False),
        sa.Column('booked_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookings_booking_reference'), 'bookings', ['booking_reference'], unique=True)

    # 2. Create booked_seats table
    op.create_table(
        'booked_seats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('booking_id', sa.String(length=36), nullable=False),
        sa.Column('seat_number', sa.String(length=50), nullable=False),
        sa.Column('seat_type', sa.String(length=50), nullable=False),
        sa.Column('seat_price', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_booked_seats_id'), 'booked_seats', ['id'], unique=False)

    # 3. Create seat_locks table
    op.create_table(
        'seat_locks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('show_id', sa.String(length=36), nullable=False),
        sa.Column('seat_number', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('locked_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_seat_locks_id'), 'seat_locks', ['id'], unique=False)
    op.create_index(op.f('ix_seat_locks_show_id'), 'seat_locks', ['show_id'], unique=False)

    # 4. Create booking_histories table
    op.create_table(
        'booking_histories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('booking_id', sa.String(length=36), nullable=False),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_booking_histories_id'), 'booking_histories', ['id'], unique=False)

def downgrade() -> None:
    op.drop_table('booking_histories')
    op.drop_table('seat_locks')
    op.drop_table('booked_seats')
    op.drop_index(op.f('ix_bookings_booking_reference'), table_name='bookings')
    op.drop_table('bookings')
