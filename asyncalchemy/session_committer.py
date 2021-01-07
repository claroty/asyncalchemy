from __future__ import absolute_import

from functools import partial
from typing import Any, Dict, Optional
from types import TracebackType

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.session import sessionmaker as sessionmaker_type

from asyncalchemy.utils import run_sync


# pylint: disable=too-few-public-methods
class SessionCommitter:
    """
    Class for managing async SQLAlchemy sessions.
    """

    def __init__(self, session_maker: sessionmaker_type,
                 reuse_session: Optional[Session] = None) -> None:
        """
        Create a SessonCommitter. You probably want create_session_factory instead.

        :param session_maker: A function returning a new SQLAlchemy session,
            sqlalchemy.orm.sessionmaker for example.
        :param reuse_session: If set to an existing session, will reduce the SessionCommitter
            to a noop and return that session instead.
        """
        self._session_maker = session_maker
        self._reuse_session = reuse_session
        self._session = reuse_session


    async def __aenter__(self) -> "AsyncDBSession":
        if self._reuse_session is None:
            self._session = await run_sync(self._session_maker)
        if not isinstance(self._session, AsyncDBSession):
            self._session = AsyncDBSession(self._session)

        return self._session


    async def __aexit__(self, exc_type: Optional[BaseException], exc_value: Optional[BaseException],
                        traceback: Optional[TracebackType]) -> None:
        """
        Commit changes on __aexit__, rollback if an exception occured, and close session.
        """
        if self._reuse_session is not None or self._session is None:
            return

        try:
            if exc_type is not None:
                await self._session.rollback()
                return
            await self._session.commit()

        except:
            await self._session.rollback()
            raise

        finally:
            await self._session.close()
            self._session = None



class AsyncQueryWrapper:
    """
    Class wraps SQLAlchemy's query functions with async executors.
    """

    MODIFY_FUNCTIONS = [
		"distinct",
		"filter",
		"filter_by",
		"from_self",
		"group_by",
		"having",
		"join",
		"limit",
		"offset",
		"order_by",
		"outerjoin",
		"populate_existing",
		"reset_joinpoint",
		"slice",
		"subquery",
		"union",
		"union_all",
    ]

    QUERY_FUNCTIONS = [
		"all",
		"count",
		"delete",
		"exists",
		"first",
		"one",
		"one_or_none",
		"scalar",
		"update",
	]

    def __init__(self, query: Query) -> None:
        self.query = query
        for function in self.MODIFY_FUNCTIONS:
            setattr(self, function, partial(self._modify_wrapper, function))
        for function in self.QUERY_FUNCTIONS:
            setattr(self, function, partial(self._query_wrapper, function))


    def _modify_wrapper(self, function_name: str, *args: Any,
                        **kwargs: Dict[Any, Any]) -> "AsyncQueryWrapper":
        return AsyncQueryWrapper(getattr(self.query, function_name)(*args, **kwargs))


    async def _query_wrapper(self, function_name: str, *args: Any, **kwargs: Dict[Any, Any]) -> Any:
        return await run_sync(getattr(self.query, function_name), *args, **kwargs)



# pylint: disable=too-few-public-methods
class AsyncDBSession:
    """
    Class wraps SQLAlchemy's session functions with async executors.
    """

    FUNCTIONS = [
		"add",
		"add_all",
		"begin",
		"begin_nested",
		"close",
		"commit",
		"delete",
		"execute",
		"expire",
		"expire_all",
		"expunge",
		"expunge_all",
		"flush",
		"invalidate",
		"merge",
		"prepare",
		"prune",
		"refresh",
		"rollback",
		"scalar",
	]

    def __init__(self, db_session: Session) -> None:
        self.session = db_session
        for function in self.FUNCTIONS:
            setattr(self, function, partial(self._wrapper, function))


    def query(self, *args: Any, **kwargs: Dict[Any, Any]) -> AsyncQueryWrapper:
        """
        Override session's query function with async wrapped version.
        """
        return AsyncQueryWrapper(self.session.query(*args, **kwargs))


    async def _wrapper(self, function_name: str, *args: Any, **kwargs: Dict[Any, Any]) -> Any:
        """
        Wrap session functions as async.
        """
        return await run_sync(getattr(self.session, function_name), *args, **kwargs)
