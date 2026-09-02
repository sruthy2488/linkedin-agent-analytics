import json
import os
import urllib.request
import urllib.error


def send_alert(
    event,
    message,
    run_id,
    severity="CRITICAL",
    **details
):
    """
    Send a structured alert to a configured webhook.

    Alert failures must never crash the pipeline.
    """

    enabled = os.getenv("ALERT_ENABLED", "false").lower() == "true"
    webhook_url = os.getenv("ALERT_WEBHOOK_URL", "").strip()

    if not enabled:
        print(f"Alert disabled: {event}")
        return False

    if not webhook_url:
        print(f"Alert webhook not configured: {event}")
        return False

    payload = {
        "event": event,
        "severity": severity,
        "message": message,
        "run_id": run_id,
        "details": details
    }

    try:
        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            if 200 <= response.status < 300:
                print(f"Alert sent: {event}")
                return True

            print(
                f"Alert failed with HTTP status: "
                f"{response.status}"
            )
            return False

    except Exception as error:
        print(
            f"Alert delivery failed for {event}: "
            f"{error}"
        )
        return False