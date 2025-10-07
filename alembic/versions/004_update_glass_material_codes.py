"""Update glass material codes for database-driven pricing

Revision ID: 004_glass_pricing
Revises: 003_add_tenant_id_catalogs
Create Date: 2025-10-07 10:00:00

This migration updates existing glass materials in app_materials table
to use standardized material codes for database-driven pricing.

Old glass materials (if they exist) will be updated with correct codes.
If no glass materials exist, this migration does nothing (sample data
initialization will create them).

Standardized codes:
- VID-CLARO-4: Vidrio Claro 4mm ($85.00/m²)
- VID-CLARO-6: Vidrio Claro 6mm ($120.00/m²)
- VID-BRONCE-4: Vidrio Bronce 4mm ($95.00/m²)
- VID-BRONCE-6: Vidrio Bronce 6mm ($135.00/m²)
- VID-REFLECTIVO-6: Vidrio Reflectivo 6mm ($180.00/m²)
- VID-LAMINADO-6: Vidrio Laminado 6mm ($220.00/m²)
- VID-TEMP-6: Vidrio Templado 6mm ($195.00/m²)
"""
from alembic import op
import sqlalchemy as sa
from decimal import Decimal

# revision identifiers, used by Alembic
revision = '004_glass_pricing'
down_revision = '003_add_tenant_id_catalogs'  # Adjust to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """
    Update existing glass materials with standardized codes
    """
    # Glass material mapping: (old_name_pattern, new_code, new_name, cost)
    glass_updates = [
        ('Vidrio Flotado 6mm', 'VID-CLARO-6', 'Vidrio Claro 6mm', Decimal('120.00')),
        ('Vidrio Claro 4mm', 'VID-CLARO-4', 'Vidrio Claro 4mm', Decimal('85.00')),
        ('Vidrio Claro 6mm', 'VID-CLARO-6', 'Vidrio Claro 6mm', Decimal('120.00')),
        ('Vidrio Bronce 4mm', 'VID-BRONCE-4', 'Vidrio Bronce 4mm', Decimal('95.00')),
        ('Vidrio Bronce 6mm', 'VID-BRONCE-6', 'Vidrio Bronce 6mm', Decimal('135.00')),
        ('Vidrio Templado 6mm', 'VID-TEMP-6', 'Vidrio Templado 6mm', Decimal('195.00')),
        ('Vidrio Laminado 6mm', 'VID-LAMINADO-6', 'Vidrio Laminado 6mm', Decimal('220.00')),
        ('Vidrio Reflectivo Bronze 6mm', 'VID-REFLECTIVO-6', 'Vidrio Reflectivo 6mm', Decimal('180.00')),
        ('Vidrio Reflectivo 6mm', 'VID-REFLECTIVO-6', 'Vidrio Reflectivo 6mm', Decimal('180.00')),
    ]

    # Use raw SQL for updates
    connection = op.get_bind()

    print("🔄 Updating glass material codes...")

    for old_pattern, new_code, new_name, cost in glass_updates:
        # Check if material exists
        result = connection.execute(
            sa.text(
                "SELECT id FROM app_materials WHERE name LIKE :pattern AND (category = 'Vidrio' OR category IS NULL) LIMIT 1"
            ),
            {"pattern": f"%{old_pattern}%"}
        ).fetchone()

        if result:
            # Update existing material
            connection.execute(
                sa.text(
                    """
                    UPDATE app_materials
                    SET code = :new_code,
                        name = :new_name,
                        cost_per_unit = :cost,
                        category = 'Vidrio',
                        updated_at = NOW()
                    WHERE name LIKE :pattern AND (category = 'Vidrio' OR category IS NULL)
                    """
                ),
                {
                    "new_code": new_code,
                    "new_name": new_name,
                    "cost": str(cost),
                    "pattern": f"%{old_pattern}%"
                }
            )
            print(f"  ✓ Updated glass material: {new_code} ({new_name})")
        else:
            # Material doesn't exist - will be created by initialize_sample_data()
            print(f"  ⚠️  Glass material not found: {old_pattern} (will be created on next startup)")

    print("✅ Glass material codes migration complete")


def downgrade():
    """
    Revert glass material code updates

    Note: Downgrade not fully implemented as original codes were inconsistent.
    If you need to rollback, restore from database backup.
    """
    print("⚠️  Downgrade not implemented - glass codes will remain updated")
    print("   To rollback, restore from database backup taken before migration")
    pass
