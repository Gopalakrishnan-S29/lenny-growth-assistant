
from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.config import get_settings


class PiAgentError(Exception):
    """Raised when Pi Agent fails."""


class PiAgent:
    """Run Pi Agent with local Ollama without long CLI prompt arguments."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        return await asyncio.to_thread(
            self._generate_sync,
            prompt,
            system_prompt,
        )

    def _generate_sync(
        self,
        prompt: str,
        system_prompt: str | None,
    ) -> str:
        pi_executable = shutil.which("pi.cmd") or shutil.which("pi")

        if not pi_executable:
            raise PiAgentError(
                "Pi executable not found. Check that Pi is installed "
                "and available in PATH."
            )

        model = getattr(
            self.settings,
            "ollama_model",
            "llama3.2:latest",
        )

        # A temporary file keeps the large system prompt off the CLI.
        temp_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".md",
                prefix="pi-system-",
                delete=False,
            ) as system_file:
                system_file.write(
                    system_prompt or "You are a helpful assistant."
                )
                temp_path = system_file.name

            command = [
                pi_executable,
                "--provider", "ollama",
                "--model", model,
                "--no-session",
                "--no-tools",
                "--print",
                "--system-prompt", temp_path,
            ]

            # The user's full prompt goes through stdin, not CLI arguments.
            result = subprocess.run(
                command,
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
                shell=False,
                env=os.environ.copy(),
                check=False,
            )

            if result.returncode != 0:
                error_text = (
                    result.stderr or result.stdout or ""
                ).strip()

                raise PiAgentError(
                    error_text[-3000:]
                    if error_text
                    else f"Pi exited with code {result.returncode}."
                )

            answer = (result.stdout or "").strip()

            if not answer:
                raise PiAgentError(
                    "Pi completed but returned an empty response."
                )

            return answer

        except subprocess.TimeoutExpired as exc:
            raise PiAgentError(
                "Pi Agent timed out while generating the response."
            ) from exc
        except OSError as exc:
            raise PiAgentError(
                f"Could not start Pi Agent: {exc}"
            ) from exc
        finally:
            if temp_path:
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except OSError:
                    pass
