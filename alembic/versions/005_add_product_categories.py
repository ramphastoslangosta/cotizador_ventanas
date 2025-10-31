"""add product categories

Revision ID: 005_add_product_categories
Revises: 004_glass_pricing
Create Date: 2025-10-30

ARCH-20251029-002: Replace window-only constraint with ProductCategory system
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '005_add_product_categories'
down_revision = '004_glass_pricing'
branch_labels = None
depends_on = None

def upgrade():
    # Step 1: Add product_category column with default 'window' (backward compatible)
    op.add_column('app_products', sa.Column(
        'product_category',
        sa.String(50),
        nullable=False,
        server_default='window'
    ))

    # Step 2: Make window_type nullable (non-window products don't need it)
    op.alter_column('app_products', 'window_type',
                    existing_type=sa.String(50),
                    nullable=True)

    # Step 3: Add door_type column (nullable, only for doors)
    op.add_column('app_products', sa.Column(
        'door_type',
        sa.String(50),
        nullable=True
    ))

    # Step 4: Add check constraint for valid product categories
    op.create_check_constraint(
        'check_product_category',
        'app_products',
        "product_category IN ('window', 'door', 'louver_door', 'railing', 'curtain_wall', 'skylight', 'canopy', 'standalone_material')"
    )

    # Step 5: Add conditional constraint: windows must have window_type
    op.create_check_constraint(
        'check_window_type_for_windows',
        'app_products',
        "(product_category = 'window' AND window_type IS NOT NULL) OR (product_category != 'window')"
    )

    # Step 6: Add conditional constraint: doors must have door_type
    op.create_check_constraint(
        'check_door_type_for_doors',
        'app_products',
        "(product_category IN ('door', 'louver_door') AND door_type IS NOT NULL) OR (product_category NOT IN ('door', 'louver_door'))"
    )

    # Step 7: Add index for category filtering (performance)
    op.create_index('idx_app_products_category', 'app_products', ['product_category'])

def downgrade():
    # Reverse migration (for rollback)
    op.drop_index('idx_app_products_category', table_name='app_products')
    op.drop_constraint('check_door_type_for_doors', 'app_products')
    op.drop_constraint('check_window_type_for_windows', 'app_products')
    op.drop_constraint('check_product_category', 'app_products')
    op.drop_column('app_products', 'door_type')
    op.alter_column('app_products', 'window_type',
                    existing_type=sa.String(50),
                    nullable=False)
    op.drop_column('app_products', 'product_category')
