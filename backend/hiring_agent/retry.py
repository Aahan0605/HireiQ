import asyncio
import random
import logging
import re
import time
from typing import Callable, Any

logger = logging.getLogger(__name__)

# Maximum total wall-clock time for all retries combined
MAX_TOTAL_RETRY_SECONDS = float(90)


async def retry_with_backoff(func: Callable, *args, max_retries: int = 3, base_delay: float = 1.0, **kwargs) -> Any:
    """
    Retry an async function with exponential backoff and jitter.
    Specifically handles google.api_core.exceptions.ResourceExhausted rate limits.

    Key behaviors:
    - If the quota error is a *daily* quota (GenerateRequestsPerDayPerProjectPerModel),
      the retry is aborted immediately because waiting won't help.
    - If the retry-delay hint from the API exceeds MAX_TOTAL_RETRY_SECONDS, fail fast.
    - Total wall-clock time across all retries is capped at MAX_TOTAL_RETRY_SECONDS.
    """
    delay = base_delay
    actual_max_retries = max(max_retries, 5)
    start_wall = time.monotonic()

    for attempt in range(actual_max_retries):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            error_class_name = e.__class__.__name__
            error_str = str(e)
            is_rate_limit = "ResourceExhausted" in error_class_name or "429" in error_str

            # Detect daily quota exhaustion — retrying won't help
            if is_rate_limit and "PerDayPerProject" in error_str:
                logger.error(
                    "Daily API quota exhausted (PerDayPerProjectPerModel). "
                    "Failing immediately without further retries."
                )
                raise e

            if attempt == actual_max_retries - 1:
                logger.error(f"All retries ({actual_max_retries}) exhausted. Final error: {e}")
                raise e

            # Check total wall-clock budget
            elapsed = time.monotonic() - start_wall
            if elapsed >= MAX_TOTAL_RETRY_SECONDS:
                logger.error(
                    f"Retry wall-clock budget ({MAX_TOTAL_RETRY_SECONDS}s) exhausted "
                    f"after {attempt + 1} attempts. Last error: {e}"
                )
                raise e

            # Compute backoff
            if is_rate_limit:
                match = re.search(r"(?:retry[_ ]in|retry[_ ]delay|please[_ ]retry[_ ]in)\s+([\d.]+)", error_str, re.I)
                if match:
                    suggested = float(match.group(1))
                    remaining_budget = MAX_TOTAL_RETRY_SECONDS - elapsed
                    if suggested > remaining_budget:
                        logger.warning(
                            f"API suggests retry in {suggested:.0f}s but only {remaining_budget:.0f}s budget left. Failing fast."
                        )
                        raise e
                    sleep_time = suggested + random.uniform(0.5, 1.5)
                else:
                    sleep_time = min(8.0 * (2 ** attempt) + random.uniform(0.5, 1.5),
                                     MAX_TOTAL_RETRY_SECONDS - elapsed)
            else:
                sleep_time = min(delay * (2 ** attempt) + random.uniform(0, 1),
                                 MAX_TOTAL_RETRY_SECONDS - elapsed)

            # Ensure positive sleep
            sleep_time = max(0.5, sleep_time)

            logger.warning(
                f"Attempt {attempt + 1}/{actual_max_retries} failed with error ({error_class_name}): {e}. "
                f"Retrying in {sleep_time:.2f}s..."
            )
            await asyncio.sleep(sleep_time)
