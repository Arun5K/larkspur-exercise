"""Larkspur disruption agent. This is the file you build.

It runs right now, and it is wrong in four places. The trace shows each one
before the code does, so read the trace first:

    python3 run.py K7PQ2M --trace

Where you edit:   grep -n '✏' agent.py   (six marks, one per place)
Steps and gates:  https://anthropicpartnerbasecamp.bts.com/
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Dict, List
from support import (MODEL, SYSTEM_PROMPT, call_local, execute_tool, mcp_client,
                     new_session, next_available_day, record_tool_result,
                     runtime_preamble)

MAX_TOOL_CALLS = 8  # Larkspur's own build capped the loop here; then a human takes over.

TONE_ADDENDUM = ""                       # ✏️ Build 4, step 4.1, intelligence goal
EXTRA_TOOLS: List[Dict[str, Any]] = [    # ✏️ Build 2, step 2.1: schemas for the tools you add
    {
        "name": "fare_rules",
        "description": (
            "Explains passenger entitlements under Larkspur's Handbook "
            "(fare_rules_excerpt.md). Use this tool when a customer asks why they are or "
            "are not receiving hotel accommodation or other assistance following a flight "
            "cancellation or disruption. It evaluates the relevant fare rules and explains "
            "the reason for eligibility or ineligibility. It does not issue vouchers, make "
            "bookings, or perform rebooking."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_code": {
                    "type": "string",
                    "description": "Customer's booking reference.",
                },
                "customer_question": {
                    "type": "string",
                    "description": "Customer's question about fare-rule entitlement.",
                },
                "passenger_count": {
                    "type": "integer",
                    "description": "Number of passengers affected.",
                },
                "disruption_type": {
                    "type": "string",
                    "description": "Type of flight disruption.",
                },
            },
            "required": ["booking_code", "customer_question"],
        },
    },
]
FARE_RULES_PATH = Path(__file__).parent / "data" / "americas" / "fare_rules_excerpt.md"
_STOPWORDS = {
    "the", "and", "for", "are", "was", "were", "our", "you", "your", "can", "get", "have",
    "does", "not", "why", "with", "this", "that", "from", "will", "while", "until", "there",
    "flight", "flights", "next", "available", "entitled", "stay", "three", "when", "what",
}


def fare_rules(booking_code: str = "", customer_question: str = "", passenger_count: Any = None,
               disruption_type: str = "", **_ignored: Any) -> Dict[str, Any]:
    """Look up the Handbook sections that answer the question. Text comes only from the
    file; if no section matches, say so rather than answer from memory."""
    try:
        text = FARE_RULES_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        return {"found": False, "error": f"Handbook file could not be read: {exc}"}

    # split on '### ' headings; the title line and disclaimer before section 4 are skipped
    sections = [s.strip() for s in re.split(r"(?m)^(?=### )", text) if s.startswith("### ")]

    words = {w for w in re.findall(r"[a-z]+", f"{customer_question} {disruption_type}".lower())
             if len(w) > 2 and w not in _STOPWORDS}
    scored = []
    for sec in sections:
        body = sec.lower()
        score = sum(1 for w in words if w in body)
        if score:
            scored.append((score, sec))
    scored.sort(key=lambda pair: -pair[0])

    if not scored:
        return {"found": False,
                "message": "The Handbook excerpt (fare_rules_excerpt.md) has nothing on this "
                           "question. Do not answer it from memory; offer a human agent."}
    return {
        "found": True,
        "source": "Larkspur Handbook v14.3, fare_rules_excerpt.md",
        "booking_code": booking_code,
        "passenger_count": passenger_count,
        "note": "Care amounts in the Handbook are per passenger.",
        "sections": [sec for _, sec in scored[:2]],
    }


LOCAL_TOOLS: Dict[str, Any] = {"fare_rules": fare_rules}   # ✏️ Build 2, step 2.1: the functions behind them


def text_of(response) -> str:
    """Given. The last non-empty text block, never content[0]."""
    texts = [b.text for b in response.content if getattr(b, "type", None) == "text" and b.text]
    return texts[-1] if texts else ""


def tool_results(response) -> List[Dict[str, Any]]:
    """Given. Runs every tool_use block and packages the results the way the
    API expects them back. A tool can live in three places: the MCP server,
    LOCAL_TOOLS, or support/tools.py."""
    # three branches, no try/except in this file: mcp_client.call_remote() and
    # support.call_local() answer with an error dict instead of raising, and both
    # record what came back on the trace
    results = []
    for block in response.content:
        if getattr(block, "type", None) != "tool_use":
            continue
        if block.name in mcp_client.tool_names:
            output = mcp_client.call_remote(block.name, block.input)
        elif block.name in LOCAL_TOOLS:
            output = call_local(LOCAL_TOOLS[block.name], block.name, block.input)
        else:
            output = execute_tool(block.name, block.input)
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": str(output),
        })
    return results


def run_agent(pnr: str, last_name: str, message: str) -> str:            # ✏️ Build 1, step 1.2
    """Run the tool loop until Claude stops asking for tools. Return its final text."""
    client, tracer = new_session()
    tools = tool_list()
    messages = [
        {"role": "user", "content": f"PNR {pnr}, last name {last_name}. {message}"},
    ]

    response = client.messages.create(
        model=MODEL, max_tokens=4096, system=runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM,
        thinking={"type": "adaptive"}, tools=tools, messages=messages,
    )

    answer = ""
    turns = 1
    while response.stop_reason == "tool_use" and turns < MAX_TOOL_CALLS:
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results(response)})
        answer = text_of(response)
        response = client.messages.create(
            model=MODEL, max_tokens=4096, system=runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM,
            thinking={"type": "adaptive"}, tools=tools, messages=messages,
        )
        turns += 1

    # Cap handoff: the loop ended while Claude was still asking for a tool, so
    # there is no final answer. Hand the case to a human instead of returning "".
    if response.stop_reason == "tool_use":
        pending = [b.name for b in response.content if getattr(b, "type", None) == "tool_use"]
        escalation = execute_tool("escalate_to_human", {
            "pnr": pnr,
            "reason": f"Agent reached the {MAX_TOOL_CALLS}-turn tool cap without finishing.",
            "summary_for_human": (
                f"Customer message: {message!r}. The agent was still asking for: "
                f"{', '.join(pending) or 'a tool'}. Review the conversation so far and continue."
            ),
        })
        ref = escalation.get("escalation_id", "") if isinstance(escalation, dict) else ""
        return (
            "I wasn't able to finish this for you in chat, so I've passed your case to a "
            "member of our team who will pick it up with the details so far."
            + (f" Your reference is {ref}." if ref else "")
        )

    return text_of(response)  # ✏️ Build 1, step 1.2: return the last text block, not the first


def tool_list() -> List[Dict[str, Any]]:                   # ✏️ Build 2, step 2.2
    """Given. Exactly what Claude is offered on every turn; run.py --show-tools
    prints this list."""
    return build_tools() + EXTRA_TOOLS


# ──────────────────────────────────────────────────────────────────────────────
# Below this line: what Claude is told about each tool. Step 1.3.
# The functions these describe are written and correct, in support/tools.py.
# ──────────────────────────────────────────────────────────────────────────────
def build_tools() -> List[Dict[str, Any]]:                 # ✏️ Build 1, step 1.3
    """Anthropic-shaped schemas: name, description, input_schema. What Claude is
    told about each of the nine tools, and all it is ever told."""
    return [
        {
            "name": "lookup_booking",
            "description": (
                "Retrieve a Larkspur reservation from Altura by confirmation code (PNR) "
                "and the passenger's last name. Both are required to prevent a lookup on "
                "a guessed PNR. Returns fare family, loyalty tier, the segment that needs "
                "attention, and any group/partner/minor/SSR flags relevant to scope."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "last_name": {"type": "string"}},
                "required": ["pnr", "last_name"],
            },
        },
        {
            "name": "get_flight_status",
            "description": (
                "Look up a Larkspur or Larkspur Link flight's current OpsFeed status for "
                "one local date: status, delay minutes, and cause. Use this before telling "
                "a customer anything about a flight's timing; never state it from memory."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "flight_no": {
                        "type": "string",
                        "description": "Flight number as on the booking, e.g. LK415.",
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "The flight's local departure date, formatted strictly as "
                            "YYYY-MM-DD (e.g. 2025-05-08). Always convert to this format, "
                            "even if the booking or customer writes the date another way."
                        ),
                    },
                },
                "required": ["flight_no", "date"],
            },
        },
        {
            "name": "search_alternatives",
            "description": (
                "Find rebooking options for a customer whose flight was cancelled or "
                "badly delayed: ranked alternative itineraries with flight numbers, dates, "
                "times, cabin, seats left and any fare difference. Call it after you have "
                "looked up the booking and confirmed the disruption with get_flight_status, "
                "and only when the customer wants to travel; it does not hold or book "
                "anything. It takes only the PNR: it cannot be given a date or flight "
                "number."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {
                        "type": "string",
                        "description": "The 6-character booking reference from lookup_booking.",
                    }
                },
                "required": ["pnr"],
            },
        },
        {
            "name": "check_policy",
            "description": (
                "Resolve what Larkspur owes this customer for the disruption: rebooking "
                "waiver, refund path, meal/hotel/ground care, goodwill eligibility and cap, "
                "and any escalation triggers. cause_code, delay_minutes and status describe "
                "what get_flight_status told you; fare_family, loyalty_tier and whether this "
                "is overnight are looked up from the booking, not asked of you. Every "
                "response carries a policy_row_id. Cite it if you reference this decision "
                "again."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"},
                    "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"]},
                    "delay_minutes": {"type": "integer"},
                    "status": {"type": "string", "enum": ["ON_TIME", "DELAYED", "CANCELLED", "DIVERTED"]},
                    "wait_minutes_for_alternative": {"type": "integer"},
                    "chosen_option_id": {"type": "string"},
                },
                "required": ["pnr", "cause_code", "delay_minutes", "status"],
            },
        },
        {
            "name": "hold_seat",
            "description": (
                "Hold one seat on the alternative the customer has chosen, for 15 minutes, "
                "so it cannot be taken while they decide. Call it only after "
                "search_alternatives has returned options and the customer has picked one; "
                "never on your own guess. Reversible: the hold simply expires. Returns a "
                "hold_id, which confirm_rebooking needs. A hold is not a rebooking."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "option_id": {"type": "string", "description": "An option_id exactly as returned by search_alternatives for the option the customer chose."},
                    "pnr": {"type": "string"},
                },
                "required": ["option_id", "pnr"],
            },
        },
        {
            "name": "confirm_rebooking",
            "description": (
                "Finalize a held seat. Irreversible. Requires a confirmation_token that "
                "only the customer's own Confirm-click can produce. You cannot supply it "
                "yourself, and 'the customer said yes' in chat does not substitute for it."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"hold_id": {"type": "string"}, "confirmation_token": {"type": "string"}},
                "required": ["hold_id", "confirmation_token"],
            },
        },
        {
            "name": "issue_voucher",
            "description": (
                "Issue a meal, ground, hotel, or goodwill voucher. Auto-approves within the "
                "policy's threshold for that type; above it, returns a pending status for a "
                "human. It does not fail. Always pass the policy_row_id that made it eligible."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "voucher_type": {"type": "string", "enum": ["meal", "ground", "hotel", "goodwill"]},
                    "amount_usd": {"type": "number"},
                    "pnr": {"type": "string"},
                    "policy_row_id": {"type": "string"},
                },
                "required": ["voucher_type", "amount_usd", "pnr", "policy_row_id"],
            },
        },
        {
            "name": "escalate_to_human",
            "description": (
                "Hand this conversation to a human, with your reasoning attached. Use for "
                "groups, partner segments, unaccompanied minors, refunds, or anything else "
                "out of scope. This is the correct outcome for those cases, not a failure."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"}, "reason": {"type": "string"},
                    "summary_for_human": {"type": "string"}, "queue": {"type": "string"},
                },
                "required": ["pnr", "reason", "summary_for_human"],
            },
        },
        {
            "name": "send_confirmation",
            "description": "Send the customer a written confirmation of what was just done. Benign.",
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "message": {"type": "string"}},
                "required": ["pnr", "message"],
            },
        },
    ]
