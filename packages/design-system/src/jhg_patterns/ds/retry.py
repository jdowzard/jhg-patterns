"""
Retry decorators and strategies for JHG applications.

Provides configurable retry logic with exponential backoff for handling
transient failures in API calls, database connections, and other
network operations.

Usage:
    from jhg_patterns.ds.retry import with_retry, DATABRICKS_RETRY, GRAPH_RETRY

    # Custom retry with decorator
    @with_retry(max_attempts=5, base_delay=0.5, max_delay=30)
    def flaky_operation():
        # Operation that might fail temporarily
        return api_call()

    # Pre-configured strategies
    @DATABRICKS_RETRY
    def query_databricks():
        return connector.query("SELECT * FROM table")

    @GRAPH_RETRY
    def send_email():
        return graph_client.send_email(...)
"""

import logging
from functools import wraps
from typing import Callable, Optional, Type, TypeVar

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable)


class DatabricksError(Exception):
    """Base exception for Databricks errors."""

    pass


class GraphError(Exception):
    """Base exception for MS Graph errors."""

    pass


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator for retrying operations with exponential backoff.

    Retries on specified exception types with exponential backoff:
    delay = base_delay * 2^attempt, capped at max_delay.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        retryable_exceptions: Tuple of exception types to retry on
            (default: (Exception,) - retries all exceptions)

    Returns:
        Decorated function that implements retry logic

    Example:
        @with_retry(max_attempts=5, base_delay=0.5, max_delay=30,
                    retryable_exceptions=(ConnectionError, TimeoutError))
        def fetch_data(url):
            return requests.get(url).json()

        result = fetch_data("https://api.example.com/data")
    """

    def decorator(func: F) -> F:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=base_delay, max=max_delay),
            retry=retry_if_exception_type(retryable_exceptions),
            reraise=True,
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


# Pre-configured retry strategies

DATABRICKS_RETRY = with_retry(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    retryable_exceptions=(DatabricksError, ConnectionError, TimeoutError),
)
"""
Retry strategy for Databricks operations.

Retries up to 3 times on DatabricksError, ConnectionError, or TimeoutError
with exponential backoff: 1s, 2s, 4s, capped at 30s.

Usage:
    @DATABRICKS_RETRY
    def query_databricks(connector, sql):
        return connector.query(sql)
"""

GRAPH_RETRY = with_retry(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    retryable_exceptions=(GraphError, ConnectionError, TimeoutError),
)
"""
Retry strategy for MS Graph API operations.

Retries up to 3 times on GraphError, ConnectionError, or TimeoutError
with exponential backoff: 1s, 2s, 4s, capped at 30s.

Usage:
    @GRAPH_RETRY
    def send_email(client, to, subject, body):
        return client.send_email(to=to, subject=subject, body_html=body)
"""


# Additional common strategies

REQUEST_RETRY = with_retry(
    max_attempts=5,
    base_delay=0.5,
    max_delay=60.0,
    retryable_exceptions=(ConnectionError, TimeoutError),
)
"""
Retry strategy for HTTP requests.

Retries up to 5 times on ConnectionError or TimeoutError with
exponential backoff: 0.5s, 1s, 2s, 4s, 8s, capped at 60s.

Usage:
    @REQUEST_RETRY
    def fetch_json(url):
        return requests.get(url, timeout=10).json()
"""
