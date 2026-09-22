"""human review and handoff

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-21 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Review Queue Items
    op.create_table('reviewer_queue_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('assigned_reviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('previous_reviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reassignment_reason', sa.Text(), nullable=True),
        sa.Column('priority_bucket', sa.String(), nullable=False, default='DEFAULT'),
        sa.Column('entered_queue_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['assigned_reviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['previous_reviewer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_id')
    )
    op.create_index('ix_review_queue_status_priority', 'reviewer_queue_items', ['status', 'priority_bucket', 'entered_queue_at'], unique=False)
    op.create_index('ix_review_queue_unassigned', 'reviewer_queue_items', ['entered_queue_at'], unique=False, postgresql_where=sa.text("status = 'PENDING_ASSIGNMENT'"))

    # Review Decisions
    op.create_table('review_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision_type', sa.String(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('case_version', sa.Integer(), nullable=False),
        sa.Column('correlation_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_review_decisions_case', 'review_decisions', ['case_id'], unique=False)

    # Reviewer Notes
    op.create_table('reviewer_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('superseded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['superseded_by'], ['reviewer_notes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reviewer_notes_case', 'reviewer_notes', ['case_id'], unique=False)
    op.create_unique_constraint('uq_reviewer_notes_active', 'reviewer_notes', ['case_id'])

    # Draft Edit Versions
    op.create_table('draft_edit_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('editor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_content_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('edited_content_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('edit_rationale', sa.Text(), nullable=True),
        sa.Column('content_origin', sa.String(), nullable=False),
        sa.Column('correlation_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['draft_id'], ['ai_drafts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['editor_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_draft_edit_versions_draft', 'draft_edit_versions', ['draft_id'], unique=False)

    # Escalation Records
    op.create_table('escalation_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('escalated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('correlation_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['escalated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_escalation_records_case', 'escalation_records', ['case_id'], unique=False)

    # Recipients
    op.create_table('recipients',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('recipient_type', sa.String(), nullable=False),
        sa.Column('config_json', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Referral Packages
    op.create_table('referral_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('prepared_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('evidence_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('superseded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('correlation_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prepared_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['superseded_by'], ['referral_packages.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_id', 'version', name='uq_referral_packages_case_version')
    )
    op.create_index('ix_referral_packages_case', 'referral_packages', ['case_id'], unique=False)

    # Handoffs
    op.create_table('handoffs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('referral_package_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('idempotency_key', sa.String(), nullable=False),
        sa.Column('sent_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivery_reference', sa.String(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledgement_reference', sa.String(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_attempts', sa.Integer(), nullable=False, default=3),
        sa.Column('correlation_id', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipient_id'], ['recipients.id'], ),
        sa.ForeignKeyConstraint(['referral_package_id'], ['referral_packages.id'], ),
        sa.ForeignKeyConstraint(['sent_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key')
    )
    op.create_index('ix_handoffs_case', 'handoffs', ['case_id'], unique=False)


def downgrade() -> None:
    op.drop_table('handoffs')
    op.drop_table('referral_packages')
    op.drop_table('recipients')
    op.drop_table('escalation_records')
    op.drop_table('draft_edit_versions')
    op.drop_table('reviewer_notes')
    op.drop_table('review_decisions')
    op.drop_table('reviewer_queue_items')
