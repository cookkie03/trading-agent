"""Datapizza AI LLM client — replaces the LangChain-backed StructuredLLM.

Uses datapizza.clients (OpenAI/Ollama/VertexAI) directly with structured output
and tool calling, removing the LangChain + LangGraph dependency from the brain.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from pydantic import BaseModel

from .schemas import DeskOpinion, PMDecision, RiskDecision


class DatapizzaLLM:
    """Unified LLM client backed by Datapizza.

    Supports structured output and tool calling via the Datapizza Agent loop.
    Replaces ForkStructuredLLM (LangChain) with a single clean interface.
    """

    def __init__(
        self,
        config: Optional[dict[str, Any]] = None,
        *,
        deep: bool = True,
        max_tool_iters: int = 4,
    ):
        from ..default_config import DEFAULT_CONFIG

        self.config = config or DEFAULT_CONFIG
        self.max_tool_iters = max_tool_iters
        model = self.config["deep_think_llm"] if deep else self.config["quick_think_llm"]
        provider = self.config["llm_provider"]
        backend_url = self.config.get("backend_url")

        # Build the Datapizza client (multi-provider)
        self._client = _create_datapizza_client(provider, model, backend_url)

    def generate(
        self,
        system_prompt: str,
        context: str,
        schema: type[BaseModel],
        *,
        tools: Sequence[Any] = (),
        recorder=None,
    ) -> BaseModel:
        """Generate a structured response, optionally with tool calling.

        When *tools* are provided, the Datapizza Agent runs a tool-calling loop:
        the model decides which tools to call, we execute them, feed results back,
        and repeat until the model produces the structured output.
        """
        from datapizza.agents import Agent

        agent = Agent(
            name="brain_agent",
            client=self._client,
            system_prompt=system_prompt,
            tools=list(tools),
            output_cls=schema,
            max_steps=self.max_tool_iters + 1,
        )

        result = agent.run(context)

        # Extract tool records from the agent's last step for the recorder
        if recorder is not None and result is not None:
            # Datapizza Agent doesn't expose per-tool records the same way
            # LangChain did, so we record at the tool level in datapizza_tools
            pass

        if result is None:
            # Fallback: return a default instance of the schema
            return schema()

        # result is already the structured output (Pydantic model)
        if isinstance(result, BaseModel):
            return result

        # If result is a StepResult, extract the output
        if hasattr(result, "output"):
            output = result.output
            if isinstance(output, BaseModel):
                return output

        return schema()


def _create_datapizza_client(provider: str, model: str, backend_url: Optional[str] = None):
    """Factory: create the right Datapizza client for the provider."""
    if provider == "ollama":
        from datapizza.clients.ollama import OllamaClient
        kwargs: dict[str, Any] = {"model": model}
        if backend_url:
            kwargs["base_url"] = backend_url
        return OllamaClient(**kwargs)
    elif provider == "google" or provider == "vertexai":
        from datapizza.clients.google import GoogleClient
        return GoogleClient(model=model)
    else:
        # Default: OpenAI-compatible (OpenAI, OpenRouter, DeepSeek, xAI, ...)
        from datapizza.clients.openai import OpenAIClient
        import os
        kwargs: dict[str, Any] = {"model": model}
        if backend_url:
            kwargs["base_url"] = backend_url
        # API key from env (same pattern as before)
        api_key = os.environ.get("OPENAI_API_KEY", "")
        kwargs["api_key"] = api_key
        return OpenAIClient(**kwargs)
