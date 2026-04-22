"""Deal Intelligence Agent — RAG + financial calculation tools via function calling.

Adapted for the unified serving endpoint. The agent is invoked via
`run()` which is synchronous (wrapped in asyncio.to_thread by the service).
`run_stream()` provides an async generator for SSE streaming.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import httpx
import yaml

from settings import get_settings
from tools.calculate_tool import calculate, describe_formulas, list_formulas
from tools.vector_search_tool import vector_search
from utils.logger import logger

# ---------------------------------------------------------------------------
# Load prompts from YAML
# ---------------------------------------------------------------------------
_DEAL_PROMPTS_PATH = Path(__file__).parent.parent / "resources" / "deal_prompts.yaml"


def _load_deal_prompts() -> dict[str, Any]:
    with _DEAL_PROMPTS_PATH.open() as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# System prompts by analyst_type (fallback if YAML scenario not found)
# ---------------------------------------------------------------------------
_FALLBACK_PROMPTS: dict[str, str] = {
    "buy_side": "You are a buy-side equity research analyst. Analyze documents to answer the user's question.",
    "sell_side": "You are a sell-side equity research analyst. Provide detailed analysis for institutional clients.",
    "credit": "You are a credit analyst specializing in fixed income. Analyze creditworthiness and leverage. Use the calculate tool for ratios.",
    "dcm": "You are a DCM analyst. Evaluate issuer creditworthiness and debt service capacity. Use the calculate tool for metrics.",
    "private_markets": "You are a private markets analyst conducting due diligence. Use the calculate tool for metrics.",
}

_PROMPT_SUFFIX = (
    "\n\nRESPONSE LENGTH GUIDELINE:"
    "\n- For simple or direct questions, keep your response under 300 words."
    "\n- For moderate analysis, keep your response under 600 words."
    "\n- Only produce detailed, multi-section responses for complex questions that explicitly ask for comprehensive analysis."
    "\n- Never pad your response with unnecessary detail just to be thorough."
    "\n\nRESPONSE CONTRACT — Your response will be parsed into this JSON structure:"
    "\n{"
    '\n  "content": "<your main analysis — everything not in the markers below>",'
    '\n  "analyst_type": "<provided by system, do not include>",'
    '\n  "confidence_level": "high|medium|low",'
    '\n  "confidence_reason": "<one sentence explaining your confidence level>",'
    '\n  "assumptions": ["<assumption 1>", "<assumption 2>", ...],'
    '\n  "calculations": [{"title": "...", "steps": "...", "result": "..."}],'
    '\n  "suggested_questions": ["<question 1>", "<question 2>", ...],'
    '\n  "citations": "<provided by system from document search, do not include>",'
    '\n  "source_excerpts": "<provided by system from document search, do not include>"'
    "\n}"
    "\n\nYou are responsible for: content, confidence_level, confidence_reason, assumptions, calculations, and suggested_questions."
    "\nThe system fills in: analyst_type, citations, and source_excerpts."
    "\n\nCITATION RULES:"
    "\n- Each source in the context is labeled [Source 1], [Source 2], etc."
    "\n- When citing a source in your analysis, use the exact marker [Source X] where X is the source number."
    "\n- Do NOT write [Document Name, Page X] — always use [Source X]."
    "\n- The system will replace [Source X] with the human-readable document name and page number."
    "\n- Only cite sources you actually use. Do not list all sources."
    "\n- When multiple documents cover the same topic for different time periods, ALWAYS prefer the most recent document unless the user specifically asks about an older period."
    "\n\nTo produce this structure, you MUST end your response with these markers in order:"
    "\n\n1. If you performed ANY calculations (using the calculate tool or manually), include a section "
    "starting with the marker CALCULATIONS_JSON: followed by a JSON array. Each element must have:"
    '\n   - "title": a human-readable name for the calculation (e.g. "Gross Margin")'
    '\n   - "steps": a multi-line string showing labeled input values and the formula with substituted numbers and intermediate steps'
    '\n   - "result": a bold markdown formatted final answer (e.g. "**Gross Margin = 46.21%**")'
    "\n   Example:"
    "\n   CALCULATIONS_JSON: ["
    '\n     {"title": "Gross Margin", "steps": "Gross Profit    = $180,683\\nRevenue         = $391,035\\n\\nGross Margin = Gross Profit / Revenue\\nGross Margin = 180,683 / 391,035", "result": "**Gross Margin = 46.21%**"}'
    "\n   ]"
    "\n\n2. A section starting with the marker ASSUMPTIONS: followed by a JSON array of strings listing "
    "the key assumptions you made in your analysis. Example:"
    '\n   ASSUMPTIONS: ["Revenue growth assumes no major macro downturn", "Tax rate held constant at 21%"]'
    "\n\n3. A line in this exact format:"
    "\nCONFIDENCE: <high|medium|low>"
    "\nCONFIDENCE_REASON: <one sentence explaining why you chose that confidence level>"
    "\n\n4.**CRITICAL**: A section titled exactly '## Suggested Questions' containing 3-4 numbered follow-up questions the user could ask next."
    "\n\n5. A final line in this exact format:\nSESSION_TITLE: <a concise 3-6 word title summarizing this conversation topic>\n"
)

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "vector_search",
            "description": "Search uploaded documents for chunks relevant to a query.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query."}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": (
                "Compute a financial formula. Call with formula_name and an inputs object "
                "containing ALL required numeric inputs for that formula.\n"
                "ONLY call this tool when you have concrete numeric values from the documents or conversation. "
                "Do NOT call with empty or placeholder inputs. "
                "Do NOT pass zero for denominator inputs (e.g. revenue, ebitda, total_debt) — "
                "division by zero will cause an error.\n\n"
                "Available formulas and their EXACT required input keys:\n"
                + describe_formulas()
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "formula_name": {
                        "type": "string",
                        "description": "Exact formula name from the list above.",
                        "enum": list_formulas(),
                    },
                    "inputs": {
                        "type": "object",
                        "description": "Named numeric inputs for the formula. Keys must match the required inputs exactly.",
                        "additionalProperties": {"type": "number"},
                    },
                },
                "required": ["formula_name", "inputs"],
            },
        },
    },
]


class DealIntelligenceAgent:
    """LLM agent with RAG retrieval and financial calculation tools."""

    MAX_TOOL_ITERATIONS = 3

    def __init__(self) -> None:
        self._settings = get_settings()

    def _get_system_prompt(self, analyst_type: str, scenario_type: str) -> str:
        """Load system prompt from YAML, falling back to hardcoded prompts."""
        try:
            prompts = _load_deal_prompts()
            prompt = prompts.get(analyst_type, {}).get(scenario_type, {})
            if isinstance(prompt, str):
                logger.info(
                    "Prompt selected from YAML: analyst_type=%s, scenario_type=%s",
                    analyst_type, scenario_type,
                )
                return prompt + _PROMPT_SUFFIX
            else:
                logger.warning(
                    "No YAML prompt matched for analyst_type=%s, scenario_type=%s (got type=%s)",
                    analyst_type, scenario_type, type(prompt).__name__,
                )
        except Exception as e:
            logger.warning("Failed to load deal prompts YAML: %s", str(e))
        base = _FALLBACK_PROMPTS.get(analyst_type, _FALLBACK_PROMPTS["buy_side"])
        logger.info(
            "Using fallback prompt: analyst_type=%s (resolved key=%s)",
            analyst_type, analyst_type if analyst_type in _FALLBACK_PROMPTS else "buy_side",
        )
        return base + _PROMPT_SUFFIX

    def run(
        self,
        user_query: str,
        chat_id: str,
        analyst_type: str,
        scenario_type: str,
        conversation_history: list[dict] | None = None,
        session_id: str | None = None,
    ) -> dict:
        """Execute the agent pipeline synchronously."""
        logger.info(
            "DealAgent.run raw payload:\n%s",
            json.dumps({
                "user_query": user_query,
                "chat_id": chat_id,
                "analyst_type": analyst_type,
                "scenario_type": scenario_type,
                "conversation_history": conversation_history,
                "session_id": session_id,
            }, indent=2, default=str),
        )

        # Fetch conversation history from DB if not provided
        if not conversation_history and session_id:
            try:
                logger.info("No conversation_history provided, fetching from DB for session %s", session_id)
                from repositories.databricks_repository import DatabricksRepository
                db_repo = DatabricksRepository()
                conversation_history = db_repo.fetch_conversation_history_sync(session_id, limit=6)
                logger.info("Fetched %d history messages from DB for session %s", len(conversation_history), session_id)
                db_repo.close()
            except Exception as e:
                logger.warning("Failed to fetch conversation history from DB: %s", str(e))
                conversation_history = None
        elif conversation_history:
            logger.info("Using %d conversation_history messages passed by caller", len(conversation_history))
        else:
            logger.info("No conversation_history and no session_id — proceeding without history")

        system_prompt = self._get_system_prompt(analyst_type, scenario_type)
        system_prompt += f"\n\nScenario: {scenario_type}"

        try:
            initial_chunks = vector_search(query=user_query, chat_id=chat_id)
        except Exception as e:
            logger.warning("Vector search failed — proceeding without RAG context", extra={"error": str(e)})
            initial_chunks = []
        context_text = self._format_chunks(initial_chunks)

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for msg in conversation_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({
            "role": "user",
            "content": f"Context from uploaded documents:\n\n{context_text}\n\nUser Question: {user_query}",
        })

        all_calculations: list[dict] = []
        all_citations: list[dict] = self._extract_chunk_citations(initial_chunks, start_index=1)

        for _ in range(self.MAX_TOOL_ITERATIONS):
            response = self._call_llm(messages, use_tools=True)
            message = response["choices"][0]["message"]
            if not message.get("tool_calls"):
                break
            messages.append(message)
            for tool_call in message["tool_calls"]:
                tool_result = self._execute_tool(tool_call, chat_id)
                if tool_call["function"]["name"] == "calculate" and isinstance(tool_result, dict):
                    all_calculations.append(tool_result)
                elif tool_call["function"]["name"] == "vector_search" and isinstance(tool_result, list):
                    next_index = len(all_citations) + 1
                    all_citations.extend(self._extract_chunk_citations(tool_result, start_index=next_index))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result,
                })
        else:
            response = self._call_llm(messages, use_tools=False)
            message = response["choices"][0]["message"]

        content = message.get("content", "") or ""
        logger.info("DealAgent raw LLM content:\n%s", content)
        result = self._parse_response(content, all_calculations, all_citations, analyst_type=analyst_type)
        logger.info("DealAgent parsed result:\n%s", json.dumps(result, indent=2, default=str))
        return result

    def _get_auth_token(self) -> str:
        """Get auth token — PAT if available, otherwise OAuth."""
        from utils.auth import get_auth_token
        return get_auth_token()

    def _call_llm(self, messages: list[dict], use_tools: bool = True) -> dict:
        host = self._settings.databricks_host.rstrip("/")
        url = f"{host}/serving-endpoints/{self._settings.llm_endpoint_sonnet}/invocations"
        headers = {
            "Authorization": f"Bearer {self._get_auth_token()}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {"messages": messages, "max_tokens": self._settings.llm_max_tokens}
        if use_tools:
            payload["tools"] = TOOL_DEFINITIONS
        response = httpx.post(url, json=payload, headers=headers, timeout=120.0)
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Streaming variants
    # ------------------------------------------------------------------

    async def _call_llm_stream(
        self, messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        """Call the LLM with stream=true and yield content delta strings."""
        host = self._settings.databricks_host.rstrip("/")
        url = f"{host}/serving-endpoints/{self._settings.llm_endpoint_sonnet}/invocations"
        headers = {
            "Authorization": f"Bearer {self._get_auth_token()}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "messages": messages,
            "max_tokens": self._settings.llm_max_tokens,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = (
                            chunk.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content")
                        )
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, IndexError):
                        continue

    async def run_stream(
        self,
        user_query: str,
        chat_id: str,
        analyst_type: str,
        scenario_type: str,
        conversation_history: list[dict] | None = None,
        session_id: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Execute the agent pipeline and yield SSE event dicts.

        Event types:
          {"type": "status", "content": "..."}   — progress updates
          {"type": "delta",  "content": "..."}   — streamed LLM tokens
          {"type": "done",   "metadata": {...}}  — final structured result
          {"type": "error",  "content": "..."}   — error message
        """
        import asyncio

        logger.info("DealAgent.run_stream started for chat_id=%s", chat_id)

        # --- Fetch conversation history (sync, run in thread) ---
        if not conversation_history and session_id:
            try:
                from repositories.databricks_repository import DatabricksRepository
                db_repo = DatabricksRepository()
                conversation_history = await asyncio.to_thread(
                    db_repo.fetch_conversation_history_sync, session_id, 6,
                )
                db_repo.close()
            except Exception as e:
                logger.warning("Failed to fetch conversation history: %s", str(e))
                conversation_history = None

        system_prompt = self._get_system_prompt(analyst_type, scenario_type)
        system_prompt += f"\n\nScenario: {scenario_type}"

        # --- Vector search (sync, run in thread) ---
        yield {"type": "status", "content": "Searching documents..."}
        try:
            initial_chunks = await asyncio.to_thread(
                vector_search, query=user_query, chat_id=chat_id,
            )
        except Exception as e:
            logger.warning("Vector search failed: %s", str(e))
            initial_chunks = []
        context_text = self._format_chunks(initial_chunks)

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for msg in conversation_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({
            "role": "user",
            "content": f"Context from uploaded documents:\n\n{context_text}\n\nUser Question: {user_query}",
        })

        all_calculations: list[dict] = []
        all_citations: list[dict] = self._extract_chunk_citations(initial_chunks, start_index=1)

        # --- Stream the response directly (no tool-calling loop) ---
        yield {"type": "status", "content": "Generating analysis..."}
        accumulated = ""
        try:
            async for delta in self._call_llm_stream(messages):
                accumulated += delta
                yield {"type": "delta", "content": delta}
        except Exception as e:
            logger.error("Streaming LLM call failed: %s", str(e))
            yield {"type": "error", "content": f"LLM streaming failed: {str(e)[:200]}"}
            return

        # --- Parse the accumulated response for metadata ---
        logger.info("DealAgent.run_stream accumulated %d chars", len(accumulated))
        result = self._parse_response(
            accumulated, all_calculations, all_citations, analyst_type=analyst_type,
        )
        yield {"type": "done", "metadata": result}

    def _execute_tool(self, tool_call: dict, chat_id: str) -> Any:
        name = tool_call["function"]["name"]
        args = json.loads(tool_call["function"]["arguments"])
        if name == "vector_search":
            return vector_search(query=args["query"], chat_id=chat_id)
        elif name == "calculate":
            try:
                return calculate(formula_name=args["formula_name"], **args.get("inputs", {}))
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.warning("calculate tool error", extra={"error": str(e), "tool_args": args})
                return {"error": str(e)}
        return {"error": f"Unknown tool: {name}"}

    @staticmethod
    def _format_chunks(chunks: list[dict]) -> str:
        if not chunks:
            logger.info("_format_chunks: no chunks to format")
            return "No relevant document context found."
        parts: list[str] = []
        for i, chunk in enumerate(chunks, start=1):
            doc_name = chunk.get("short_name") or chunk.get("document_name") or chunk.get("document_id", "Unknown")
            page = chunk.get("page_number", "N/A")
            section = chunk.get("section_name", "")
            text = chunk.get("chunk_text", "")
            header = f"[Source {i}] {doc_name}, Page {page}"
            if section:
                header += f", Section: {section}"
            parts.append(f"{header}\n{text}")
        logger.info("_format_chunks: formatted %d chunks as [Source 1] to [Source %d]", len(chunks), len(chunks))
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _extract_chunk_citations(chunks: list[dict], start_index: int = 1) -> list[dict]:
        logger.info("_extract_chunk_citations: processing %d chunks starting at index %d", len(chunks), start_index)
        results = []
        for i, c in enumerate(chunks, start=start_index):
            doc_name = c.get("short_name") or c.get("document_name") or c.get("document_id", "Unknown")
            page = c.get("page_number", "N/A")
            label = f"{doc_name}, p.{page}"
            results.append({
                "source_index": i,
                "chunk_id": c.get("chunk_id"),
                "document_id": c.get("document_id"),
                "page_number": c.get("page_number"),
                "section_name": c.get("section_name"),
                "source_text": (c.get("chunk_text", ""))[:200],
                "label": label,
            })
        logger.info("_extract_chunk_citations: built %d citations with labels: %s",
                     len(results), [r["label"] for r in results])
        return results


    @staticmethod
    def _parse_response(content: str, calculations: list[dict], citations: list[dict], analyst_type: str | None = None) -> dict:
        session_title = None
        confidence_level = None
        confidence_reason = None
        parsed_assumptions: list[str] | None = None
        clean_lines: list[str] = []
        parsed_calculations: list[dict] | None = None

        # Extract multi-line CALCULATIONS_JSON block
        calc_json_lines: list[str] = []
        in_calc_block = False

        # Extract multi-line ASSUMPTIONS block
        assumptions_json_lines: list[str] = []
        in_assumptions_block = False

        for line in content.split("\n"):
            stripped = line.strip()
            upper = stripped.upper()
            if upper.startswith("SESSION_TITLE:"):
                session_title = stripped.split(":", 1)[1].strip()
            elif upper.startswith("CONFIDENCE_REASON:"):
                confidence_reason = stripped.split(":", 1)[1].strip()
            elif upper.startswith("CONFIDENCE:"):
                val = stripped.split(":", 1)[1].strip().lower()
                if val in ("high", "medium", "low"):
                    confidence_level = val
            elif upper.startswith("ASSUMPTIONS:"):
                in_assumptions_block = True
                remainder = stripped.split(":", 1)[1].strip()
                if remainder:
                    assumptions_json_lines.append(remainder)
            elif in_assumptions_block:
                assumptions_json_lines.append(line)
                joined = "\n".join(assumptions_json_lines).strip()
                try:
                    parsed_assumptions = json.loads(joined)
                    in_assumptions_block = False
                except json.JSONDecodeError:
                    pass
            elif upper.startswith("CALCULATIONS_JSON:"):
                in_calc_block = True
                remainder = stripped.split(":", 1)[1].strip()
                if remainder:
                    calc_json_lines.append(remainder)
            elif in_calc_block:
                calc_json_lines.append(line)
                joined = "\n".join(calc_json_lines).strip()
                try:
                    parsed_calculations = json.loads(joined)
                    in_calc_block = False
                except json.JSONDecodeError:
                    pass
            else:
                clean_lines.append(line)

        # Try parsing if we exited the loop still in a block
        if in_calc_block and calc_json_lines and parsed_calculations is None:
            try:
                parsed_calculations = json.loads("\n".join(calc_json_lines).strip())
            except json.JSONDecodeError:
                logger.warning("Failed to parse CALCULATIONS_JSON from LLM response")

        if in_assumptions_block and assumptions_json_lines and parsed_assumptions is None:
            try:
                parsed_assumptions = json.loads("\n".join(assumptions_json_lines).strip())
            except json.JSONDecodeError:
                logger.warning("Failed to parse ASSUMPTIONS from LLM response")

        content = "\n".join(clean_lines).strip()

        # Fallback: scan content for confidence if marker wasn't found
        if confidence_level is None:
            for level in ("high", "medium", "low"):
                if f"confidence: {level}" in content.lower() or f"confidence level: {level}" in content.lower():
                    confidence_level = level
                    break

        suggested_questions: list[str] = []
        lines = content.split("\n")
        in_questions = False
        for line in lines:
            stripped = line.strip()
            lower = stripped.lower()
            # Detect question section headers (various formats the LLM might use)
            if any(kw in lower for kw in (
                "follow-up question", "suggested question",
                "## suggested questions", "## follow-up questions",
                "### suggested questions", "### follow-up questions",
                "suggested questions:", "follow-up questions:",
            )):
                in_questions = True
                continue
            if in_questions and stripped:
                cleaned = stripped.lstrip("0123456789.-) *").strip()
                if cleaned and cleaned.endswith("?"):
                    suggested_questions.append(cleaned)
                elif not cleaned:
                    in_questions = False

        # Fallback: if no section header was found, scan for any numbered
        # question lines (e.g. "1. What is ...?") anywhere in the response.
        if not suggested_questions:
            import re
            for line in lines:
                m = re.match(r"^\s*\d+[\.\)]\s+(.+\?)\s*$", line)
                if m:
                    candidate = m.group(1).strip()
                    # Only collect lines that look like genuine questions
                    if len(candidate) > 15:
                        suggested_questions.append(candidate)

        # --- Citation linking: replace [Source X] with [label] and filter ---
        import re as _re

        # Build lookup: source_index -> citation dict
        citation_lookup: dict[int, dict] = {}
        for c in citations:
            idx = c.get("source_index")
            if idx is not None:
                citation_lookup[idx] = c
        logger.info("Citation linking: %d total citations available, indices: %s",
                     len(citation_lookup), sorted(citation_lookup.keys()))

        # Find all [Source X] references in content
        used_indices: set[int] = set()
        for m in _re.finditer(r'\[Source\s+(\d+)\]', content):
            used_indices.add(int(m.group(1)))
        logger.info("Citation linking: LLM referenced %d sources: %s", len(used_indices), sorted(used_indices))

        # Check for any references that don't match available citations
        missing = used_indices - set(citation_lookup.keys())
        if missing:
            logger.warning("Citation linking: LLM referenced non-existent sources: %s", sorted(missing))

        # Replace [Source X] with [label] for human-readable inline citations
        def _replace_source_ref(m: _re.Match) -> str:
            idx = int(m.group(1))
            cit = citation_lookup.get(idx)
            if cit and cit.get("label"):
                return f"[{cit['label']}]"
            return m.group(0)  # keep original if no match

        content = _re.sub(r'\[Source\s+(\d+)\]', _replace_source_ref, content)

        # Filter citations to only the ones actually referenced
        used_citations = []
        for idx in sorted(used_indices):
            cit = citation_lookup.get(idx)
            if cit:
                # Remove internal source_index from the output
                out = {k: v for k, v in cit.items() if k != "source_index"}
                used_citations.append(out)
        logger.info("Citation linking: filtered to %d used citations (from %d total)",
                     len(used_citations), len(citations))

        # Build source_excerpts from used citations only
        source_excerpts = [
            {
                "document_id": c.get("document_id"),
                "page_number": c.get("page_number"),
                "text": c.get("source_text"),
            }
            for c in used_citations
            if c.get("source_text")
        ] or None

        return {
            "analyst_type": analyst_type,
            "content": content,
            "confidence_level": confidence_level,
            "confidence_reason": confidence_reason,
            "assumptions": parsed_assumptions,
            "calculations": parsed_calculations,
            "suggested_questions": suggested_questions or None,
            "citations": used_citations if used_citations else None,
            "source_excerpts": source_excerpts,
            "session_title": session_title,
        }
