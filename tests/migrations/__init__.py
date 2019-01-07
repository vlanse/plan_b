import os

from alembic.command import ScriptDirectory
from sqlalchemy import exc
from yarl import URL

from tests import BaseDBTestCase


class TestMigrationsBase(BaseDBTestCase):
    DB_URL_ENV_VAR_NAME = 'MIGRATION_DB_URL'
    DB_URL = os.getenv(DB_URL_ENV_VAR_NAME, None)
    target_revision = None
    do_upgrade = False
    connect_to_db = False

    @classmethod
    def get_all_alembic_revisions(cls):
        script = ScriptDirectory.from_config(cls.alembic_config)
        revisions = []
        for sc in script.walk_revisions('base', 'heads'):
            revisions.append(sc.revision)
        return revisions

    @classmethod
    def get_previous_alembic_revision(cls):
        assert cls.target_revision, 'target_revision is not defined'

        revisions = cls.get_all_alembic_revisions()
        return revisions[revisions.index(cls.target_revision) + 1]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()

        # connect without database name specification to re-create database
        url = URL(self.DB_URL)
        db_name = url.path.split('/')[1]
        self.db.init_engine(str(url.with_path('')))
        with self.db.session() as session:
            session.connection().connection.set_isolation_level(0)
            try:
                session.execute(f'SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = \'{db_name}\'')
                session.execute(f'DROP DATABASE IF EXISTS {db_name}')
            except exc.OperationalError as err:
                pass
            session.execute(f'CREATE DATABASE {db_name}')
            session.connection().connection.set_isolation_level(1)
        self.db.close()

        # re-init connection to newly created database
        self.db.init_engine(self.DB_URL)
