"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum_exists(conn, name):
    result = conn.execute(sa.text(
        "SELECT 1 FROM pg_type WHERE typname = :name"
    ), {"name": name})
    return result.fetchone() is not None


def _table_exists(conn, name):
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = :name"
    ), {"name": name})
    return result.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()

    if not _enum_exists(conn, "userrole"):
        conn.execute(sa.text("CREATE TYPE userrole AS ENUM ('admin', 'staff')"))
    if not _enum_exists(conn, "finishtype"):
        conn.execute(sa.text("CREATE TYPE finishtype AS ENUM ('matte', 'gloss', 'satin', 'textured', 'woodgrain', 'metallic', 'other')"))
    if not _enum_exists(conn, "uploadstatus"):
        conn.execute(sa.text("CREATE TYPE uploadstatus AS ENUM ('pending', 'processing', 'completed', 'failed')"))
    if not _enum_exists(conn, "feedbacktype"):
        conn.execute(sa.text("CREATE TYPE feedbacktype AS ENUM ('confirmed', 'rejected', 'corrected')"))

    if not _table_exists(conn, "users"):
        op.create_table("users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("full_name", sa.String(255), nullable=False),
            sa.Column("hashed_password", sa.String(255), nullable=False),
            sa.Column("role", sa.Enum("admin", "staff", name="userrole", create_type=False), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_users_id", "users", ["id"])
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if not _table_exists(conn, "companies"):
        op.create_table("companies",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("country", sa.String(100), nullable=True),
            sa.Column("website", sa.String(500), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
        op.create_index("ix_companies_id", "companies", ["id"])

    if not _table_exists(conn, "catalogs"):
        op.create_table("catalogs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("year", sa.Integer(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("company_id", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_catalogs_id", "catalogs", ["id"])

    if not _table_exists(conn, "products"):
        op.create_table("products",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(100), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("name_ar", sa.String(255), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("catalog_id", sa.Integer(), nullable=False),
            sa.Column("color_hex", sa.String(7), nullable=True),
            sa.Column("color_lab_l", sa.Float(), nullable=True),
            sa.Column("color_lab_a", sa.Float(), nullable=True),
            sa.Column("color_lab_b", sa.Float(), nullable=True),
            sa.Column("color_rgb_r", sa.Integer(), nullable=True),
            sa.Column("color_rgb_g", sa.Integer(), nullable=True),
            sa.Column("color_rgb_b", sa.Integer(), nullable=True),
            sa.Column("finish", sa.Enum("matte","gloss","satin","textured","woodgrain","metallic","other", name="finishtype", create_type=False), nullable=True),
            sa.Column("thickness_mm", sa.Float(), nullable=True),
            sa.Column("width_mm", sa.Float(), nullable=True),
            sa.Column("length_mm", sa.Float(), nullable=True),
            sa.Column("reference_image_key", sa.String(500), nullable=True),
            sa.Column("qdrant_point_id", sa.String(100), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["catalog_id"], ["catalogs.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_products_id", "products", ["id"])
        op.create_index("ix_products_code", "products", ["code"])
        op.create_index("ix_products_qdrant_point_id", "products", ["qdrant_point_id"])

    if not _table_exists(conn, "image_uploads"):
        op.create_table("image_uploads",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("original_filename", sa.String(500), nullable=False),
            sa.Column("storage_key", sa.String(500), nullable=False),
            sa.Column("processed_key", sa.String(500), nullable=True),
            sa.Column("file_size_bytes", sa.Integer(), nullable=True),
            sa.Column("mime_type", sa.String(100), nullable=True),
            sa.Column("width_px", sa.Integer(), nullable=True),
            sa.Column("height_px", sa.Integer(), nullable=True),
            sa.Column("status", sa.Enum("pending","processing","completed","failed", name="uploadstatus", create_type=False), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("uploaded_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("processed_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_image_uploads_id", "image_uploads", ["id"])

    if not _table_exists(conn, "match_results"):
        op.create_table("match_results",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("upload_id", sa.Integer(), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("rank", sa.Integer(), nullable=False),
            sa.Column("confidence_score", sa.Float(), nullable=False),
            sa.Column("vector_distance", sa.Float(), nullable=True),
            sa.Column("color_delta_e", sa.Float(), nullable=True),
            sa.Column("score_breakdown", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["upload_id"], ["image_uploads.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_match_results_id", "match_results", ["id"])

    if not _table_exists(conn, "feedbacks"):
        op.create_table("feedbacks",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("match_result_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("product_id", sa.Integer(), nullable=True),
            sa.Column("feedback_type", sa.Enum("confirmed","rejected","corrected", name="feedbacktype", create_type=False), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["match_result_id"], ["match_results.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_feedbacks_id", "feedbacks", ["id"])


def downgrade() -> None:
    op.drop_table("feedbacks")
    op.drop_table("match_results")
    op.drop_table("image_uploads")
    op.drop_table("products")
    op.drop_table("catalogs")
    op.drop_table("companies")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS feedbacktype")
    op.execute("DROP TYPE IF EXISTS uploadstatus")
    op.execute("DROP TYPE IF EXISTS finishtype")
    op.execute("DROP TYPE IF EXISTS userrole")
