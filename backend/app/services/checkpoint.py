"""Disk checkpoints that let a multi-step operation resume after a failure."""

import json
import logging
import os
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

logger: logging.Logger = logging.getLogger(__name__)


class Checkpoint:
    """Remember the result of every completed step of one operation.

    If a later step fails, the next identical request skips the steps that already
    succeeded instead of repeating them (for example, creating the same campaign in
    Keitaro twice). Call ``clear()`` after the last step so the same request can be
    run again from scratch.

    Limitations (acceptable for a single-instance deployment): the state lives in one
    JSON file, there is no locking, and the file is not shared between machines.

    Attributes:
        path: JSON file with the saved step results.
        key: Identifies the operation. It must include everything that defines the
            request (name, country, offers), otherwise a different request would
            reuse stale results.
    """

    DEFAULT_PATH = Path(tempfile.gettempdir()) / "campaign_checkpoint.json"

    def __init__(self, key: str, path: Path | str | None = None) -> None:
        self.path: Path = Path(path) if path else self.DEFAULT_PATH
        self.key: str = key

    def _read(self) -> dict:
        return json.loads(self.path.read_text("utf-8")) if self.path.exists() else {}

    def _write(self, data: dict) -> None:
        """Write atomically: dump to a temp file, then rename it over the original."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp: Path = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, self.path)

    async def run(self, step: str, fn: Callable[[], Awaitable[Any]]) -> Any:
        """Run a step unless it already succeeded, and save its result.

        Args:
            step: Step name, unique within the key.
            fn: Async callable that performs the step.

        Returns:
            The saved result if the step was already completed, otherwise the new one.

        Raises:
            Any exception raised by ``fn``; nothing is saved in that case.
        """
        done = self._read().get(self.key, {})
        if step in done:
            return done[step]

        try:
            result = await fn()
        except Exception:
            logger.warning("Step %r failed for %r; next request resumes from it", step, self.key)
            raise

        data: dict = self._read()
        data.setdefault(self.key, {})[step] = result
        self._write(data)
        return result

    def clear(self) -> None:
        """Forget all saved steps of this operation."""
        data: dict = self._read()
        if data.pop(self.key, None) is not None:
            self._write(data)
