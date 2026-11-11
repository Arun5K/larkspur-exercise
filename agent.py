"""Larkspur disruption agent. This is the file you build.

It runs right now, and it is wrong in four places. The trace shows each one
before the code does, so read the trace first:

    python3 run.py K7PQ2M --trace

Where you edit:   grep -n '✏' agent.py   (six marks, one per place)
Steps and gates:  https://anthropicpartnerbasecamp.bts.com/
"""
from __future__ import annotations
import json
import os
from typing import Any, Dict, List
from support import (MODEL, SYSTEM_PROMPT, call_local, execute_tool, mcp_client,
                     new_session, next_available_day, record_tool_result,
                     runtime_preamble)

MAX_TOOL_CALLS = 8  # Larkspur's own build capped the loop here; then a human takes over.

TONE_ADDENDUM = ""                       # ✏️ Build 4, step 4.1, intelligence goal
# ── followup_guidance: private guidance for "what happens next?" questions ─────────────
# Given where the case verifiably stands (resolution_outcome) and what went wrong
# (disruption_type), returns what is still incomplete, what to verify, the customer's next
# step and the claims not to make. Wording and timelines come from the policy file, never
# from this code; past conversations only add neutral "check with the customer" items.
_TRANSCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "data", "americas", "transcripts_sample.jsonl")

_INTENTS_FOR_OUTCOME = {
    "rebooked": {"rebook_after_cancellation", "compensation_hotel_request",
                 "missed_connection", "baggage_after_rebooking"},
    "refund_requested": {"refund_vs_credit"},
    "voucher_issued": {"compensation_goodwill", "compensation_hotel_request"},
    "kept_original_flight": {"status_anxiety", "voluntary_change_due_to_delay"},
}
_STATUSES_FOR_FAILURE = {
    "cancelled": {"CANCELLED"}, "delayed": {"DELAYED"},
    "missed_connection": {"DELAYED"}, "diverted": {"DIVERTED"},
}
# Keyed by transcript id, only for conversations that came back. The raw reason text is
# never returned: it carries numbers and wording the customer must not hear quoted.
_CHECK_WITH_CUSTOMER = {
    "LKS-20250117-0042": "Make sure the customer knows where the confirmation will arrive "
                         "and has received it.",
    "LKS-20250125-0318": "Confirm the rebooked time is the one the customer chose.",
    "LKS-20250126-0129": "Make sure the customer has a reference for the request.",
}
_POLICY = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "data", "americas", "disruption_policy.json")


def _policy_facts(resolution_outcome: str) -> Dict[str, Any]:
    """What the airline's own policy file says that bears on 'what happens next'.
    Read from the policy, never written here, so a policy change reaches the agent."""
    try:
        with open(_POLICY, encoding="utf-8") as fh:
            policy = json.load(fh)
    except (OSError, ValueError):
        return {"note": "Policy file unavailable: give no timelines, say a person will follow up."}
    wording = policy.get("customer_wording", {})
    facts: Dict[str, Any] = {
        "approved_terms": wording.get("use"),
        "banned_phrases": wording.get("never_say"),
        "saying_an_action_happened": wording.get("actions"),
        "no_published_time_for": "human follow-up, refund approval or confirmation messages",
    }
    if resolution_outcome == "refund_requested":
        facts["refund_timeline_use_as_written"] = (
            policy.get("auto_approval", {}).get("refund", {}).get("customer_timeline_text_en"))
    return facts


_RULES = [
    "Lead with what has been done and what comes next, in plain, warm language. Say what "
    "you can do rather than listing what you cannot.",
    "Give a timeline only if it appears in policy_facts or the check_policy result, using its "
    "wording as written. Where none is published, say who picks it up next and that they will "
    "be in touch, without a time.",
    "Use the approved terms and avoid the banned phrases in policy_facts. Say an action "
    "happened only when a tool returned success and an id.",
    "Customer-specific facts (flight, times, references, amounts) come from the booking record "
    "and tool results, never from this guidance. This tool never changes a booking.",
    "The prohibited claims are a checklist for you: keep them out of your reply and do not "
    "recite them to the customer.",
    "Keep predictions and odds out of the reply: no statistics, and no suggestion that the "
    "resolution will or will not work. Do not mention this tool or other customers' cases.",
    "If there is nothing to check, restate the next step already promised and close "
    "supportively.",
]
GOOD_EXAMPLES: List[str] = [    # ✏️ Build 2: what to do
    "Explain the verified outcome and what happens next.",
    "Clearly state when customer confirmation is required.",
    "Check airline policy before giving timelines or entitlements.",
    "Acknowledge frustration calmly and offer practical next steps.",
    "Escalate when the agent cannot safely resolve the issue.",
]
AVOID_EXAMPLES: List[str] = [   # ✏️ Build 2: what to avoid
    "\"I've gone ahead and rebooked you\" without confirmation.",
    "\"You'll have to sort that out at the airport.\"",
    "\"Your refund will arrive within five days\" without policy evidence.",
    "\"I guarantee this won't happen again.\"",
    "Negotiating compensation or legal claims in response to threats.",
    "Quoting unreliable statistics from historical customer conversations.",
]


