"""RTQ Intelligence Agent — LangGraph ReAct implementation.

Adapted for the unified serving endpoint. Uses Genie MCP tool for
data retrieval and LangGraph for the ReAct loop.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, TypedDict

import yaml
from jinja2 import BaseLoader, Environment
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool as lc_tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from models.rtq_models import (
    RFQAgentRequest,
    RFQAgentResponse,
    AgentResponseEnvelope,
    AgentResponsePayload,
    MetadataResource,
    ToolCallLog,
)
from repositories.genie_repository import GenieRepository
from settings import PERSONA_SIMULATION_MAP, PROMPT_VERSION, VALID_PERSONAS, get_settings
from utils.exceptions import (
    ERR_INVALID_PERSONA, ERR_INVALID_SIMULATION, ERR_METADATA_LOAD,
    GuardrailViolationError, InvalidPersonaError, InvalidSimulationError, MetadataLoadError,
)
from utils.logger import logger

_PROMPTS_PATH = Path(__file__).parent.parent / "resources" / "rtq_prompts.yaml"
_METADATA_PATH = Path(__file__).parent.parent / "resources" / "metadata.yaml"
_jinja_env = Environment(loader=BaseLoader(), autoescape=False)  # noqa: S701
_UC_TABLES = frozenset({"wallet_share_snapshots", "trace_data", "bonds", "firms", "rfq_trades"})


@lru_cache(maxsize=1)
def _load_prompts() -> dict[str, Any]:
    try:
        with _PROMPTS_PATH.open() as fh:
            return yaml.safe_load(fh)
    except Exception as exc:
        raise MetadataLoadError(f"Failed to load rtq_prompts.yaml: {exc}", error_code=ERR_METADATA_LOAD) from exc


@lru_cache(maxsize=1)
def _load_tool_rules() -> str:
    return _load_prompts().get("tool_rules", "")


@lru_cache(maxsize=1)
def _load_genie_tool_description() -> str:
    return _load_prompts().get("genie_tool_description", "Query Databricks Genie MCP.")


@lru_cache(maxsize=1)
def _load_metadata_context_template() -> str:
    return _load_prompts().get("metadata_context_template", "## Available UC Tables\n{tables_json}\n\n## UC Metrics Formulas\n{formula_lines}")


@lru_cache(maxsize=1)
def _load_human_input_template() -> str:
    return _load_prompts().get("human_input_template", "trader_id: {trader_id}\nrequest: {user_message}")


@lru_cache(maxsize=1)
def _load_output_format_instruction() -> str:
    return _load_prompts().get("output_format_instruction", "")


@lru_cache(maxsize=1)
def _load_static_tables() -> dict[str, Any]:
    try:
        with _METADATA_PATH.open() as fh:
            raw = yaml.safe_load(fh) or {}
        return raw.get("tables", {})
    except Exception as exc:
        raise MetadataLoadError(f"Failed to load metadata.yaml: {exc}", error_code=ERR_METADATA_LOAD) from exc


# Guardrails
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"disregard\s+(your\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if\s+you\s+are\s+)?a\s+different", re.IGNORECASE),
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
]
_MIN_MSG_LEN = 3
_MAX_MSG_LEN = 4000


def _validate_input(user_message: str) -> None:
    if len(user_message.strip()) < _MIN_MSG_LEN:
        raise GuardrailViolationError("User message is too short.")
    if len(user_message) > _MAX_MSG_LEN:
        raise GuardrailViolationError(f"User message exceeds {_MAX_MSG_LEN} characters.")
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(user_message):
            raise GuardrailViolationError("Message contains disallowed content.")


def _extract_json(text: str) -> str:
    """Extract the outermost JSON object from LLM output.

    Handles: markdown fences, preamble/postamble prose, balanced and
    unbalanced (truncated) braces.
    """
    s = text.strip()
    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    if s.startswith("```"):
        s = s.split("\n", 1)[-1] if "\n" in s else s[3:]
    if s.endswith("```"):
        s = s.rsplit("```", 1)[0]
    s = s.strip()

    # Find the first '{' — start of JSON
    start = s.find("{")
    if start == -1:
        return s

    # Walk forward with brace-depth counting, respecting strings
    depth = 0
    in_string = False
    escape = False
    end = -1
    for i in range(start, len(s)):
        ch = s[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    if end != -1:
        return s[start: end + 1]

    # JSON is truncated (no matching close brace) — return from start
    # to end of string; caller will repair missing brackets.
    return s[start:]


def _repair_truncated_json(s: str) -> str:
    """Best-effort repair of truncated JSON by closing open brackets/braces.

    Walks the string tracking open delimiters outside of strings, then
    appends the missing closing characters in reverse order.  Also
    handles unterminated strings and trailing commas.
    """
    stack: list[str] = []
    in_string = False
    escape = False
    last_non_ws = ""

    for ch in s:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ("{", "["):
            stack.append("}" if ch == "{" else "]")
        elif ch in ("}", "]"):
            if stack and stack[-1] == ch:
                stack.pop()
        if ch.strip():
            last_non_ws = ch

    repaired = s
    # If we're inside an unterminated string, close it
    if in_string:
        repaired += '"'
    # Remove trailing comma before we close brackets
    repaired = repaired.rstrip()
    if repaired.endswith(","):
        repaired = repaired[:-1]
    # Close all open brackets/braces in reverse order
    repaired += "".join(reversed(stack))
    return repaired


def _try_json_loads(s: str, trace_id: str, label: str) -> dict | None:
    """Attempt json.loads; return parsed dict or None."""
    try:
        data = json.loads(s)
        if isinstance(data, dict):
            logger.info(f"JSON parsed successfully ({label})", extra={"trace_id": trace_id})
            return data
        logger.warning(f"JSON parsed but not a dict ({label})", extra={
            "trace_id": trace_id, "type": type(data).__name__,
        })
    except json.JSONDecodeError as exc:
        logger.warning(f"JSON decode failed ({label})", extra={
            "trace_id": trace_id,
            "error": str(exc),
            "preview": s[:300],
        })
    return None


def _validate_parsed_data(data: dict, trace_id: str) -> AgentResponsePayload:
    """Validate a parsed dict into AgentResponsePayload.

    Tries envelope shape, direct payload shape, and finally manual
    extraction as a last resort so we never lose data.
    """
    # Shape 1: {"agent_response": {...}}
    if "agent_response" in data:
        try:
            payload = AgentResponseEnvelope.model_validate(data).agent_response
            logger.info("Validated as envelope", extra={
                "trace_id": trace_id, "confidence": payload.confidence,
            })
            return payload
        except Exception as exc:
            logger.warning("Envelope validation failed, trying inner dict", extra={
                "trace_id": trace_id, "error": str(exc),
            })
            # Try validating just the inner dict
            inner = data["agent_response"]
            if isinstance(inner, dict):
                try:
                    payload = AgentResponsePayload.model_validate(inner)
                    logger.info("Validated inner agent_response directly", extra={
                        "trace_id": trace_id, "confidence": payload.confidence,
                    })
                    return payload
                except Exception:
                    pass

    # Shape 2: {"response_message": ..., "confidence": ...}
    if "response_message" in data:
        try:
            payload = AgentResponsePayload.model_validate(data)
            logger.info("Validated as direct payload", extra={
                "trace_id": trace_id, "confidence": payload.confidence,
            })
            return payload
        except Exception as exc:
            logger.warning("Direct payload validation failed", extra={
                "trace_id": trace_id, "error": str(exc),
            })

    # Shape 3: manual extraction — pull whatever fields exist
    logger.warning("Falling back to manual field extraction", extra={
        "trace_id": trace_id, "top_keys": list(data.keys())[:10],
    })
    # Dig into agent_response if it exists but failed validation
    src = data.get("agent_response", data) if isinstance(data.get("agent_response"), dict) else data
    return AgentResponsePayload(
        response_message=src.get("response_message", json.dumps(src, default=str)[:3000]),
        confidence=int(src.get("confidence", 40)),
        panels=None,
        sources=None,
        recommendations=src.get("recommendations", ["Response was partially parsed. Some data may be missing."]),
        recommended_questions=src.get("recommended_questions", []),
    )


class RTQGraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    request: RFQAgentRequest
    trace_id: str
    metadata: MetadataResource | None
    tool_logs: list[ToolCallLog]
    total_input_tokens: int
    total_output_tokens: int
    iteration: int
    queried_tables: list[str]


class RTQAgent:
    """RTQ Intelligence Agent built on LangGraph ReAct pattern."""

    def __init__(self, genie_repo: GenieRepository | None = None) -> None:
        self._settings = get_settings()
        self._genie_repo = genie_repo or GenieRepository()
        self._llm = ChatOpenAI(
            model=self._settings.llm_model_name,
            openai_api_base=f"{self._settings.llm_endpoint_url}/",
            openai_api_key=self._settings.databricks_token,
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
            timeout=self._settings.llm_timeout,
            max_retries=2,
        )
        self._graph = self._build_graph()

    async def run(self, request: RFQAgentRequest) -> RFQAgentResponse:
        trace_id = str(uuid.uuid4())
        logger.info("RTQAgent.run started", extra={
            "session_id": request.session_id, "conversation_id": request.conversation_id,
            "persona": request.persona, "simulation": request.simulation, "trace_id": trace_id,
        })

        _validate_input(request.user_message)
        if request.persona not in VALID_PERSONAS:
            raise InvalidPersonaError(f"Unknown persona '{request.persona}'", error_code=ERR_INVALID_PERSONA)
        valid_sims = PERSONA_SIMULATION_MAP.get(request.persona, set())
        if request.simulation not in valid_sims:
            logger.info("Simulation '%s' not found for '%s', falling back to default",
                        request.simulation, request.persona,
                        extra={"trace_id": trace_id})
            request = request.model_copy(update={"simulation": "default"})

        initial_state: RTQGraphState = {
            "messages": [], "request": request, "trace_id": trace_id,
            "metadata": None, "tool_logs": [], "total_input_tokens": 0,
            "total_output_tokens": 0, "iteration": 0, "queried_tables": [],
        }
        config = {"configurable": {"thread_id": request.session_id}}
        final_state: RTQGraphState = await self._graph.ainvoke(initial_state, config=config)

        raw_content = ""
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                raw_content = str(msg.content).strip()
                break

        # If the last AIMessage has tool_calls with AgentResponseEnvelope args,
        # use those directly — they're already validated by the tool strategy.
        payload = None
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage):
                tc = getattr(msg, "tool_calls", None) or []
                for call in tc:
                    args = call.get("args", {})
                    if "agent_response" in args:
                        try:
                            envelope = AgentResponseEnvelope.model_validate(args)
                            payload = envelope.agent_response
                            logger.info("Extracted payload from tool call args", extra={
                                "trace_id": trace_id, "confidence": payload.confidence,
                            })
                        except Exception:
                            pass
                    break
                break

        logger.info("Raw LLM response extracted", extra={
            "trace_id": trace_id,
            "raw_content_length": len(raw_content),
            "has_content": bool(raw_content),
            "payload_from_tool_call": payload is not None,
            "iterations": final_state["iteration"],
        })

        if payload is None:
            payload = self._parse_response(raw_content, trace_id)

        logger.info("RTQAgent.run completed", extra={
            "trace_id": trace_id,
            "input_tokens": final_state["total_input_tokens"],
            "output_tokens": final_state["total_output_tokens"],
            "iterations": final_state["iteration"],
            "confidence": payload.confidence,
        })

        return RFQAgentResponse(
            conversation_id=request.conversation_id, session_id=request.session_id,
            persona=request.persona, simulation=request.simulation,
            agent_response=payload,
            total_input_tokens=final_state["total_input_tokens"],
            total_output_tokens=final_state["total_output_tokens"],
            tool_logs=final_state["tool_logs"], prompt_version=PROMPT_VERSION,
        )

    def _build_graph(self) -> Any:
        genie_repo = self._genie_repo
        _tool_desc = _load_genie_tool_description().strip()

        @lc_tool(description=_tool_desc)
        async def genie_query(query: str) -> str:
            try:
                rows = await genie_repo.query(query)
                return json.dumps(rows) if rows else json.dumps({"info": "No data returned."})
            except Exception as exc:
                return json.dumps({"error": str(exc)})

        tools = [genie_query]
        llm_with_tools = self._llm.bind_tools(tools)
        # For final synthesis: bind the response schema as a tool and force
        # the LLM to "call" it.  Databricks Model Serving supports tool
        # calling for Llama, so the response comes back as validated
        # structured arguments — no free-form text parsing needed.
        llm_final = self._llm.bind_tools(
            [AgentResponseEnvelope],
            tool_choice="AgentResponseEnvelope",
        )

        async def load_metadata(state: RTQGraphState) -> dict[str, Any]:
            request = state["request"]
            trace_id = state["trace_id"]
            tables = await asyncio.to_thread(_load_static_tables)
            metadata = MetadataResource(tables=tables, formulas={})
            prompts = _load_prompts()
            persona_prompts = prompts.get(request.persona, {})
            sim_prompt = persona_prompts.get(request.simulation) or persona_prompts.get("default")
            persona_prompt: str = sim_prompt["system"]
            tool_rules: str = _load_tool_rules()
            metadata_ctx_tmpl: str = _load_metadata_context_template()
            human_input_tmpl: str = _load_human_input_template()
            output_format: str = _load_output_format_instruction()
            formula_lines = "(formulas loaded live from UC Metrics Volume via Genie)"
            metadata_context = metadata_ctx_tmpl.format(
                tables_json=json.dumps(list(tables.keys())), formula_lines=formula_lines,
            )
            system_prompt = f"{persona_prompt}\n\n{tool_rules}\n\n{metadata_context}\n\n{output_format}"
            human_input = human_input_tmpl.format(trader_id=request.user_id, user_message=request.user_message)

            # Build message list: system → conversation history → current user message
            messages: list[SystemMessage | HumanMessage | AIMessage] = [SystemMessage(content=system_prompt)]
            for turn in request.conversation_history:
                if turn.get("user_message"):
                    messages.append(HumanMessage(content=turn["user_message"]))
                if turn.get("agent_response"):
                    messages.append(AIMessage(content=turn["agent_response"]))
            messages.append(HumanMessage(content=human_input))

            return {
                "metadata": metadata,
                "messages": messages,
            }

        async def call_model(state: RTQGraphState) -> dict[str, Any]:
            queried = set(state["queried_tables"])
            all_done = queried >= _UC_TABLES
            iteration = state["iteration"] + 1
            max_iter = self._settings.max_agent_iterations
            force_stop = all_done or iteration >= max_iter
            start = time.monotonic()

            if force_stop:
                logger.info("call_model using tool-strategy for structured output", extra={
                    "iteration": iteration, "queried_tables": list(queried),
                })
                synthesis_messages = list(state["messages"]) + [
                    HumanMessage(content=(
                        "Now synthesise all the data above into your final response. "
                        "You MUST call the AgentResponseEnvelope tool with your complete analysis."
                    ))
                ]
                try:
                    last_err = None
                    for attempt in range(1, 3):
                        try:
                            response: AIMessage = await llm_final.ainvoke(synthesis_messages)
                            break
                        except Exception as exc:
                            last_err = exc
                            logger.warning("llm_final call failed, retrying", extra={
                                "iteration": iteration, "attempt": attempt,
                                "error": str(exc)[:200],
                            })
                            await asyncio.sleep(2)
                    else:
                        raise last_err  # type: ignore[misc]

                    input_tokens = output_tokens = 0
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        input_tokens = response.usage_metadata.get("input_tokens", 0)
                        output_tokens = response.usage_metadata.get("output_tokens", 0)

                    # Extract structured args from the tool call
                    tool_calls = getattr(response, "tool_calls", None) or []
                    if tool_calls:
                        args = tool_calls[0].get("args", {})
                        envelope = AgentResponseEnvelope.model_validate(args)
                        logger.info("Structured output via tool call succeeded", extra={
                            "iteration": iteration,
                            "confidence": envelope.agent_response.confidence,
                        })
                        return {
                            "messages": [AIMessage(content=envelope.model_dump_json())],
                            "iteration": iteration,
                            "total_input_tokens": state["total_input_tokens"] + input_tokens,
                            "total_output_tokens": state["total_output_tokens"] + output_tokens,
                        }

                    # LLM didn't produce a tool call — fall through to use
                    # raw content (the parse_response fallback will handle it)
                    logger.warning("LLM did not produce a tool call on force_stop", extra={
                        "iteration": iteration,
                        "has_content": bool(response.content),
                    })
                    return {
                        "messages": [response],
                        "iteration": iteration,
                        "total_input_tokens": state["total_input_tokens"] + input_tokens,
                        "total_output_tokens": state["total_output_tokens"] + output_tokens,
                    }
                except Exception as exc:
                    logger.warning("Tool-strategy structured output failed, falling back to plain LLM", extra={
                        "iteration": iteration, "error": str(exc)[:200],
                    })
                    # Fallback: plain LLM call with retry
                    last_err = None
                    for attempt in range(1, 3):
                        try:
                            response = await self._llm.ainvoke(synthesis_messages)
                            break
                        except Exception as retry_exc:
                            last_err = retry_exc
                            logger.warning("Plain LLM fallback failed, retrying", extra={
                                "iteration": iteration, "attempt": attempt,
                                "error": str(retry_exc)[:200],
                            })
                            await asyncio.sleep(2)
                    else:
                        raise last_err  # type: ignore[misc]

                    input_tokens = output_tokens = 0
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        input_tokens = response.usage_metadata.get("input_tokens", 0)
                        output_tokens = response.usage_metadata.get("output_tokens", 0)
                    return {
                        "messages": [response],
                        "iteration": iteration,
                        "total_input_tokens": state["total_input_tokens"] + input_tokens,
                        "total_output_tokens": state["total_output_tokens"] + output_tokens,
                    }

            logger.info("call_model using tool-calling LLM", extra={
                "iteration": iteration, "queried_tables": list(queried),
            })
            last_err = None
            for attempt in range(1, 3):  # up to 2 attempts
                try:
                    response: AIMessage = await llm_with_tools.ainvoke(state["messages"])
                    break
                except Exception as exc:
                    last_err = exc
                    logger.warning("LLM call failed, retrying", extra={
                        "iteration": iteration, "attempt": attempt,
                        "error": str(exc)[:200],
                    })
                    await asyncio.sleep(2)
            else:
                raise last_err  # type: ignore[misc]

            input_tokens = output_tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                input_tokens = response.usage_metadata.get("input_tokens", 0)
                output_tokens = response.usage_metadata.get("output_tokens", 0)
            return {
                "messages": [response], "iteration": iteration,
                "total_input_tokens": state["total_input_tokens"] + input_tokens,
                "total_output_tokens": state["total_output_tokens"] + output_tokens,
            }

        async def call_tools(state: RTQGraphState) -> dict[str, Any]:
            last_ai: AIMessage = next(m for m in reversed(state["messages"]) if isinstance(m, AIMessage))
            tool_calls = getattr(last_ai, "tool_calls", []) or []
            queried = list(state["queried_tables"])
            new_tool_logs = list(state["tool_logs"])
            tool_messages: list[ToolMessage] = []

            def _extract_table(query: str) -> str | None:
                q = query.lower()
                for tbl in _UC_TABLES:
                    if tbl.replace("_", " ") in q or tbl in q:
                        return tbl
                return None

            for i, tc in enumerate(tool_calls):
                if i > 0:
                    await asyncio.sleep(0.5)
                fn_name = tc.get("name", "")
                args = tc.get("args", {})
                call_id = tc.get("id", str(uuid.uuid4()))
                query = args.get("query", "") if isinstance(args, dict) else ""
                table = _extract_table(query)

                if table and table in queried:
                    tool_messages.append(ToolMessage(
                        content=json.dumps({"info": f"Table '{table}' already queried."}),
                        tool_call_id=call_id,
                    ))
                    continue
                if table:
                    queried.append(table)

                start = time.monotonic()
                log = ToolCallLog(tool_name=fn_name, input_summary=str(args)[:200], output_summary="", duration_ms=0.0)
                try:
                    rows = await self._genie_repo.query(query)
                    content = json.dumps(rows) if rows else json.dumps({"info": "No data returned."})
                    log.output_summary = content[:200]
                    log.success = True
                except Exception as exc:
                    content = json.dumps({"error": str(exc)})
                    log.success = False
                    log.error_message = str(exc)
                finally:
                    log.duration_ms = round((time.monotonic() - start) * 1000, 2)
                    new_tool_logs.append(log)
                tool_messages.append(ToolMessage(content=content, tool_call_id=call_id))

            return {"messages": tool_messages, "queried_tables": queried, "tool_logs": new_tool_logs}

        def should_continue(state: RTQGraphState) -> str:
            last_ai = next((m for m in reversed(state["messages"]) if isinstance(m, AIMessage)), None)
            if last_ai is None:
                return END
            has_tool_calls = bool(getattr(last_ai, "tool_calls", None))
            queried = set(state["queried_tables"])
            if not has_tool_calls or queried >= _UC_TABLES or state["iteration"] >= self._settings.max_agent_iterations:
                return END
            return "call_tools"

        graph = StateGraph(RTQGraphState)
        graph.add_node("load_metadata", load_metadata)
        graph.add_node("call_model", call_model)
        graph.add_node("call_tools", call_tools)
        graph.set_entry_point("load_metadata")
        graph.add_edge("load_metadata", "call_model")
        graph.add_conditional_edges("call_model", should_continue, {"call_tools": "call_tools", END: END})
        graph.add_edge("call_tools", "call_model")
        return graph.compile()

    @staticmethod
    def _parse_response(raw_content: str, trace_id: str) -> AgentResponsePayload:
        """Parse the LLM's final response into AgentResponsePayload.

        Handles every known failure mode:
          1. Clean JSON envelope or direct payload
          2. Markdown-wrapped JSON
          3. Preamble/postamble prose around JSON
          4. Truncated JSON (missing ], }, or unterminated strings)
          5. Pydantic validation failures (missing optional fields)
          6. Completely unparseable output → extract what we can
        """
        logger.info("Parsing agent response", extra={
            "trace_id": trace_id,
            "raw_content_length": len(raw_content),
            "raw_content_preview": raw_content[:500],
        })

        if not raw_content.strip():
            logger.warning("Empty raw_content from LLM", extra={"trace_id": trace_id})
            return AgentResponsePayload(
                response_message="Analysis completed but the model returned an empty response — please retry.",
                confidence=20, recommendations=["Retry the request."],
            )

        json_str = _extract_json(raw_content)

        # --- Try parsing as-is first ---
        data = _try_json_loads(json_str, trace_id, "direct")

        # --- If that failed, repair truncated JSON and retry ---
        if data is None:
            repaired = _repair_truncated_json(json_str)
            data = _try_json_loads(repaired, trace_id, "repaired")

        # --- If still no valid dict, return raw LLM text as the response ---
        if not isinstance(data, dict):
            logger.warning("All JSON parse attempts failed — returning raw LLM output", extra={
                "trace_id": trace_id,
                "raw_content_tail": raw_content[-500:],
            })
            return AgentResponsePayload(
                response_message=raw_content,
                confidence=30,
                recommendations=["Response could not be structured. Raw agent output is shown above."],
            )

        # --- Validate into Pydantic models ---
        return _validate_parsed_data(data, trace_id)
