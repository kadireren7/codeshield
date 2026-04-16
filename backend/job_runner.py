from __future__ import annotations

from uuid import UUID

from backend.analysis_service import run_path_analysis
from backend.jobs import complete_job, fail_job
from backend.models import PathAnalysisRequest


def run_background_analysis(job_id: UUID, request: PathAnalysisRequest) -> None:
    """Executed after HTTP response; must not raise."""
    try:
        response = run_path_analysis(request, request_id=job_id)
        complete_job(job_id, response.model_dump(mode="json"))
    except FileNotFoundError as exc:
        fail_job(job_id, str(exc))
    except (PermissionError, OSError) as exc:
        fail_job(job_id, f"Path could not be scanned: {exc}")
    except Exception as exc:  # pragma: no cover - defensive
        fail_job(job_id, str(exc))