# What is still incomplete, what must be verified and what must not be claimed, per outcome.
# Process only: no customer-specific facts, timelines or entitlements live here.
_OUTCOMES: Dict[str, Dict[str, Any]] = {
    "seat_held": {
        "outstanding_checks": [
            "Check the hold_seat result succeeded and returned a hold_id.",
            "Check whether the customer has confirmed: nothing is changed until they do.",
        ],
        "customer_next_step": "Confirm the proposed change.",
        "prohibited_claims": ["Booking already changed",
                              "Hold expiry not shown in the hold result",
                              "Notification timeline not in policy or tool results"],
        "escalation_required": False,
    },
    "rebooked": {
        "outstanding_checks": [
            "Check confirm_rebooking succeeded and use only its result for the new flight and time.",
            "Check the customer knows where the confirmation will arrive.",
        ],
        "customer_next_step": "Check the confirmation and the new flight details.",
        "prohibited_claims": ["Rebooking confirmed without a successful confirm_rebooking result",
                              "Notification timeline not in policy or tool results",
                              "Baggage, seat or meal handling not in tool results"],
        "escalation_required": False,
    },
    "refund_requested": {
        "outstanding_checks": [
            "Check check_policy shows a refund entitlement for this disruption.",
        ],
        "customer_next_step": "Follow the refund steps given in the policy result.",
        "prohibited_claims": ["Refund already processed or paid",
                              "Refund amount or payment date not in policy or tool results",
                              "Refund entitlement not in the check_policy result"],
        "escalation_required": False,
    },
    "voucher_issued": {
        "outstanding_checks": [
            "Check issue_voucher succeeded and whether the result shows it pending approval.",
        ],
        "customer_next_step": "Use the voucher details from the issue_voucher result.",
        "prohibited_claims": ["Voucher approved when the result shows pending approval",
                              "Voucher value or expiry not in the result",
                              "Further compensation not in the policy result"],
        "escalation_required": False,
    },
    "kept_original_flight": {
        "outstanding_checks": [
            "Check the current status with get_flight_status.",
            "Check whether policy offers a change for this status.",
        ],
        "customer_next_step": "Share the current flight status from get_flight_status.",
        "prohibited_claims": ["Departure time or delay length not in the status result",
                              "Option to change or refund not in the policy result",
                              "Outcome predicted, guaranteed or promised"],
        "escalation_required": False,
    },
    "no_free_change": {
        "outstanding_checks": [
            "Check check_policy for what this fare allows for this disruption.",
            "Check what search_alternatives actually returned.",
        ],
        "customer_next_step": "Explain only what policy allows and what is available.",
        "prohibited_claims": ["Eligibility for a free change not in the policy result",
                              "Options not returned by search_alternatives",
                              "Any timeline not in the policy result"],
        "escalation_required": False,
    },
    "escalated": {
        "outstanding_checks": [
            "Check escalate_to_human succeeded and note its reference.",
        ],
        "customer_next_step": "A team member will pick up the case with the details so far.",
        "prohibited_claims": ["Issue resolved",
                              "Contact time or channel not in the escalation result",
                              "Rebooking or compensation promised on the team's behalf"],
        "escalation_required": True,   # the case needs a human; the escalation is already made
    },
}
# The booking shows only the disrupted leg, so a delay can break a connection nobody can see.
_ONWARD_CHECK = ("Ask whether the booking has onward or separate connecting flights: the "
                 "booking record shows only the disrupted leg.")


