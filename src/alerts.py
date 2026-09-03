import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def send_alert(
    event,
    message,
    run_id,
    severity="CRITICAL",
    **details
):
    """
    Send a structured alert to a configured Discord webhook.

    Alert failures must never crash the pipeline.

    Parameters
    ----------
    event : str
        Name of the alert event.

    message : str
        Human-readable alert message.

    run_id : str
        Unique pipeline execution ID.

    severity : str
        Alert severity such as INFO, WARNING or CRITICAL.

    **details
        Additional information included in the alert.

    Returns
    -------
    bool
        True if the alert was successfully delivered.
        False if alerting is disabled, not configured,
        or Discord rejects/fails the request.
    """

    enabled = (
        os.getenv(
            "ALERT_ENABLED",
            "false"
        )
        .strip()
        .lower()
        == "true"
    )

    webhook_url = (
        os.getenv(
            "ALERT_WEBHOOK_URL",
            ""
        )
        .strip()
    )


    if not enabled:
        print(
            f"Alert disabled: {event}"
        )
        return False

    

    if not webhook_url:
        print(
            f"Alert webhook not configured: "
            f"{event}"
        )
        return False


    details_text = "\n".join(
        f"**{key}:** {value}"
        for key, value in details.items()
    )


    content = (
        "🚨 **LinkedIn Agent Analytics Alert**\n\n"
        f"**Event:** {event}\n"
        f"**Severity:** {severity}\n"
        f"**Message:** {message}\n"
        f"**Run ID:** `{run_id}`"
    )

    if details_text:
        content += (
            f"\n{details_text}"
        )

    
    payload = {
        "content": content
    }

    

    try:

        data = json.dumps(
            payload
        ).encode("utf-8")

        request = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": (
                    "LinkedIn-Agent-Analytics/1.0"
                )
            },
            method="POST"
        )

        with urllib.request.urlopen(
            request,
            timeout=10
        ) as response:

            

            if 200 <= response.status < 300:

                print(
                    f"Alert sent: {event}"
                )

                return True

            print(
                f"Alert failed with HTTP status: "
                f"{response.status}"
            )

            return False

    

    except urllib.error.HTTPError as error:

        try:

            response_body = (
                error.read()
                .decode(
                    "utf-8",
                    errors="replace"
                )
            )

        except Exception:

            response_body = ""

        print(
            f"Alert delivery failed for "
            f"{event}: "
            f"HTTP {error.code} "
            f"{error.reason}"
        )

        if response_body:

            print(
                f"Discord response: "
                f"{response_body}"
            )

        return False

   

    except urllib.error.URLError as error:

        print(
            f"Alert delivery failed for "
            f"{event}: "
            f"Network error: {error.reason}"
        )

        return False

    

    except Exception as error:

        print(
            f"Alert delivery failed for "
            f"{event}: {error}"
        )

        return False