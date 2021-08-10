from __future__ import absolute_import

from asyncio import get_event_loop
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Callable, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative.api import DeclarativeMeta

from asyncalchemy.session_committer import SessionCommitter

# Callable doesn't support optional parameters (reuse_session in our case),
#   therefore the "..." convention is used.
SessionFactoryType = Callable[..., SessionCommitter]

SQLITE_DRIVER_NAME = 'pysqlite'


def create_session_factory_from_engine(engine: Engine) -> SessionFactoryType:
    """
    Create an SQLAlchemy session factory from an engine instance.

    :param engine: An instance of an SQLAlchemy engine.
    :returns: A function of (reuse_session=None) -> SessionCommitter
    """
    session_maker = sessionmaker(bind=engine)

    # SQLite workaround: SQLite objects cannot be shared between threads
    if engine.driver == SQLITE_DRIVER_NAME:
        print('WARNING: Sqlite backend detected. Using single threaded executor '
			  '- DO NOT USE IN PRODUCTION!')
        executor = ThreadPoolExecutor(max_workers=1)
        get_event_loop().set_default_executor(executor)

    def factory(reuse_session: Optional[Session] = None) -> SessionCommitter:
        """
        Create a session.

        :param reuse_session: If set to an existing session, will reduce the SessionCommitter
            to a noop and return that session instead. Useful for with statements that might
            be within other with statements, but not necessarily.
        :returns: A SessionCommitter
        """
        return SessionCommitter(session_maker, reuse_session)
    return factory


def create_session_factory(uri: str, base: Optional[DeclarativeMeta] = None,
    **engine_kwargs: Dict[Any, Any]) -> SessionFactoryType:
    """
    Create an SQLAlchemy session factory.

    :param uri: The URI to the database to use
    :param base: The declarative base class, if any
    :param engine_kwargs: Keyword arguments to be passed to SQLAlchemy's create_engine
    :returns: A function of (reuse_session=None) -> SessionCommitter
    """
    engine = create_engine(uri, **engine_kwargs)

    # Create tables.
    if base is not None:
        base.metadata.create_all(engine)

    return create_session_factory_from_engine(engine)
