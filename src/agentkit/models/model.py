from abc import ABC, abstractmethod

from agentkit.models.request import ModelRequest
from agentkit.models.response import ModelResponse


class Model(ABC):
    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError
