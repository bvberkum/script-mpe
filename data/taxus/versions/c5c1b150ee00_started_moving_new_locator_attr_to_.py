"""Started moving new locator attr to resource

Revision ID: c5c1b150ee00
Revises: 27f684150e68
Create Date: 2017-08-13 21:11:49.458503

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5c1b150ee00'
down_revision = '27f684150e68'
branch_labels = None
depends_on = None


def upgrade():
    # Add table for remote cached resources
    op.create_table('rcres',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id'], ['res.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Drop sqlalchemy migrations tables
    op.drop_table('migrations_lock')
    op.drop_table('migrations')

    # Prepare Status table for HTTP code import
    op.drop_column('status', 'http_code')
    op.add_column('status', sa.Column('code', sa.Integer(), nullable=False))
    op.add_column('status', sa.Column('protocol', sa.VARCHAR(length=16), nullable=False))

    # Drop local CardMixin fields for Bookmark, and alter to inherit from Resource
    op.create_foreign_key(None, 'bm', 'res', ['id'], ['id'])

    op.drop_index('ix_bm_date_added', table_name='bm')
    op.drop_index('ix_bm_date_updated', table_name='bm')
    op.drop_index('ix_bm_deleted', table_name='bm')
    op.drop_column('bm', 'deleted')
    op.drop_column('bm', 'date_updated')
    op.drop_column('bm', 'date_deleted')
    op.drop_column('bm', 'date_added')

    # Adding SHA1 checksum relation for locators
    op.add_column('ids_lctr', sa.Column('ref_sha1_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'ids_lctr', 'chks_sha1', ['ref_sha1_id'], ['id'])


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'ids_lctr', type_='foreignkey')
    op.drop_column('ids_lctr', 'ref_sha1_id')
    op.add_column('bm', sa.Column('date_added', sa.DATETIME(), nullable=False))
    op.add_column('bm', sa.Column('date_deleted', sa.DATETIME(), nullable=True))
    op.add_column('bm', sa.Column('date_updated', sa.DATETIME(), nullable=False))
    op.add_column('bm', sa.Column('deleted', sa.BOOLEAN(), nullable=True))
    op.drop_constraint(None, 'bm', type_='foreignkey')
    op.create_index('ix_bm_deleted', 'bm', ['deleted'], unique=False)
    op.create_index('ix_bm_date_updated', 'bm', ['date_updated'], unique=False)
    op.create_index('ix_bm_date_added', 'bm', ['date_added'], unique=False)
    op.create_table('sqlite_sequence',
    sa.Column('name', sa.NullType(), nullable=True),
    sa.Column('seq', sa.NullType(), nullable=True)
    )
    op.create_table('migrations',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=255), nullable=True),
    sa.Column('batch', sa.INTEGER(), nullable=True),
    sa.Column('migration_time', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('migrations_lock',
    sa.Column('is_locked', sa.INTEGER(), nullable=True)
    )
    op.drop_table('rcres')
    # ### end Alembic commands ###
