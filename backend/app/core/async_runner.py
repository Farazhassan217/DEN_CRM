import anyio
from typing import Callable, TypeVar, Any

T = TypeVar("T")

async def run_in_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Executes a blocking synchronous function in a separate worker thread
    via anyio.to_thread.run_sync to keep the FastAPI asyncio event loop unblocked.
    """
    if kwargs:
        def wrapped():
            return func(*args, **kwargs)
        return await anyio.to_thread.run_sync(wrapped)
    return await anyio.to_thread.run_sync(func, *args)


async def execute_query(query: Any) -> Any:
    """
    Executes a blocking Supabase PostgREST sync query in a worker thread
    via anyio.to_thread.run_sync to eliminate event loop blocking.
    """
    return await run_in_thread(query.execute)
