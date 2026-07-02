"""create movie service tables

Revision ID: b2c3d4e5f6g7
Revises: 
Create Date: 2026-06-30 20:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create movies table
    op.create_table(
        'movies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('genre', sa.String(length=100), nullable=True),
        sa.Column('language', sa.String(length=100), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('release_date', sa.Date(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('poster_url', sa.String(length=512), nullable=True),
        sa.Column('trailer_url', sa.String(length=512), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_movies_title'), 'movies', ['title'], unique=True)

    # 2. Create theatres table
    op.create_table(
        'theatres',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_theatres_city'), 'theatres', ['city'], unique=False)

    # 3. Create screens table
    op.create_table(
        'screens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('theatre_id', sa.String(length=36), nullable=False),
        sa.Column('screen_name', sa.String(length=100), nullable=False),
        sa.Column('total_seats', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['theatre_id'], ['theatres.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Create shows table
    op.create_table(
        'shows',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('movie_id', sa.String(length=36), nullable=False),
        sa.Column('screen_id', sa.String(length=36), nullable=False),
        sa.Column('show_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('ticket_price', sa.Float(), nullable=False),
        sa.Column('available_seats', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['movie_id'], ['movies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['screen_id'], ['screens.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('shows')
    op.drop_table('screens')
    op.drop_index(op.f('ix_theatres_city'), table_name='theatres')
    op.drop_table('theatres')
    op.drop_index(op.f('ix_movies_title'), table_name='movies')
    op.drop_table('movies')
