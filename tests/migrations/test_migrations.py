from alembic.command import upgrade as upgrade_database, downgrade as downgrade_database

from . import TestMigrationsBase


class TestMigrationSanity(TestMigrationsBase):

    def test_all_migrations(self):
        """
        Check that upgrades/downgrades in all revisions are applied correctly
        """
        revisions = self.get_all_alembic_revisions()
        upgrade_database(self.alembic_config, revisions[0])
        downgrade_database(self.alembic_config, 'base')
