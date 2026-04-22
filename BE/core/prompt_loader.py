"""Prompt loader for agent system prompts from YAML resource files."""

from __future__ import annotations

from pathlib import Path

import yaml

from BE.utils.logger import get_logger

logger = get_logger(__name__)

_PROMPTS_FILE = Path(__file__).resolve().parent.parent / "resources" / "agent_prompts.yaml"


class PromptLoader:
    """Loads scenario-specific system prompts from the agent_prompts.yaml resource."""

    def __init__(self, prompts_path: Path | None = None) -> None:
        self._prompts_path = prompts_path or _PROMPTS_FILE
        self._cache: dict | None = None

    def _load_yaml(self) -> dict:
        """Load and cache the YAML prompts file."""
        if self._cache is not None:
            return self._cache

        if not self._prompts_path.exists():
            raise FileNotFoundError(
                f"Agent prompts file not found: {self._prompts_path}"
            )

        with open(self._prompts_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid prompts file format: expected dict, got {type(data).__name__}")

        self._cache = data
        return self._cache

    def load_prompt(self, analyst_type: str, scenario_type: str) -> str:
        """Load the system prompt for a given analyst_type and scenario_type.

        Looks up ``prompts[analyst_type][scenario_type]`` in the YAML file.

        Args:
            analyst_type: The analyst role (e.g. "buy_side", "credit").
            scenario_type: The analysis scenario (e.g. "pre_earnings").

        Returns:
            The system prompt string.

        Raises:
            KeyError: If the analyst_type or scenario_type is not found.
        """
        prompts = self._load_yaml()

        analyst_prompts = prompts.get(analyst_type)
        if analyst_prompts is None:
            raise KeyError(
                f"No prompts found for analyst_type '{analyst_type}'. "
                f"Available: {list(prompts.keys())}"
            )

        prompt = analyst_prompts.get(scenario_type)
        if prompt is None:
            raise KeyError(
                f"No prompt found for scenario_type '{scenario_type}' under "
                f"analyst_type '{analyst_type}'. Available: {list(analyst_prompts.keys())}"
            )

        return prompt
