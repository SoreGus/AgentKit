import json
from abc import ABC
from dataclasses import dataclass
from typing import Any, Callable

from agentkit.agents.policy.decision import PolicyDecision
from agentkit.models import Model, ModelRequest, ModelResponse, ModelMessage, MessageRole


@dataclass(frozen=True, slots=True)
class ModelPolicyRequested:
    policy_name: str
    request: ModelRequest


@dataclass(frozen=True, slots=True)
class ModelPolicyResponded:
    policy_name: str
    response: ModelResponse


ModelPolicyEvent = ModelPolicyRequested | ModelPolicyResponded
ModelPolicyEventHandler = Callable[[ModelPolicyEvent], None]


class ModelPolicy(ABC):
    def __init__(
        self,
        model: Model,
        on_model_event: ModelPolicyEventHandler | None = None,
        policy_name: str | None = None,
    ) -> None:
        self._model = model
        self._on_model_event = on_model_event
        self._policy_name = policy_name or type(self).__name__

    def evaluate_with_model(
        self,
        instructions: str,
        payload: dict[str, Any],
    ) -> PolicyDecision:
        request = ModelRequest(
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

        self._emit(
            ModelPolicyRequested(
                policy_name=self._policy_name,
                request=request,
            )
        )

        response = self._model.generate(request)

        self._emit(
            ModelPolicyResponded(
                policy_name=self._policy_name,
                response=response,
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

    def _emit(self, event: ModelPolicyEvent) -> None:
        if self._on_model_event is not None:
            self._on_model_event(event)
