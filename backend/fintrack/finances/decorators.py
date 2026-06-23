import time, logging
from functools import wraps

logger = logging.getLogger(__name__)


def log_execution_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"[PERF] {func.__name__} took {duration:.3f}s", flush=True)
        logger.info(f"{func.__name__} took {duration:.3f}s")
        return result
    return wrapper
