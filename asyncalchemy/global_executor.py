"""
Creates a shared executor that will be exclusively used by asyncalchemy
"""
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

executor = None  # pylint: disable=invalid-name

def set_global_executor(global_executor: Optional[ThreadPoolExecutor] = None) -> None:
    """
    Set the global executor
    :param global_executor: executor to set
    """
    global executor  #pylint: disable=global-statement,invalid-name
    executor = global_executor
