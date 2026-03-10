"""add dashboard shares table

Revision ID: 3f4a5b6c7d8e
Revises: 2b2ca9ae2f76
Create Date: 2026-03-09 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3f4a5b6c7d8e'
down_revision = '2b2ca9ae2f76'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'dashboard_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('share_token', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['job_id'], ['analysis_jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
    )

    # Create index for efficient lookups
    op.create_index('ix_dashboard_shares_job_id', 'dashboard_shares', ['job_id'])
    op.create_index('ix_dashboard_shares_org_id', 'dashboard_shares', ['org_id'])


def downgrade():
    op.drop_index('ix_dashboard_shares_org_id')
    op.drop_index('ix_dashboard_shares_job_id')
    op.drop_table('dashboard_shares')
