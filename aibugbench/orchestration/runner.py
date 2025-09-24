"""Benchmark orchestration entry point (Phase 2.5).

Adds bounded concurrency, retry/backoff, and resumable checkpoints while
keeping a thin, deterministic surface for the CLI.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
import contextlib
from dataclasses import dataclass
from enum import Enum, auto
import json
import os
from pathlib import Path
import random
import threading
import time
from typing import Any, Protocol

from aibugbench.config.artifacts import choose_artifact_path

__all__ = [
    "BenchmarkRunner",
    "RetriableError",
    "RunResult",
    "RunStatus",
]

_StrPath = str | Path


class RunStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class RunResult:
    prompt: str
    status: RunStatus
    summary: dict[str, Any] | None
    error: str | None = None


class Clock(Protocol):
    def sleep(self, seconds: float) -> None: ...


class Logger(Protocol):
    def event(self, name: str, **fields: Any) -> None: ...


class _SystemClock:
    def sleep(self, seconds: float) -> None:  # pragma: no cover - thin wrapper
        time.sleep(seconds)


class _NullLogger:
    def event(self, name: str, **fields: Any) -> None:  # pragma: no cover
        return None


class RetriableError(Exception):
    """Signal that a run may be retried safely."""


class _FS(Protocol):
    def atomic_write_json(self, path: _StrPath, obj: dict[str, Any]) -> None: ...

    def load_json(self, path: _StrPath) -> Any | None: ...


class BenchmarkRunner:
    """Coordinate benchmark execution with retry/backoff and checkpoints."""

    _LOCK_POLL_SECONDS = 0.1

    def __init__(
        self,
        *,
        validator_factory: Callable[[str], Validator],
        env: Mapping[str, str],
        fs: _FS,
        args: Mapping[str, Any] | None = None,
        default_artifact: str | None = None,
        clock: Clock | None = None,
        logger: Logger | None = None,
        max_workers: int | None = None,
        max_retries: int | None = None,
        backoff_base: float | None = None,
        backoff_factor: float | None = None,
        jitter: float | None = None,
        retry_seed: int | None = None,
    ) -> None:
        self._validator_factory = validator_factory
        self._env = dict(env)
        self._fs = fs
        self._args = dict(args or {})
        self._default_artifact = default_artifact
        self._clock = clock or _SystemClock()
        self._logger = logger or _NullLogger()

        self._max_workers = self._resolve_int(
            provided=max_workers,
            arg_keys=("max_workers", "concurrency", "jobs"),
            env_key="AIBENCH_CONCURRENCY",
            default=1,
        )
        self._max_workers = max(1, self._max_workers)

        self._max_retries = self._resolve_int(
            provided=max_retries,
            arg_keys=("max_retries",),
            env_key="AIBENCH_MAX_RETRIES",
            default=2,
        )
        self._max_retries = max(0, self._max_retries)

        self._backoff_base = self._resolve_float(
            provided=backoff_base,
            arg_keys=("backoff_base",),
            env_key="AIBENCH_BACKOFF_BASE",
            default=0.5,
        )
        self._backoff_factor = self._resolve_float(
            provided=backoff_factor,
            arg_keys=("backoff_factor",),
            env_key="AIBENCH_BACKOFF_FACTOR",
            default=2.0,
        )
        self._jitter = max(
            0.0,
            min(
                1.0,
                self._resolve_float(
                    provided=jitter,
                    arg_keys=("backoff_jitter", "jitter"),
                    env_key="AIBENCH_BACKOFF_JITTER",
                    default=0.1,
                ),
            ),
        )

        seed = self._resolve_int(
            provided=retry_seed,
            arg_keys=("retry_seed",),
            env_key="AIBENCH_RETRY_SEED",
            default=0,
        )
        # Deterministic, non-cryptographic RNG for jitter/backoff calculations.
        # Acceptable for scheduling; no security impact.
        self._rng = random.Random(seed)  # noqa: S311
        self._rng_lock = threading.Lock()

        self._artifact_root: Path | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_once(self, prompt: str) -> dict[str, Any]:
        summary = self._perform_single_run(prompt)
        if not self._is_dry_run():
            self._write_checkpoint(
                prompt,
                status="SUCCEEDED",
                summary=summary,
                attempts=1,
                error=None,
            )
        return summary

    def run_many(self, prompts: Iterable[str]) -> list[RunResult]:
        prompts_list = list(prompts)
        if not prompts_list:
            return []

        if self._is_dry_run():
            return [
                RunResult(prompt=p, status=RunStatus.SUCCEEDED, summary=self._perform_single_run(p))
                for p in prompts_list
            ]

        start_time = time.perf_counter()
        results_map: dict[str, RunResult] = {}
        work: list[tuple[str, int]] = []

        for prompt in prompts_list:
            checkpoint = self._load_checkpoint(prompt)
            if checkpoint and checkpoint.get("status") == "SUCCEEDED":
                summary = checkpoint.get("summary")
                if summary is None:
                    summary = self._read_summary(prompt)
                self._emit("run.skip", prompt=prompt, reason="checkpoint_succeeded")
                results_map[prompt] = RunResult(
                    prompt=prompt,
                    status=RunStatus.SKIPPED,
                    summary=summary,
                )
                continue

            attempts_used = int(checkpoint.get("attempts", 0)) if checkpoint else 0
            if (
                checkpoint
                and checkpoint.get("status") == "FAILED"
                and attempts_used >= self._max_attempts
            ):
                error = checkpoint.get("error")
                self._emit(
                    "run.failure",
                    prompt=prompt,
                    attempts=attempts_used,
                    error=error,
                    resumed=False,
                )
                results_map[prompt] = RunResult(
                    prompt=prompt,
                    status=RunStatus.FAILED,
                    summary=None,
                    error=error,
                )
                continue

            work.append((prompt, attempts_used))

        self._emit(
            "runner.start",
            prompts=len(prompts_list),
            pending=len(work),
            max_workers=self._max_workers,
        )

        if self._max_workers <= 1 or len(work) <= 1:
            for prompt, attempts_used in work:
                results_map[prompt] = self._execute_with_retries(prompt, attempts_used)
        else:
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                futures = {
                    executor.submit(self._execute_with_retries, prompt, attempts_used): prompt
                    for prompt, attempts_used in work
                }
                for future in as_completed(futures):
                    prompt = futures[future]
                    results_map[prompt] = future.result()

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        self._emit(
            "runner.finish",
            duration_ms=duration_ms,
            succeeded=sum(1 for r in results_map.values() if r.status is RunStatus.SUCCEEDED),
            failed=sum(1 for r in results_map.values() if r.status is RunStatus.FAILED),
            skipped=sum(1 for r in results_map.values() if r.status is RunStatus.SKIPPED),
        )

        return [results_map[p] for p in prompts_list]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _perform_single_run(self, prompt: str) -> dict[str, Any]:
        artifact_root = self._artifact_root_path()
        summary: dict[str, Any] = {
            "status": "ok",
            "prompt": prompt,
            "artifact": str(artifact_root),
            "artifacts": {},
            "score": 0.0,
        }

        if self._is_dry_run():
            return summary

        run_dir = artifact_root / prompt
        run_dir.mkdir(parents=True, exist_ok=True)

        validator = self._validator_factory(prompt)
        analysis = validator.analyze(str(run_dir))
        score = float(validator.score(analysis))

        analysis_path = run_dir / "analysis.json"
        summary_path = run_dir / "summary.json"

        self._fs.atomic_write_json(analysis_path, analysis)
        self._fs.atomic_write_json(summary_path, {"prompt": prompt, "score": score})

        summary["score"] = score
        summary["artifacts"] = {
            "analysis": str(analysis_path),
            "summary": str(summary_path),
        }
        return summary

    def _execute_with_retries(self, prompt: str, attempts_completed: int) -> RunResult:
        lock_path = self._acquire_lock(prompt)
        try:
            attempt = attempts_completed
            while attempt < self._max_attempts:
                attempt += 1
                self._emit("run.start", prompt=prompt, attempt=attempt)
                try:
                    summary = self._perform_single_run(prompt)
                except Exception as exc:
                    if self._is_dry_run():
                        return RunResult(prompt, RunStatus.SUCCEEDED, summary=None)

                    if self._should_retry(exc) and attempt < self._max_attempts:
                        delay = self._compute_backoff(attempt)
                        self._emit(
                            "run.retry",
                            prompt=prompt,
                            attempt=attempt,
                            delay=delay,
                            error=self._format_error(exc),
                        )
                        self._clock.sleep(delay)
                        continue

                    error_text = self._format_error(exc)
                    self._write_checkpoint(
                        prompt,
                        status="FAILED",
                        summary=None,
                        attempts=attempt,
                        error=error_text,
                    )
                    self._emit(
                        "run.failure",
                        prompt=prompt,
                        attempts=attempt,
                        error=error_text,
                        resumed=True,
                    )
                    return RunResult(
                        prompt=prompt,
                        status=RunStatus.FAILED,
                        summary=None,
                        error=error_text,
                    )

                self._write_checkpoint(
                    prompt,
                    status="SUCCEEDED",
                    summary=summary,
                    attempts=attempt,
                    error=None,
                )
                self._emit("run.success", prompt=prompt, attempts=attempt)
                return RunResult(prompt=prompt, status=RunStatus.SUCCEEDED, summary=summary)

            error_text = "max attempts exhausted"
            self._write_checkpoint(
                prompt,
                status="FAILED",
                summary=None,
                attempts=self._max_attempts,
                error=error_text,
            )
            self._emit(
                "run.failure",
                prompt=prompt,
                attempts=self._max_attempts,
                error=error_text,
                resumed=True,
            )
            return RunResult(prompt, RunStatus.FAILED, None, error=error_text)
        finally:
            self._release_lock(lock_path)

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    @property
    def _max_attempts(self) -> int:
        return self._max_retries + 1

    def _resolve_int(
        self,
        *,
        provided: int | None,
        arg_keys: tuple[str, ...],
        env_key: str,
        default: int,
    ) -> int:
        if provided is not None:
            return int(provided)

        for key in arg_keys:
            raw = self._args.get(key)
            if raw is None:
                continue
            try:
                return int(raw)
            except (TypeError, ValueError):
                continue

        raw_env = self._env.get(env_key)
        if raw_env is not None:
            try:
                return int(raw_env)
            except ValueError:
                pass
        return default

    def _resolve_float(
        self,
        *,
        provided: float | None,
        arg_keys: tuple[str, ...],
        env_key: str,
        default: float,
    ) -> float:
        if provided is not None:
            return float(provided)

        for key in arg_keys:
            raw = self._args.get(key)
            if raw is None:
                continue
            try:
                return float(raw)
            except (TypeError, ValueError):
                continue

        raw_env = self._env.get(env_key)
        if raw_env is not None:
            try:
                return float(raw_env)
            except ValueError:
                pass
        return default

    # ------------------------------------------------------------------
    # Checkpoint handling
    # ------------------------------------------------------------------

    def _artifact_root_path(self) -> Path:
        if self._artifact_root is None:
            path_str = choose_artifact_path(
                self._args,
                self._env,
                self._default_artifact,
            )
            self._artifact_root = Path(path_str)
        return self._artifact_root

    def _run_dir(self, prompt: str) -> Path:
        return self._artifact_root_path() / prompt

    def _summary_path(self, prompt: str) -> Path:
        return self._run_dir(prompt) / "summary.json"

    def _checkpoint_path(self, prompt: str) -> Path:
        return self._run_dir(prompt) / "checkpoint.json"

    def _load_checkpoint(self, prompt: str) -> dict[str, Any] | None:
        path = self._checkpoint_path(prompt)
        data = self._fs.load_json(path)
        return data if isinstance(data, dict) else None

    def _write_checkpoint(
        self,
        prompt: str,
        *,
        status: str,
        summary: dict[str, Any] | None,
        attempts: int,
        error: str | None,
    ) -> None:
        payload = {
            "prompt": prompt,
            "status": status,
            "summary": summary,
            "attempts": attempts,
            "error": error,
        }
        self._fs.atomic_write_json(self._checkpoint_path(prompt), payload)

    def _read_summary(self, prompt: str) -> dict[str, Any] | None:
        data = self._fs.load_json(self._summary_path(prompt))
        return data if isinstance(data, dict) else None

    # ------------------------------------------------------------------
    # Lock helpers
    # ------------------------------------------------------------------

    def _acquire_lock(self, prompt: str) -> Path:
        lock_path = self._run_dir(prompt) / ".lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        while True:
            try:
                fd = os.open(lock_path, flags)
            except FileExistsError:
                self._clock.sleep(self._LOCK_POLL_SECONDS)
                continue
            else:
                try:
                    os.write(fd, json.dumps({"pid": os.getpid()}).encode("utf-8"))
                finally:
                    os.close(fd)
                return lock_path

    def _release_lock(self, lock_path: Path) -> None:
        with contextlib.suppress(FileNotFoundError):  # pragma: no cover - best effort cleanup
            lock_path.unlink()

    # ------------------------------------------------------------------
    # Retry helpers
    # ------------------------------------------------------------------

    def _compute_backoff(self, attempt: int) -> float:
        delay = self._backoff_base * (self._backoff_factor ** max(0, attempt - 1))
        if self._jitter == 0.0:
            return delay
        with self._rng_lock:
            delta = self._rng.uniform(-self._jitter, self._jitter)
        return max(0.0, delay * (1.0 + delta))

    def _should_retry(self, exc: Exception) -> bool:
        if isinstance(exc, RetriableError):
            return True
        retriable_flag = getattr(exc, "retriable", None)
        if isinstance(retriable_flag, bool):
            return retriable_flag
        return False

    @staticmethod
    def _format_error(exc: Exception) -> str:
        return f"{exc.__class__.__name__}: {exc}" if exc else ""

    # ------------------------------------------------------------------
    # Misc helpers
    # ------------------------------------------------------------------

    def _is_dry_run(self) -> bool:
        return bool(self._args.get("dry_run"))

    def _emit(self, name: str, **fields: Any) -> None:
        # Logging must never raise; suppress all logger backend exceptions.
        with contextlib.suppress(Exception):
            self._logger.event(name, **fields)


# Deferred import to avoid cycles
from aibugbench.validation.base import Validator  # noqa: E402
