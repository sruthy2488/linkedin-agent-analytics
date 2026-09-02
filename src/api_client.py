import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()


class APIClient:

    def __init__(self):
        self.base_url = os.getenv("API_URL")
        self.token = os.getenv("API_TOKEN")

        if not self.base_url:
            raise ValueError("API_URL is not configured")

        self.session = requests.Session()

        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            })

    def get_leads(self, updated_after=None):

        params = {}

        if updated_after:
            params["updated_after"] = updated_after

        max_retries = 5

        for attempt in range(max_retries):

            try:

                response = self.session.get(
                    f"{self.base_url}/leads",
                    params=params,
                    timeout=30
                )

                # Rate limit
                if response.status_code == 429:

                    retry_after = response.headers.get(
                        "Retry-After",
                        "5"
                    )

                    wait_time = int(retry_after)

                    print(
                        f"Rate limited. Waiting {wait_time} seconds..."
                    )

                    time.sleep(wait_time)
                    continue

                # Temporary server errors
                if response.status_code in [500, 502, 503, 504]:

                    wait_time = 2 ** attempt

                    print(
                        f"Server error {response.status_code}. "
                        f"Retrying in {wait_time}s..."
                    )

                    time.sleep(wait_time)
                    continue

                response.raise_for_status()

                return response.json()

            except requests.RequestException as e:

                if attempt == max_retries - 1:
                    raise

                wait_time = 2 ** attempt

                print(
                    f"Request failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(wait_time)

        raise RuntimeError("API request failed after retries")