from __future__ import annotations

import json
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


MAX_CAPTURE_CHARS = 20_000


class TaskSpecError(ValueError):
    """Raised when a task specification cannot be evaluated reliably."""


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    weight: float
    earned_weight: float
    duration_ms: int
    exit_code: int | None
    stdout: str
    stderr: str
    reason: str


@dataclass(frozen=True)
class EvaluationReport:
    task_id: str
    score: float
    passed_weight: float
    total_weight: float
    checks: tuple[CheckResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "score": self.score,
            "passed_weight": self.passed_weight,
            "total_weight": self.total_weight,
            "checks": [asdict(check) for check in self.checks],
        }


def load_task(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        spec = json.load(handle)
    validate_task(spec)
    return spec


def validate_task(spec: dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        raise TaskSpecError("task specification must be a JSON object")
    if not isinstance(spec.get("id"), str) or not spec["id"].strip():
        raise TaskSpecError("task id must be a non-empty string")
    checks = spec.get("checks")
    if not isinstance(checks, list) or not checks:
        raise TaskSpecError("checks must be a non-empty list")
    names: set[str] = set()
    total_weight = 0.0
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise TaskSpecError(f"check {index} must be an object")
        name = check.get("name")
        if not isinstance(name, str) or not name.strip():
            raise TaskSpecError(f"check {index} has no valid name")
        if name in names:
            raise TaskSpecError(f"duplicate check name: {name}")
        names.add(name)
        command = check.get("command")
        if not isinstance(command, list) or not command or not all(
            isinstance(part, str) and part for part in command
        ):
            raise TaskSpecError(f"check {name} must define a string command list")
        weight = check.get("weight")
        if not isinstance(weight, (int, float)) or weight <= 0:
            raise TaskSpecError(f"check {name} must have a positive weight")
        total_weight += float(weight)
    if total_weight <= 0:
        raise TaskSpecError("total weight must be positive")


def _clip(value: str) -> str:
    if len(value) <= MAX_CAPTURE_CHARS:
        return value
    return value[:MAX_CAPTURE_CHARS] + "\n...[output truncated]"


def _check_output(check: dict[str, Any], exit_code: int, stdout: str) -> tuple[bool, str]:
    expected_exit = int(check.get("expected_exit_code", 0))
    if exit_code != expected_exit:
        return False, f"expected exit code {expected_exit}, got {exit_code}"
    normalized = stdout.strip()
    if "stdout_equals" in check and normalized != str(check["stdout_equals"]).strip():
        return False, "stdout did not exactly match the expected value"
    if "stdout_contains" in check and str(check["stdout_contains"]) not in stdout:
        return False, "stdout did not contain the expected text"
    return True, "passed"


def evaluate_task(spec: dict[str, Any], submission_dir: str | Path) -> EvaluationReport:
    validate_task(spec)
    cwd = Path(submission_dir).resolve()
    if not cwd.is_dir():
        raise FileNotFoundError(f"submission directory does not exist: {cwd}")
    timeout = float(spec.get("timeout_seconds", 5))
    if timeout <= 0 or timeout > 60:
        raise TaskSpecError("timeout_seconds must be in the range (0, 60]")

    results: list[CheckResult] = []
    for check in spec["checks"]:
        started = time.perf_counter()
        exit_code: int | None = None
        stdout = ""
        stderr = ""
        passed = False
        reason = ""
        try:
            completed = subprocess.run(
                check["command"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
                check=False,
            )
            exit_code = completed.returncode
            stdout = _clip(completed.stdout)
            stderr = _clip(completed.stderr)
            passed, reason = _check_output(check, completed.returncode, completed.stdout)
        except subprocess.TimeoutExpired as exc:
            stdout = _clip(exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = _clip(exc.stderr or "") if isinstance(exc.stderr, str) else ""
            reason = f"timed out after {timeout:g} seconds"
        except OSError as exc:
            reason = f"could not start command: {exc}"

        duration_ms = round((time.perf_counter() - started) * 1000)
        weight = float(check["weight"])
        results.append(
            CheckResult(
                name=check["name"],
                passed=passed,
                weight=weight,
                earned_weight=weight if passed else 0.0,
                duration_ms=duration_ms,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                reason=reason,
            )
        )

    total_weight = sum(item.weight for item in results)
    passed_weight = sum(item.earned_weight for item in results)
    score = round(100 * passed_weight / total_weight, 2)
    return EvaluationReport(
        task_id=spec["id"],
        score=score,
        passed_weight=passed_weight,
        total_weight=total_weight,
        checks=tuple(results),
    )
