"""Add multi-database support

Revision ID: add_multi_database_support
Revises: 
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_multi_database_support'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create QueryDatabaseConnection table
    op.create_table(
        'query_database_connection',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('join_columns', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['connection_id'], ['database_connection.id'], ),
        sa.ForeignKeyConstraint(['query_id'], ['query.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Remove connection_id from Query table
    op.drop_column('query', 'connection_id')

def downgrade():
    # Add back connection_id to Query table
    op.add_column('query', sa.Column('connection_id', sa.Integer(), nullable=True))
    
    # Drop QueryDatabaseConnection table
    op.drop_table('query_database_connection') 