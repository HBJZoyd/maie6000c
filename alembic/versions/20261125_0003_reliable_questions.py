"""Add fenced job attempts, submission idempotency and immutable answer snapshots."""

import sqlalchemy as sa
from alembic import op

revision = "20261125_0003"
down_revision = "20261023_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("cases", sa.Column("answer_payload", sa.JSON(), nullable=True))
    op.add_column("cases", sa.Column("idempotency_key", sa.String(128), nullable=True))
    op.create_index("uq_cases_idempotency_key", "cases", ["idempotency_key"], unique=True)
    op.add_column("jobs", sa.Column("generation", sa.Integer(), server_default="0", nullable=False))
    op.add_column("jobs", sa.Column("claim_token", sa.String(36), nullable=True))
    op.add_column("jobs", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_jobs_pending_schedule", "jobs", ["status", "next_run_at", "created_at"])
    op.create_table(
        "job_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.UniqueConstraint("job_id", "generation"),
    )
    op.create_index("ix_job_attempts_job_id", "job_attempts", ["job_id"])


def downgrade():
    op.drop_table("job_attempts")
    op.drop_index("ix_jobs_pending_schedule", table_name="jobs")
    for name in ("next_run_at", "heartbeat_at", "claim_token", "generation"):
        op.drop_column("jobs", name)
    op.drop_index("uq_cases_idempotency_key", table_name="cases")
    op.drop_column("cases", "idempotency_key")
    op.drop_column("cases", "answer_payload")
