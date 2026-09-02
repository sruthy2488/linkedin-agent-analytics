import logging
from pathlib import Path

from pythonjsonlogger import jsonlogger


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"


class PipelineLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that always carries the pipeline run_id."""

    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})
        extra.setdefault("run_id", self.extra["run_id"])
        extra.setdefault("event", "pipeline")
        return msg, kwargs


def get_pipeline_logger(run_id):
    """
    Create a structured JSON logger for one pipeline run.

    run_id is the correlation ID for the complete pipeline execution.
    """

    logger = logging.getLogger("linkedin_agent_pipeline")

    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:

        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s "
            "%(event)s %(run_id)s %(message)s"
        )

        file_handler = logging.FileHandler(
            LOG_FILE,
            encoding="utf-8"
        )

        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return PipelineLoggerAdapter(
        logger,
        {"run_id": run_id}
    )