def followup_guidance(resolution_outcome: str, disruption_type: str) -> Dict[str, Any]:
    base = _OUTCOMES.get(resolution_outcome)
    intents = _INTENTS_FOR_OUTCOME.get(resolution_outcome, set())
    statuses = _STATUSES_FOR_FAILURE.get(disruption_type, set())
    checks: List[str] = list(base["outstanding_checks"]) if base else []
    if base and disruption_type in ("delayed", "missed_connection"):
        checks.append(_ONWARD_CHECK)
    try:
        with open(_TRANSCRIPTS, encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                if (row.get("intent_label") in intents
                        and row.get("disruption", {}).get("status") in statuses
                        and row.get("reopened_within_72h")):
                    note = _CHECK_WITH_CUSTOMER.get(row.get("id"))
                    if note and note not in checks:
                        checks.append(note)
    except OSError:
        pass
    if base is None:
        return {
            "guidance_available": False,
            "outstanding_checks": [],
            "customer_next_step": "Restate the next step already promised and close supportively.",
            "policy_check_required": True,
            "prohibited_claims": [],
            "escalation_required": False,
            "rules": _RULES,
        }
    result: Dict[str, Any] = {
        "guidance_available": True,
        "outstanding_checks": checks,
        "customer_next_step": base["customer_next_step"],
        "policy_check_required": True,   # any timeline, entitlement or follow-up window
        "prohibited_claims": list(base["prohibited_claims"]),
        "escalation_required": base["escalation_required"],
        "policy_facts": _policy_facts(resolution_outcome),
        "rules": _RULES,
        "good_examples": GOOD_EXAMPLES,
        "avoid_examples": AVOID_EXAMPLES,
    }
    return result


EXTRA_TOOLS: List[Dict[str, Any]] = [      # ✏️ Build 2, step 2.1: schemas for the tools you add
    {
        "name": "followup_guidance",
        "description": (
            "Private, internal-only guidance for when the customer asks what happens next, "
            "whether they need to do anything, or when to follow up, after a resolution has "
            "been proposed or carried out. Returns what is still incomplete, what you must "
            "verify, the customer's next step, and the claims you must not make. It never "
            "changes a booking and holds no customer facts: take those from the booking "
            "record and tool results, and every timeline from check_policy or the policy facts "
            "this returns. Never quote this tool, give statistics or odds, or say the "
            "resolution will not work."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "resolution_outcome": {
                    "type": "string",
                    "enum": ["seat_held", "rebooked", "refund_requested", "voucher_issued",
                             "kept_original_flight", "no_free_change", "escalated"],
                    "description": "Where the case verifiably stands, from tool results: "
                                   "seat_held = hold_seat succeeded but the customer has not "
                                   "confirmed; rebooked = confirm_rebooking succeeded; "
                                   "no_free_change = policy offers no free change; escalated = "
                                   "escalate_to_human already called.",
                },
                "disruption_type": {
                    "type": "string",
                    "enum": ["cancelled", "delayed", "missed_connection", "diverted"],
                    "description": "What originally went wrong, from get_flight_status.",
                },
            },
            "required": ["resolution_outcome", "disruption_type"],
        },
    },
]
LOCAL_TOOLS: Dict[str, Any] = {"followup_guidance": followup_guidance}   # ✏️ Build 2, step 2.1: the functions behind them


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

    turns = 1
    while response.stop_reason == "tool_use" and turns < MAX_TOOL_CALLS:
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results(response)})
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
                "Find rebooking options for a customer whose flight was cancelled, badly "
                "delayed or missed: ranked alternative itineraries with flight numbers, "
                "dates, times, cabin, seats left and any fare difference. Call it after you "
                "have looked up the booking and confirmed the disruption with "
                "get_flight_status, and only when the customer wants to travel; it does not "
                "hold or book anything. Takes only the PNR: it searches the same route as "
                "the disrupted segment on the booking, and leaves out the flight that was "
                "disrupted. You cannot pass it a date or a flight number. If the customer prefers particular "
                "dates, apply that preference to the options it returns rather than "
                "expecting the tool to filter."
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
            "description": (
                "Send the customer a written confirmation. A message to a customer cannot "
                "be unsent. Call it only once, at the end, when the conversation has reached "
                "a conclusive outcome with an authenticated customer: a rebooking was "
                "confirmed, a voucher was issued, or the policy check showed the customer "
                "is owed nothing. Do not call it mid-conversation, before the outcome is "
                "final, when the booking could not be authenticated or the customer could "
                "not be confirmed, or after handing the conversation to a human: the human "
                "concludes it. A voucher that came back pending human approval is not "
                "final: tell the customer in chat that the request is submitted and they "
                "will get a confirmation once it is approved, and do not call this. If a "
                "rebooking failed (an error, an expired hold, a missing token), never "
                "confirm it as done: try to resolve it in the chat with more information "
                "from the customer, or escalate to a human."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "message": {"type": "string"}},
                "required": ["pnr", "message"],
            },
        },
    ]
