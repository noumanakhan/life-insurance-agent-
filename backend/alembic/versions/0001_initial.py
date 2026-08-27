"""Initial schema — all tables + pgvector extension

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import pgvector

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # sessions
    op.create_table(
        "sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # messages
    op.create_table(
        "messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # client_profiles
    op.create_table(
        "client_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id"), nullable=False, unique=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("annual_income", sa.Numeric(15, 2), nullable=True),
        sa.Column("dependents", sa.Integer(), nullable=True),
        sa.Column("total_debt", sa.Numeric(15, 2), nullable=True),
        sa.Column("available_savings", sa.Numeric(15, 2), nullable=True),
        sa.Column("existing_life_insurance", sa.Numeric(15, 2), nullable=True),
        sa.Column("income_replacement_years", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # policy_documents
    op.create_table(
        "policy_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("insurer_name", sa.String(255), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # policy_chunks — uses pgvector VECTOR type
    op.create_table(
        "policy_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("policy_documents.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(768), nullable=True),
    )

    # ivfflat index for cosine similarity search
    op.execute(
        "CREATE INDEX ON policy_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
    )

    # insurance_products
    op.create_table(
        "insurance_products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("insurer_name", sa.String(255), nullable=True),
        sa.Column("product_name", sa.String(255), nullable=True),
        sa.Column("product_type", sa.String(100), nullable=True),
        sa.Column("min_coverage", sa.Numeric(15, 2), nullable=True),
        sa.Column("max_coverage", sa.Numeric(15, 2), nullable=True),
        sa.Column("term_years", sa.Integer(), nullable=True),
        sa.Column("premium_estimate", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("insurance_products")
    op.execute("DROP INDEX IF EXISTS policy_chunks_embedding_idx;")
    op.drop_table("policy_chunks")
    op.drop_table("policy_documents")
    op.drop_table("client_profiles")
    op.drop_table("messages")
    op.drop_table("sessions")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector;")
