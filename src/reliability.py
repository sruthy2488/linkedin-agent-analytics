import time
import random

from google.api_core import exceptions


MAX_RETRIES = 5

BASE_DELAY = 2

MAX_DELAY = 30


RETRYABLE_EXCEPTIONS = (
    exceptions.TooManyRequests,       
    exceptions.InternalServerError,   
    exceptions.BadGateway,            
    exceptions.ServiceUnavailable,    
    exceptions.DeadlineExceeded,     
)


def run_with_retry(operation, operation_name):
    """
    Execute an operation with exponential backoff.

    Retries only transient/rate-limit errors.
    Permanent errors are raised immediately.
    """

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            return operation()

        except RETRYABLE_EXCEPTIONS as error:

            if attempt == MAX_RETRIES:
                print(
                    f"{operation_name} failed after "
                    f"{MAX_RETRIES} attempts."
                )
                raise

            delay = min(
                BASE_DELAY * (2 ** (attempt - 1)),
                MAX_DELAY
            )

            jitter = random.uniform(0, 1)

            wait_time = delay + jitter

            print(
                f"{operation_name} encountered a transient "
                f"error: {error}"
            )

            print(
                f"Retrying in {wait_time:.1f} seconds "
                f"(attempt {attempt + 1}/{MAX_RETRIES})..."
            )

            time.sleep(wait_time)