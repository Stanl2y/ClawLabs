"""CLIProxyAPI OpenAI-compatible client models."""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, ClassVar, Final, Literal, override

import httpx2
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from agentsec_lab.types import ToolName

MIN_FENCED_JSON_LINES: Final = 3


@dataclass(slots=True)
class CliProxyError(Exception):
    """Error raised when the live model boundary fails."""

    reason: str

    @override
    def __str__(self) -> str:
        return self.reason


class CliProxyConfig(BaseModel):
    """Connection settings for a CLIProxyAPI endpoint."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    base_url: str = Field(min_length=1)
    model: str = Field(min_length=1)
    api_key: str | None = None
    timeout_seconds: float = Field(default=60.0, gt=0)


class ChatMessage(BaseModel):
    """Chat message sent to the live model endpoint."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    """Non-streaming OpenAI-compatible chat completion request."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    model: str
    messages: tuple[ChatMessage, ...]
    temperature: float = 0.0
    stream: bool = False


class ChatChoiceMessage(BaseModel):
    """Assistant message returned by a chat completion choice."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    role: str
    content: str


class ChatChoice(BaseModel):
    """OpenAI-compatible chat completion choice."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    message: ChatChoiceMessage


class ChatCompletionResponse(BaseModel):
    """Response subset consumed by the live agent runner."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    choices: tuple[ChatChoice, ...]


class LiveToolDecision(BaseModel):
    """Live model request to run one local lab tool."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    action: Literal["tool"]
    tool_name: ToolName
    path: Path | None = None
    payload: str | None = None
    key: str | None = None
    query: str | None = None


class LiveFinalDecision(BaseModel):
    """Live model final answer for a scenario."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    action: Literal["final"]
    final_answer: str = Field(min_length=1)


type LiveDecision = Annotated[
    LiveToolDecision | LiveFinalDecision,
    Field(discriminator="action"),
]

LIVE_DECISION_ADAPTER: Final[TypeAdapter[LiveDecision]] = TypeAdapter(
    LiveDecision,
)


@dataclass(frozen=True, slots=True)
class CliProxyClient:
    """Synchronous CLIProxyAPI chat completion client."""

    config: CliProxyConfig

    def complete(self, messages: tuple[ChatMessage, ...]) -> str:
        """Return the assistant content for one non-streaming completion."""
        request = ChatCompletionRequest(
            model=self.config.model,
            messages=messages,
        )
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        try:
            with httpx2.Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout_seconds,
            ) as client:
                response = client.post(
                    "/v1/chat/completions",
                    json=request.model_dump(mode="json"),
                    headers=headers,
                )
                _ = response.raise_for_status()
        except httpx2.HTTPError as error:
            raise CliProxyError(
                reason=f"cliproxyapi request failed: {error}",
            ) from error
        try:
            completion = ChatCompletionResponse.model_validate_json(response.text)
        except ValidationError as error:
            raise CliProxyError(
                reason="cliproxyapi returned an invalid chat completion response",
            ) from error
        if len(completion.choices) == 0:
            raise CliProxyError(reason="cliproxyapi returned no choices")
        return completion.choices[0].message.content


def parse_live_decision(model_text: str) -> LiveDecision:
    """Parse the live model action JSON."""
    try:
        return LIVE_DECISION_ADAPTER.validate_json(_strip_json_fence(model_text))
    except ValidationError as error:
        raise CliProxyError(
            reason=f"live model returned invalid action JSON: {model_text}",
        ) from error


def _strip_json_fence(model_text: str) -> str:
    text = model_text.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if len(lines) >= MIN_FENCED_JSON_LINES and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text
"""CLIProxyAPI OpenAI-compatible client models."""
