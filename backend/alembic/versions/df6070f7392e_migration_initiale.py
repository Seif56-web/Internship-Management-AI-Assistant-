"""Migration initiale - creation de toutes les tables

Revision ID: df6070f7392e
Revises:
Create Date: 2026-07-06 15:30:48.231293
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'df6070f7392e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('nom', sa.String(length=100), nullable=False),
        sa.Column('prenom', sa.String(length=100), nullable=False),
        sa.Column('role', sa.Enum('RH', 'Encadrant', 'Admin', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_id', 'users', ['id'])

    op.create_table('encadrants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(length=100), nullable=False),
        sa.Column('prenom', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_encadrants_id', 'encadrants', ['id'])

    op.create_table('stagiaires',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(length=100), nullable=False),
        sa.Column('prenom', sa.String(length=100), nullable=False),
        sa.Column('date_naissance', sa.Date(), nullable=False),
        sa.Column('cin', sa.String(length=8), nullable=False),
        sa.Column('country_code', sa.String(length=5), nullable=False, server_default='+216'),
        sa.Column('telephone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('ecole', sa.String(length=255), nullable=True),
        sa.Column('taille', sa.Integer(), nullable=True),
        sa.Column('pointure', sa.Integer(), nullable=True),
        sa.Column('date_debut_stage', sa.Date(), nullable=False),
        sa.Column('date_fin_stage', sa.Date(), nullable=False),
        sa.Column('statut', sa.Enum('EN_ATTENTE', 'EN_COURS_VALIDATION', 'VALIDE', 'REFUSE', 'ATTESTATION_GENEREE', name='statutstage'), nullable=False),
        sa.Column('encadrant_nom', sa.String(length=255), nullable=True),
        sa.Column('encadrant_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['encadrant_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.CheckConstraint("length(cin) = 8", name='ck_cin_8_chars'),
        sa.CheckConstraint('date_fin_stage > date_debut_stage', name='ck_dates_stage'),
    )
    op.create_index('ix_stagiaires_cin', 'stagiaires', ['cin'])
    op.create_index('ix_stagiaires_id', 'stagiaires', ['id'])
    op.create_index('ix_stagiaires_nom', 'stagiaires', ['nom'])

    op.create_table('rapports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stagiaire_id', sa.Integer(), nullable=False),
        sa.Column('file_pdf', sa.String(length=512), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['stagiaire_id'], ['stagiaires.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rapports_id', 'rapports', ['id'])

    op.create_table('validations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stagiaire_id', sa.Integer(), nullable=False),
        sa.Column('encadrant_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('VALIDE', 'REFUSE', name='statutvalidation'), nullable=False),
        sa.Column('commentaire', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['stagiaire_id'], ['stagiaires.id'], ),
        sa.ForeignKeyConstraint(['encadrant_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_validations_id', 'validations', ['id'])

    op.create_table('attestations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stagiaire_id', sa.Integer(), nullable=False),
        sa.Column('numero_attestation', sa.String(length=50), nullable=False),
        sa.Column('generated_by', sa.Integer(), nullable=False),
        sa.Column('pdf_url', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['stagiaire_id'], ['stagiaires.id'], ),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('numero_attestation'),
    )
    op.create_index('ix_attestations_id', 'attestations', ['id'])


def downgrade() -> None:
    op.drop_table('attestations')
    op.drop_table('validations')
    op.drop_table('rapports')
    op.drop_table('stagiaires')
    op.drop_table('encadrants')
    op.drop_table('users')

    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='statutstage').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='statutvalidation').drop(op.get_bind(), checkfirst=False)
