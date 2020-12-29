from __future__ import absolute_import

from typing import Any, Dict, Callable, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative.api import DeclarativeMeta

from asyncalchemy.session_committer import SessionCommitter


def create_session_factory(uri: str, base: Optional[DeclarativeMeta] = None,
    **engine_kwargs: Dict[Any, Any]) -> Callable[[Optional[Session]], SessionCommitter]:
    """
    Create an SQLAlchemy session factory.

    :param uri: The URI to the database to use
    :param base: The declarative base class, if any
    :param engine_kwargs: Keyword arguments to be passed to SQLAlchemy's create_engine
    :returns: A function of (reuse_session=None) -> SessionCommitter
    """
    engine = create_engine(uri, **engine_kwargs)
    session_maker = sessionmaker(bind=engine)

    # Create tables.
    if base is not None:
        base.metadata.create_all(engine)

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
