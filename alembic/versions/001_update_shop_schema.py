"""Update shop schema to match models

Revision ID: 001
Revises: 
Create Date: 2025-07-27 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove old columns that don't exist in new model
    op.drop_column('shops', 'services')
    op.drop_column('shops', 'pricing')
    op.drop_column('shops', 'hours')
    op.drop_column('shops', 'location')
    op.drop_column('shops', 'description')
    
    # Add new columns from the model
    op.add_column('shops', sa.Column('address', sa.String(), nullable=False, server_default=''))
    op.add_column('shops', sa.Column('phone', sa.String(), nullable=False, server_default=''))
    op.add_column('shops', sa.Column('logo_url', sa.String(), nullable=True))
    op.add_column('shops', sa.Column('greeting_message', sa.Text(), server_default="Hi! How can I help you with your auto detailing needs?"))
    op.add_column('shops', sa.Column('primary_color', sa.String(), server_default="#007bff"))
    op.add_column('shops', sa.Column('secondary_color', sa.String(), server_default="#6c757d"))
    op.add_column('shops', sa.Column('calendar_type', sa.String(), nullable=True))
    op.add_column('shops', sa.Column('calendar_config', sa.JSON(), nullable=True))
    op.add_column('shops', sa.Column('booking_rules', sa.JSON(), nullable=True))
    op.add_column('shops', sa.Column('stripe_customer_id', sa.String(), nullable=True))
    op.add_column('shops', sa.Column('subscription_status', sa.String(), server_default="trial"))
    op.add_column('shops', sa.Column('plan_id', sa.Integer(), nullable=True))
    op.add_column('shops', sa.Column('public_api_key', sa.String(), nullable=False, server_default=''))
    op.add_column('shops', sa.Column('private_api_key', sa.String(), nullable=False, server_default=''))
    op.add_column('shops', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true')))
    
    # Modify name column if needed (ensure proper length)
    op.alter_column('shops', 'name', type_=sa.String(100), nullable=False)
    
    # Add foreign key constraints
    op.create_foreign_key('fk_shops_plan_id', 'shops', 'plans', ['plan_id'], ['id'])
    
    # Add unique constraints for API keys
    op.create_unique_constraint('uq_shops_public_api_key', 'shops', ['public_api_key'])
    op.create_unique_constraint('uq_shops_private_api_key', 'shops', ['private_api_key'])
    
    # Remove server defaults after adding columns
    op.alter_column('shops', 'address', server_default=None)
    op.alter_column('shops', 'phone', server_default=None)
    op.alter_column('shops', 'public_api_key', server_default=None)
    op.alter_column('shops', 'private_api_key', server_default=None)


def downgrade() -> None:
    # Remove new columns
    op.drop_constraint('uq_shops_private_api_key', 'shops', type_='unique')
    op.drop_constraint('uq_shops_public_api_key', 'shops', type_='unique')
    op.drop_constraint('fk_shops_plan_id', 'shops', type_='foreignkey')
    
    op.drop_column('shops', 'is_active')
    op.drop_column('shops', 'private_api_key')
    op.drop_column('shops', 'public_api_key')
    op.drop_column('shops', 'plan_id')
    op.drop_column('shops', 'subscription_status')
    op.drop_column('shops', 'stripe_customer_id')
    op.drop_column('shops', 'booking_rules')
    op.drop_column('shops', 'calendar_config')
    op.drop_column('shops', 'calendar_type')
    op.drop_column('shops', 'secondary_color')
    op.drop_column('shops', 'primary_color')
    op.drop_column('shops', 'greeting_message')
    op.drop_column('shops', 'logo_url')
    op.drop_column('shops', 'phone')
    op.drop_column('shops', 'address')
    
    # Restore old columns
    op.add_column('shops', sa.Column('description', sa.TEXT(), nullable=True))
    op.add_column('shops', sa.Column('location', sa.VARCHAR(length=255), nullable=True))
    op.add_column('shops', sa.Column('hours', sa.VARCHAR(length=255), nullable=True))
    op.add_column('shops', sa.Column('pricing', sa.TEXT(), nullable=True))
    op.add_column('shops', sa.Column('services', sa.TEXT(), nullable=True))