"""create_interpretation_links_table

Revision ID: 97f81a11bea9
Revises: 
Create Date: 2025-10-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '97f81a11bea9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create interpretation_links table with fact-pattern awareness."""
    
    # Create interpretation_links table
    op.create_table(
        'interpretation_links',
        
        # Primary Key
        sa.Column('id', sa.String(255), primary_key=True),
        
        # Foreign Keys
        sa.Column('statute_id', sa.String(255), nullable=False),
        sa.Column('case_id', sa.String(255), nullable=False),
        
        # Denormalized Statute Details
        sa.Column('statute_name', sa.String(500), nullable=False),
        sa.Column('statute_section', sa.String(50), nullable=False),
        sa.Column('statute_text', sa.Text),
        
        # Denormalized Case Details
        sa.Column('case_name', sa.String(500), nullable=False),
        sa.Column('case_citation', sa.String(100), nullable=False),
        sa.Column('case_para_no', sa.Integer, nullable=False),
        sa.Column('case_text', sa.Text),
        sa.Column('court', sa.String(50)),
        sa.Column('year', sa.Integer),
        
        # Interpretation Metadata
        sa.Column('interpretation_type', sa.String(50), nullable=False),
        sa.Column('authority', sa.String(50), nullable=False),
        sa.Column('holding', sa.Text, nullable=False),
        
        # FACT PATTERN AWARENESS (Core Innovation)
        sa.Column('fact_pattern_tags', postgresql.ARRAY(sa.String)),
        sa.Column('case_facts_summary', sa.Text),
        sa.Column('applicability_score', sa.Float),
        sa.Column('cause_of_action', sa.String(100)),
        sa.Column('sub_issues', postgresql.ARRAY(sa.String)),
        
        # Extraction Metadata
        sa.Column('extraction_method', sa.String(50)),
        sa.Column('confidence', sa.Float),
        
        # Verification Status
        sa.Column('verified', sa.Boolean, default=False),
        sa.Column('verified_by', sa.String(100)),
        sa.Column('verified_at', sa.DateTime),
        
        # Retrieval Weights
        sa.Column('boost_factor', sa.Float, nullable=False, default=2.0),
        
        # Audit Trail
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        
        # Constraints
        sa.CheckConstraint(
            "interpretation_type IN ('NARROW', 'BROAD', 'CLARIFY', 'PURPOSIVE', 'LITERAL', 'APPLY')",
            name='check_interpretation_type'
        ),
        sa.CheckConstraint(
            "authority IN ('BINDING', 'PERSUASIVE', 'OBITER', 'DISSENT')",
            name='check_authority'
        ),
        sa.CheckConstraint(
            "extraction_method IN ('RULE_BASED', 'LLM_ASSISTED', 'MANUAL')",
            name='check_extraction_method'
        ),
        sa.CheckConstraint(
            'confidence >= 0 AND confidence <= 1',
            name='check_confidence_range'
        ),
        sa.CheckConstraint(
            'applicability_score >= 0 AND applicability_score <= 1',
            name='check_applicability_range'
        ),
        sa.CheckConstraint(
            'boost_factor >= 1.0 AND boost_factor <= 3.0',
            name='check_boost_factor_range'
        ),
        sa.UniqueConstraint('statute_id', 'case_id', name='unique_statute_case_pair')
    )
    
    # Create Indexes
    op.create_index(
        'idx_statute_lookup',
        'interpretation_links',
        ['statute_id'],
        postgresql_where=sa.text('verified = true')
    )
    
    op.create_index(
        'idx_case_lookup',
        'interpretation_links',
        ['case_id']
    )
    
    op.create_index(
        'idx_verified',
        'interpretation_links',
        ['verified'],
        postgresql_where=sa.text('verified = true')
    )
    
    op.create_index(
        'idx_authority',
        'interpretation_links',
        ['authority']
    )
    
    op.create_index(
        'idx_cause_of_action',
        'interpretation_links',
        ['cause_of_action']
    )
    
    op.create_index(
        'idx_fact_tags',
        'interpretation_links',
        ['fact_pattern_tags'],
        postgresql_using='gin'
    )
    
    op.create_index(
        'idx_applicability',
        'interpretation_links',
        ['applicability_score']
    )
    
    op.create_index(
        'idx_statute_verified_authority',
        'interpretation_links',
        ['statute_id', 'verified', 'authority'],
        postgresql_where=sa.text("verified = true AND authority IN ('BINDING', 'PERSUASIVE')")
    )
    
    op.create_index(
        'idx_extraction_method',
        'interpretation_links',
        ['extraction_method']
    )
    
    op.create_index(
        'idx_low_confidence',
        'interpretation_links',
        ['confidence'],
        postgresql_where=sa.text('confidence < 0.7 AND verified = false')
    )
    
    # Create trigger for auto-updating updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_interpretation_links_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trigger_update_interpretation_links_updated_at
            BEFORE UPDATE ON interpretation_links
            FOR EACH ROW
            EXECUTE FUNCTION update_interpretation_links_updated_at();
    """)
    
    # Add comments
    op.execute("""
        COMMENT ON TABLE interpretation_links IS 
        'Links statute sections to case paragraphs where the case interprets, applies, or clarifies the statute. PRIMARY INNOVATION of the statutory interpretation RAG system.';
    """)


def downgrade():
    """Drop interpretation_links table and related objects."""
    
    # Drop trigger
    op.execute('DROP TRIGGER IF EXISTS trigger_update_interpretation_links_updated_at ON interpretation_links')
    op.execute('DROP FUNCTION IF EXISTS update_interpretation_links_updated_at()')
    
    # Drop indexes
    op.drop_index('idx_low_confidence', table_name='interpretation_links')
    op.drop_index('idx_extraction_method', table_name='interpretation_links')
    op.drop_index('idx_statute_verified_authority', table_name='interpretation_links')
    op.drop_index('idx_applicability', table_name='interpretation_links')
    op.drop_index('idx_fact_tags', table_name='interpretation_links')
    op.drop_index('idx_cause_of_action', table_name='interpretation_links')
    op.drop_index('idx_authority', table_name='interpretation_links')
    op.drop_index('idx_verified', table_name='interpretation_links')
    op.drop_index('idx_case_lookup', table_name='interpretation_links')
    op.drop_index('idx_statute_lookup', table_name='interpretation_links')
    
    # Drop table
    op.drop_table('interpretation_links')
