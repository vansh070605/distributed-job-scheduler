"""initial

Revision ID: 000000000000
Revises: 
Create Date: 2026-07-02 12:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '000000000000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Organizations
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # 3. Projects
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'slug', name='uq_projects_org_slug')
    )
    op.create_index(op.f('ix_projects_slug'), 'projects', ['slug'], unique=False)

    # 4. Retry Policies
    op.create_table(
        'retrypolicies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('strategy', sa.String(length=50), nullable=False, server_default='fixed'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('base_delay', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('backoff_factor', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Queues
    op.create_table(
        'queues',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('concurrency', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('is_paused', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('retry_policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['retry_policy_id'], ['retrypolicies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='uq_queues_project_name')
    )
    op.create_index(op.f('ix_queues_name'), 'queues', ['name'], unique=False)

    # 6. Jobs
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('queue_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('priority_override', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('cron_expression', sa.String(length=255), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('last_worker_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['queue_id'], ['queues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'idempotency_key', name='uq_projects_idempotency')
    )
    op.create_index(op.f('ix_jobs_name'), 'jobs', ['name'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
    op.create_index(op.f('ix_jobs_next_run_at'), 'jobs', ['next_run_at'], unique=False)
    op.create_index(
        'idx_jobs_claim',
        'jobs',
        ['status', 'queue_id', 'priority_override', 'created_at'],
        unique=False
    )

    # 7. Job Executions
    op.create_table(
        'jobexecutions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('worker_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='running'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobexecutions_job_id'), 'jobexecutions', ['job_id'], unique=False)

    # 8. Job Logs
    op.create_table(
        'joblogs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('level', sa.String(length=50), nullable=False, server_default='info'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['execution_id'], ['jobexecutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_joblogs_execution_id'), 'joblogs', ['execution_id'], unique=False)
    op.create_index(op.f('ix_joblogs_job_id'), 'joblogs', ['job_id'], unique=False)

    # 9. Dead Letter Queue
    op.create_table(
        'deadletterqueues',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('original_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )

    # 10. Workers
    op.create_table(
        'workers',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('concurrency', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workers_last_heartbeat'), 'workers', ['last_heartbeat'], unique=False)

    # 11. Worker Queue Assignments
    op.create_table(
        'workerqueueassignments',
        sa.Column('worker_id', sa.String(length=255), nullable=False),
        sa.Column('queue_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['queue_id'], ['queues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('worker_id', 'queue_id')
    )

    # 12. Queue Metrics
    op.create_table(
        'queuemetrics',
        sa.Column('queue_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('queued_jobs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('running_jobs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_jobs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_jobs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_execution_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('throughput_1h', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_rate', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['queue_id'], ['queues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('queue_id')
    )
    op.create_index(op.f('ix_queuemetrics_last_updated_at'), 'queuemetrics', ['last_updated_at'], unique=False)


def downgrade() -> None:
    op.drop_table('queuemetrics')
    op.drop_table('workerqueueassignments')
    op.drop_table('workers')
    op.drop_table('deadletterqueues')
    op.drop_table('joblogs')
    op.drop_table('jobexecutions')
    op.drop_table('jobs')
    op.drop_table('queues')
    op.drop_table('retrypolicies')
    op.drop_table('projects')
    op.drop_table('organizations')
    op.drop_table('users')
