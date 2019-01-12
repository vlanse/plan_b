"""Initial database creation

Revision ID: 1cda061a421c
Revises: 
Create Date: 2019-01-04 16:10:58.718875

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '1cda061a421c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'project',
        sa.Column('id', postgresql.INTEGER(), nullable=False, primary_key=True),
        sa.Column('name', postgresql.VARCHAR(255), nullable=False),
        sa.Column('data_source_query', postgresql.VARCHAR(1024), nullable=True)
    )

    op.create_table(
        'team',
        sa.Column('id', postgresql.INTEGER(), nullable=False, primary_key=True),
        sa.Column('name', postgresql.VARCHAR(255), nullable=False),
        sa.Column('bugfix_rate', postgresql.FLOAT(), nullable=False),
    )

    op.create_table(
        'project_history',
        sa.Column('begin_datetime', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('end_datetime', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('project_id', postgresql.INTEGER(), nullable=False),
        sa.Column('scope_complete_datetime', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('feature_complete_datetime', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('ready_to_manufacture_datetime', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('owner_team_id', postgresql.INTEGER(), nullable=False),
        sa.Column('comment', postgresql.TEXT(), nullable=True),
        sa.ForeignKeyConstraint(
            ('project_id',),
            ('project.id',),
            name='project_history_project_id_fk',
        ),
        sa.ForeignKeyConstraint(
            ('owner_team_id',),
            ('team.id',),
            name='project_history_owner_team_id_fk',
        ),
        sa.UniqueConstraint('begin_datetime', 'project_id', name='project_history_begin_datetime_project_id_idx'),
    )

    op.create_table(
        'known_bugs_count_history',
        sa.Column('begin_datetime', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('end_datetime', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('project_id', postgresql.INTEGER(), nullable=False),
        sa.Column('team_id', postgresql.INTEGER(), nullable=False),
        sa.Column('known_bugs_count', postgresql.INTEGER(), nullable=False),
        sa.ForeignKeyConstraint(
            ('project_id',),
            ('project.id',),
            name='project_history_project_id_fk',
        ),
        sa.ForeignKeyConstraint(
            ('team_id',),
            ('team.id',),
            name='project_history_owner_team_id_fk',
        ),
        sa.UniqueConstraint(
            'begin_datetime', 'project_id', 'team_id',
            name='known_bugs_count_history_begin_datetime_project_id_team_id_idx'
        ),
    )

    op.create_table(
        'person',
        sa.Column('id', postgresql.INTEGER(), nullable=False, primary_key=True),
        sa.Column('firstname', postgresql.VARCHAR(255), nullable=False),
        sa.Column('lastname', postgresql.VARCHAR(255), nullable=False),
        sa.Column('issue_tracker_name', postgresql.VARCHAR(255), nullable=False),
    )

    op.create_table(
        'person_history',
        sa.Column('begin_datetime', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('end_datetime', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('person_id', postgresql.INTEGER(), nullable=False),
        sa.Column('team_id', postgresql.INTEGER(), nullable=False),
        sa.Column('project_id', postgresql.INTEGER(), nullable=False),
        sa.Column('project_assignment', postgresql.FLOAT(), nullable=False),
        sa.Column('comment', postgresql.TEXT(), nullable=True),
        sa.ForeignKeyConstraint(
            ('person_id',),
            ('person.id',),
            name='person_history_person_id_fk',
        ),
        sa.ForeignKeyConstraint(
            ('team_id',),
            ('team.id',),
            name='person_history_team_id_fk',
        ),
        sa.ForeignKeyConstraint(
            ('project_id',),
            ('project.id',),
            name='person_history_project_id_fk',
        ),
        sa.UniqueConstraint(
            'begin_datetime', 'person_id', 'team_id', 'project_id',
            name='person_history_begin_datetime_person_id_team_id_project_id_idx'
        ),
    )

    op.create_table(
        'issue_type',
        sa.Column('id', postgresql.INTEGER(), nullable=False, primary_key=True),
        sa.Column('name', postgresql.VARCHAR(255), nullable=False),
    )

    op.create_table(
        'implementation_type',
        sa.Column('id', postgresql.INTEGER(), nullable=False, primary_key=True),
        sa.Column('name', postgresql.VARCHAR(255), nullable=False),
    )

    op.create_table(
        'issue',
        sa.Column('id', postgresql.BIGINT(), nullable=False, primary_key=True),
        sa.Column('key', postgresql.VARCHAR(64), nullable=False),
        sa.Column('url', postgresql.VARCHAR(255), nullable=False),
        sa.Column('created', postgresql.TIMESTAMP(), nullable=False),
    )

    op.create_table(
        'issue_history',
        sa.Column('begin_datetime', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('end_datetime', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('issue_id', postgresql.BIGINT(), nullable=False),
        sa.Column('type_id', postgresql.INTEGER(), nullable=False),
        sa.Column('resolved', postgresql.INTEGER(), nullable=True, default=None),
        sa.Column('due', postgresql.DATE(), nullable=True, default=None),
        sa.Column('summary', postgresql.VARCHAR(255), nullable=False),
        sa.Column('components', postgresql.VARCHAR(255), nullable=True),
        sa.Column('assignee_id', postgresql.INTEGER(), nullable=False),
        sa.Column('reporter_id', postgresql.INTEGER(), nullable=False),
        sa.Column('status', postgresql.VARCHAR(255), nullable=False),
        sa.Column('reqs_level', postgresql.FLOAT(), nullable=True),
        sa.Column('design_level', postgresql.FLOAT(), nullable=True),
        sa.Column('comment', postgresql.TEXT(), nullable=True),
        sa.ForeignKeyConstraint(
            ('issue_id',),
            ('issue.id',),
            name='issue_history_issue_id_fk',
        ),
        sa.ForeignKeyConstraint(
            ('type_id',),
            ('issue_type.id',),
            name='issue_history_type_id_fk',
        ),
        sa.ForeignKeyConstraint(
            ('assignee_id',),
            ('person.id',),
            name='issue_history_assignee_id_fk',
        ),
        sa.ForeignKeyConstraint(
            ('reporter_id',),
            ('person.id',),
            name='issue_history_reporter_id_fk',
        ),
        sa.UniqueConstraint(
            'begin_datetime', 'issue_id',
            name='issue_history_begin_datetime_issue_id_idx'
        ),
    )

    op.create_table(
        'original_estimate',
        sa.Column('begin_datetime', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('end_datetime', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('issue_id', postgresql.BIGINT(), nullable=False),
        sa.Column('team_id', postgresql.INTEGER(), nullable=False),
        sa.Column('implementation_type_id', postgresql.INTEGER(), nullable=False),
        sa.Column('estimation', postgresql.FLOAT(), nullable=True),
        sa.Column('comment', postgresql.TEXT(), nullable=True),
        sa.ForeignKeyConstraint(
            ('issue_id',),
            ('issue.id',),
            name='original_estimate_issue_id_fk',
        ),
        sa.ForeignKeyConstraint(
            ('team_id',),
            ('team.id',),
            name='original_estimate_team_id_fk',
        ),
        sa.ForeignKeyConstraint(
            ('implementation_type_id',),
            ('implementation_type.id',),
            name='original_estimate_implementation_type_id_fk',
        ),
        sa.UniqueConstraint(
            'begin_datetime', 'issue_id', 'team_id',
            name='original_estimate_begin_datetime_issue_id_team_id_idx'
        ),
    )

    op.create_table(
        'remaining_estimate',
        sa.Column('begin_datetime', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('end_datetime', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('issue_id', postgresql.BIGINT(), nullable=False),
        sa.Column('team_id', postgresql.INTEGER(), nullable=False),
        sa.Column('implementation_type_id', postgresql.INTEGER(), nullable=False),
        sa.Column('estimation', postgresql.FLOAT(), nullable=True),
        sa.Column('comment', postgresql.TEXT(), nullable=True),
        sa.ForeignKeyConstraint(
            ('issue_id',),
            ('issue.id',),
            name='remaining_estimate_issue_id_fk',
        ),
        sa.ForeignKeyConstraint(
            ('team_id',),
            ('team.id',),
            name='remaining_estimate_team_id_fk',
        ),
        sa.ForeignKeyConstraint(
            ('implementation_type_id',),
            ('implementation_type.id',),
            name='remaining_estimate_implementation_type_id_fk',
        ),
        sa.UniqueConstraint(
            'begin_datetime', 'issue_id', 'team_id',
            name='remaining_estimate_begin_datetime_issue_id_team_id_idx'
        ),
    )


def downgrade():
    pass
