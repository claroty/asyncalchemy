from __future__ import absolute_import

import os
from typing import Any

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from asyncalchemy import SessionFactoryType, create_session_factory
from asyncalchemy.session_committer import AsyncDBSession

PEOPLE_LIST = [f"Test{i}" for i in range(3)]

Base = declarative_base()   # type: Any # pylint: disable=invalid-name


# pylint: disable=inherit-non-class,too-few-public-methods
class Person(Base):
    """
    A basic SQLAlchemy model for testing purposes.
    """
    __tablename__ = "person"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)


async def get_session_factory(sqlite_path: str) -> SessionFactoryType:
    """
    Create a session factory, to be used alogside with fixture.
    """
    # Create paths.
    db_file = os.path.join(sqlite_path, "test.db")
    db_uri = f"sqlite:///{db_file}?check_same_thread=False"
    assert not os.path.exists(db_file)

    # Create session and verify sqlite file was created.
    session_factory = create_session_factory(db_uri, Base)
    assert os.path.exists(db_file)

    # Create test people.
    async with session_factory() as session:
        assert isinstance(session, AsyncDBSession)
        for name in PEOPLE_LIST:
            await session.add(Person(name=name)) # type: ignore

    return session_factory
