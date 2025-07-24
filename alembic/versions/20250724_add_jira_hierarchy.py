"""Add Jira hierarchy fields to apontamento table

Revision ID: 20250724_jira_hierarchy
Revises: 696b6a4d1edc
Create Date: 2025-07-24 18:32:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250724_jira_hierarchy'
down_revision = '696b6a4d1edc'
branch_labels = None
depends_on = None


def upgrade():
    """Add hierarchy fields to apontamento table"""
    
    # Adicionar campos para hierarquia Jira
    op.add_column('apontamento', sa.Column('jira_parent_key', sa.String(50), nullable=True))
    op.add_column('apontamento', sa.Column('jira_issue_type', sa.String(50), nullable=True))
    op.add_column('apontamento', sa.Column('nome_subtarefa', sa.String(200), nullable=True))
    op.add_column('apontamento', sa.Column('projeto_pai_id', sa.Integer, nullable=True))
    op.add_column('apontamento', sa.Column('nome_projeto_pai', sa.String(200), nullable=True))
    
    # Adicionar foreign key para projeto pai
    op.create_foreign_key(
        'fk_apontamento_projeto_pai',
        'apontamento', 'projeto',
        ['projeto_pai_id'], ['id'],
        onupdate='CASCADE',
        ondelete='SET NULL'
    )
    
    # Adicionar índices para performance
    op.create_index('idx_apontamento_jira_parent_key', 'apontamento', ['jira_parent_key'])
    op.create_index('idx_apontamento_jira_issue_type', 'apontamento', ['jira_issue_type'])
    op.create_index('idx_apontamento_projeto_pai_id', 'apontamento', ['projeto_pai_id'])


def downgrade():
    """Remove hierarchy fields from apontamento table"""
    
    # Remover índices
    op.drop_index('idx_apontamento_projeto_pai_id', 'apontamento')
    op.drop_index('idx_apontamento_jira_issue_type', 'apontamento')
    op.drop_index('idx_apontamento_jira_parent_key', 'apontamento')
    
    # Remover foreign key
    op.drop_constraint('fk_apontamento_projeto_pai', 'apontamento', type_='foreignkey')
    
    # Remover colunas
    op.drop_column('apontamento', 'nome_projeto_pai')
    op.drop_column('apontamento', 'projeto_pai_id')
    op.drop_column('apontamento', 'nome_subtarefa')
    op.drop_column('apontamento', 'jira_issue_type')
    op.drop_column('apontamento', 'jira_parent_key')
