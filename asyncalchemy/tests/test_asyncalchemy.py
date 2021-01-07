# pylint: disable=redefined-outer-name
from __future__ import absolute_import

import pytest

from sqlalchemy.exc import IntegrityError

from asyncalchemy import SessionFactoryType
from asyncalchemy.tests.utils import PEOPLE_LIST, get_session_factory, Person


@pytest.fixture
# pylint: disable=missing-function-docstring
async def session_factory(tmpdir: str) -> SessionFactoryType:
    return await get_session_factory(tmpdir)



@pytest.mark.asyncio
async def test_sanity(session_factory: SessionFactoryType) -> None:
    """
    Basic async query sanity test.
    """
    async with session_factory() as session:
        assert await session.query(Person).count() == 3 # type: ignore
        all_people = [x.name for x in await session.query(Person).all()]    # type: ignore
    assert all_people == PEOPLE_LIST


@pytest.mark.asyncio
async def test_modify(session_factory: SessionFactoryType) -> None:
    """
    Modify DB and make sure changes were commited successfuly (in a seperate session).
    """
    # Modify a person.
    async with session_factory() as session:
        obj1 = await session.query(Person).filter_by(name="Test1").one() # type: ignore
        obj1.name = "Test1a"

    # Verify modification was committed correctly and can be queried.
    async with session_factory() as session:
        all_people = [x.name for x in await session.query(Person).all()] # type: ignore
        assert all_people == ["Test0", "Test1a", "Test2"]


@pytest.mark.asyncio
async def test_rollback(session_factory: SessionFactoryType) -> None:
    """
    Verify changes aren't committed if an exception occurs in execution block.
    """
    # Rollback on exception
    with pytest.raises(RuntimeError):
        async with session_factory() as session:
            obj1 = await session.query(Person).filter_by(name="Test1").one() # type: ignore
            obj1.name = "Test1a"
            raise RuntimeError()

    # Verify changes weren't committed.
    async with session_factory() as session:
        all_people = [x.name for x in await session.query(Person).all()] # type: ignore
        assert all_people == PEOPLE_LIST


@pytest.mark.asyncio
async def test_exception_on_commit(session_factory: SessionFactoryType) -> None:
    """
    Verify changes aren't commited if change throws an exception.
    """
    # Try to commit a change that will fail.
    with pytest.raises(IntegrityError):
        async with session_factory() as session:
            await session.add(Person(name=None)) # type: ignore

    # Verify changes weren't committed.
    async with session_factory() as session:
        all_people = [x.name for x in await session.query(Person).all()] # type: ignore
        assert all_people == PEOPLE_LIST


@pytest.mark.asyncio
async def test_reuse_session(session_factory: SessionFactoryType) -> None:
    """
    Reuse session and verify changes are only committed after original session exists.
    """
    # Create the original session.
    async with session_factory() as session:
        # Reuse session sanity.
        async with session_factory(reuse_session=session) as reused_session:
            await reused_session.add(Person(name="Test3")) # type: ignore
            await reused_session.add(Person(name="Test4")) # type: ignore

        # Reuse with exception.
        with pytest.raises(RuntimeError):
            async with session_factory(reuse_session=session) as reused_session:
                await reused_session.add(Person(name="Test5")) # type: ignore
                raise RuntimeError()

        # Make sure the subsession didn't commit anything.
        async with session_factory() as secondary:
            all_people = [x.name for x in await secondary.query(Person).all()] # type: ignore
            assert all_people == PEOPLE_LIST

    # Make sure the parent session did commit.
    async with session_factory(reuse_session=session) as secondary:
        all_people = [x.name for x in await session.query(Person).all()] # type: ignore
        assert all_people == ["Test0", "Test1", "Test2", "Test3", "Test4", "Test5"]
