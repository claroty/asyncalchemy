from __future__ import absolute_import

from functools import partial
from asyncio import get_event_loop
from typing import Callable, Any, Dict


async def run_sync(function: Callable, *args: Any, **kwargs: Dict[Any, Any]) -> Any:
    """
    Run non-asynchronous as async using executor.
    """
    return await get_event_loop().run_in_executor(None, partial(function, *args, **kwargs))
