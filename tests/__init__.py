import logging
import os
from unittest import TestCase

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import Session, sessionmaker, Query

from alembic.command import upgrade as upgrade_database
from alembic.config import Config
from yarl import URL

import plan_b

log = logging.getLogger(__name__)

MODULE_PATH = os.path.abspath(os.path.dirname(plan_b.__file__))

DEFAULT_TX_ISOLATION_LEVEL = 'REPEATABLE_READ'


class DatabaseConfiguration:

    ENGINE = None
    SESSION_MAKER = None

    @classmethod
    def init_engine(
        cls,
        db_url: str,
        pool_size: int = 5,
        pool_recycle: int = 60,
        timeout: int = 30,
        max_overflow: int = 1,
        debug: bool = False,
        isolation_level: str = None
    ):
        engine = create_engine(
            db_url,
            isolation_level=(isolation_level or DEFAULT_TX_ISOLATION_LEVEL),
            encoding='utf-8',
            echo=debug,
            poolclass=QueuePool,
            pool_size=pool_size,
            pool_recycle=pool_recycle,
            pool_timeout=timeout,
            max_overflow=max_overflow,
            pool_pre_ping=True,
        )
        cls.ENGINE = engine
        cls.SESSION_MAKER = sessionmaker(
            bind=cls.ENGINE,
            query_cls=Query,
            class_=Session
        )

    @classmethod
    @contextmanager
    def session(cls) -> Session:
        session = cls.SESSION_MAKER(expire_on_commit=False)
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        else:
            session.commit()
        finally:
            session.close()

    @classmethod
    def close(cls):
        if cls.ENGINE is not None:
            cls.ENGINE.dispose()
            cls.ENGINE = None
        cls._SESSION_MAKER = None


class BaseDBTestCase(TestCase):
    setup_counter = 0
    db = None
    alembic_config = None
    do_upgrade = True
    connect_to_db = True

    DB_URL_ENV_VAR_NAME = 'DB_URL'
    DB_URL = os.getenv(DB_URL_ENV_VAR_NAME, None)

    @classmethod
    def setUpBase(cls):
        cls.setup_counter += 1
        if cls.setup_counter != 1:
            return

        if cls.DB_URL is None:
            raise RuntimeError(f'{cls.DB_URL_ENV_VAR_NAME} must be set')

        url = URL(cls.DB_URL)
        log.info("Preparing test database: %r", url)

        cls.alembic_config = Config(os.path.join(MODULE_PATH, 'alembic.ini'), 'alembic')
        logging.getLogger('alembic.runtime.migration').disabled = True

        cls.alembic_config.set_main_option('script_location', str(os.path.join(MODULE_PATH, 'alembic')))
        cls.alembic_config.set_main_option('sqlalchemy.url', str(url))

        if cls.do_upgrade:
            logging.debug('Upgrading to head migration')
            upgrade_database(cls.alembic_config, 'head')

        cls.db = DatabaseConfiguration()
        if cls.connect_to_db:
            cls.db.init_engine(str(url))

    @classmethod
    def tearDownBase(cls):
        cls.setup_counter -= 1
        if cls.setup_counter != 0:
            return
        DatabaseConfiguration.close()

    @classmethod
    def setUpClass(cls):
        cls.setUpBase()

    @classmethod
    def tearDownClass(cls):
        cls.tearDownBase()
