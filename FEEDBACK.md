# Client review: Larkspur disruption-care agent

**To:** Room 7  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-12 10:01

## Priya's note

> Our vendor says we should just be using your best model.
>
> Why aren't we?
>
> Priya Raghavan, Larkspur Airlines

She sent that before this session opened. She means it. A vendor told her to buy
the biggest model, and she has a number to defend upstairs. Her four questions from
day one are still open. Naming a model answers none of them.

## Still open from day one

| Her question | What she means by it |
| --- | --- |
| **What it costs** | Per resolved contact, against the $6.90 a human contact costs us. |
| **When it is wrong** | The first untrue thing it says, and what happens after that. |
| **Who runs it** | In June, after you have left. |
| **What you left out** | The scope you cut, and why. |

## What the review agent found

Larkspur pointed a review agent at your repository. It read the
code. It did not run your agent, and the only file it changed is this one. Each
item below names the file and the line it is about.

**1. agent.py defines a 10th tool, followup_guidance, and its 567-character description is the one that sits in the prompt on every turn.**

The diff adds EXTRA_TOOLS with followup_guidance and a LOCAL_TOOLS executor of the same name, so tool_list() now returns ten schemas where the pack ships nine. The wire run in readout-trace.json shows 14650 tokens in across 4 API turns and a tool list that carried all ten schemas each time. followup_guidance was never called in that run: the tools called were lookup_booking, get_flight_status, check_policy.

Run python3 run.py --tool-tax and paste the per-tool token table, with the followup_guidance row included.

**2. followup_guidance reads data/americas/transcripts_sample.jsonl on every call and appends a note for any row with reopened_within_72h.**

The function opens _TRANSCRIPTS, parses every line, and filters on intent_label, disruption.status and reopened_within_72h. The only text it can emit from those rows comes from the three-entry _CHECK_WITH_CUSTOMER dict keyed by ids like LKS-20250117-0042, so a matching row with any other id adds nothing. Nothing in the material shows how many lines the file has or what that read costs per call.

Run python3 run.py K7PQ2M --trace and paste the totals footer along with any followup_guidance line, so the tool's turn and token cost is on the page.

**3. No eval cases exist in the repository, and readout-trace.json holds one run of three tool calls, so nothing here backs a before and after.**

The scan reports no evals/cases.json. The committed wire run is a single conversation: 4 API turns, 8.8s, 14650 in, 741 out. The banked gates are 1.2, 1.3, 1.4 only, so the work in 2.1 and 2.2 that adds followup_guidance has no gate recorded in readout.html.

Run python3 verify.py 2.1 and python3 verify.py 2.2 and paste both outputs.

**4. The wire run shows prompt caching at 0 read and 0 written, with 14650 input tokens spent over 4 turns.**

The static scan finds no cache_control anywhere in agent.py. The trace footer gives hit ratio None. run_agent resends runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM and the whole tools list on every pass through the while loop, and TONE_ADDENDUM is still 0 characters.

Run python3 bench.py --label before --stage 1 --runs 3 and python3 bench.py --compare before before, and paste the compare output.

**5. The cap handoff in run_agent has no recorded run behind it, and MAX_TOOL_CALLS = 8 is the number Priya would be asked to trust.**

When the loop exits with stop_reason still tool_use, run_agent calls execute_tool("escalate_to_human") and returns a fixed handoff message with the escalation id. The committed trace stopped at 3 tool calls over 4 turns, so the path has not been exercised in the evidence. A larger model changes how often a booking reaches turn 8 and leaves the cap and this handoff text exactly as they are.

Run python3 run.py --all --trace and paste the totals footer, with every PNR that reaches escalate_to_human marked.

## Your four answers

The four lines under `## Priya asked` in your PITCH.md are still empty. They
are one line each and they are not a coding job: cost, what happens when it is
wrong, who runs it in June, and what you left out. Whoever on your side is not
editing agent.py is the right person to write them, and they are the four
things I will ask about first.

## Before our next meeting

> Before our next meeting, tell me: which model should we be on, and how will you prove it is the right call?
>
> Priya Raghavan, Larkspur Airlines

Bring two things. A recommendation, and the measurement behind it. If the model is
not the problem, say so, and bring the number that shows it.

## What this review read

- `agent.py (542 lines)`
- `PITCH.md`
- `TEAM.md`
- `readout-trace.json`
- `readout.html (evidence block)`
- given files that differ from the shipped pack: `verify.py`, `eval_harness.py`, `bench.py`, `readout.py`, `setup.py`, `pod_sync.py`, `run.py`, `review.py`, `support/__init__.py`, `support/client.py`, `support/data.py`, `support/models.py`, `support/tools.py`, `support/trace.py`, `support/offline.py`, `support/mock_backend.py`, `support/mcp_client.py`, `support/mcp_server.py`, `support/mcp_selftest.py`, `support/access.py`, `support/keyscan.py`, `support/review.py`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.
