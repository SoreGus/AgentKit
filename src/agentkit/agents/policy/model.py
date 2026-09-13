import json
from abc import ABC, abstractmethod
from typing import Any

from agentkit.agents.policy.decision import PolicyDecision
from agentkit.models import MessageRole, Model, ModelMessage, ModelRequest


class ModelPolicy(ABC):
    def __init__(self, model: Model) -> None:
        self._model = model

    def evaluate_with_model(
        self,
        instructions: str,
        payload: dict[str, Any],
    ) -> PolicyDecision:
        response = self._model.generate(
            ModelRequest(
                messages=(
                    ModelMessage(
                        role=MessageRole.SYSTEM,
                        content=self._system_prompt(instructions),
                    ),
                    ModelMessage(
                        role=MessageRole.USER,
                        content=json.dumps(
                            payload,
                            ensure_ascii=False,
                            indent=2,
                        ),
                    ),
                )
            )
        )

        return self._parse_decision(response.content)

    def _system_prompt(self, instructions: str) -> str:
        return f"""You are evaluating an agent policy.

{instructions}

Return JSON only, with no markdown.

Allowed decisions:

{{"action": "allow", "feedback": ""}}
{{"action": "retry", "feedback": "Specific feedback explaining what should happen next."}}
{{"action": "reject", "feedback": "Specific feedback explaining why this must be rejected."}}
"""

    def _parse_decision(self, content: str) -> PolicyDecision:
        text = self._strip_code_fence(content)

        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return PolicyDecision.retry(
                "The model policy evaluator returned an invalid response. "
                "Continue with a safer approach and gather stronger evidence."
            )

        if not isinstance(value, dict):
            return PolicyDecision.retry(
                "The model policy evaluator returned an invalid response. "
                "Continue with a safer approach and gather stronger evidence."
            )

        action = value.get("action")
        feedback = value.get("feedback", "")

        if not isinstance(feedback, str):
            feedback = ""

        if action == "allow":
            return PolicyDecision.allow()

        if action == "retry":
            return PolicyDecision.retry(
                feedback or "The model policy requested another attempt."
            )

        if action == "reject":
            return PolicyDecision.reject(
                feedback or "The model policy rejected this action."
            )

        return PolicyDecision.retry(
            "The model policy evaluator returned an unknown decision. "
            "Continue with a safer approach and gather stronger evidence."
        )

    def _strip_code_fence(self, content: str) -> str:
        text = content.strip()

        if not text.startswith("```"):
            return text

        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

        if text.startswith("json"):
            text = text[4:].lstrip()

        return text
