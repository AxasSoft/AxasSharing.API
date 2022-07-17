"""empty message

Revision ID: 78f86778d017
Revises: 98e77b35cf26
Create Date: 2022-07-16 01:56:12.786452

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78f86778d017'
down_revision = '98e77b35cf26'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('flats',
    sa.Column('room_count', sa.Integer(), nullable=False),
    sa.Column('has_balcony', sa.Boolean(), nullable=False),
    sa.Column('has_loggia', sa.Boolean(), nullable=False),
    sa.Column('address', sa.String(), nullable=False),
    sa.Column('lat', sa.Float(), nullable=False),
    sa.Column('lon', sa.Float(), nullable=False),
    sa.Column('area', sa.Float(), nullable=False),
    sa.Column('price_short', sa.Integer(), nullable=True),
    sa.Column('price_long', sa.Integer(), nullable=True),
    sa.Column('children', sa.Boolean(), nullable=False),
    sa.Column('animals', sa.Boolean(), nullable=False),
    sa.Column('washing_machine', sa.Boolean(), nullable=False),
    sa.Column('fridge', sa.Boolean(), nullable=False),
    sa.Column('tv', sa.Boolean(), nullable=False),
    sa.Column('dishwasher', sa.Boolean(), nullable=False),
    sa.Column('air_conditioner', sa.Boolean(), nullable=False),
    sa.Column('smoking', sa.Boolean(), nullable=False),
    sa.Column('noise', sa.Boolean(), nullable=False),
    sa.Column('party', sa.Boolean(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('guest_count', sa.Integer(), nullable=False),
    sa.Column('bed_count', sa.Integer(), nullable=False),
    sa.Column('restroom_count', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('flat_picture',
    sa.Column('flat_id', sa.Integer(), nullable=False),
    sa.Column('link', sa.String(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['flat_id'], ['flats.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('flat_picture')
    op.drop_table('flats')
    # ### end Alembic commands ###
