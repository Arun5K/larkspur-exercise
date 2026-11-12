# Client review: Larkspur disruption-care agent

**To:** Room 7  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-12 10:05

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

**1. agent.py sends no cache_control, and readout-trace.json shows 0 read and 0 written against 14650 tokens in over 4 API turns.**

The static scan finds no cache_control anywhere in agent.py. The committed wire run reports a hit ratio of None. Every turn resends runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM plus all 10 tool schemas, and tool_list() returns build_tools() + EXTRA_TOOLS on each of those turns.

Run python3 run.py --all --trace and paste the totals footer, then run python3 run.py --tool-tax and paste its output.

**2. Your PITCH.md Number reads "17154 to 17556 tokens in for the total five tickets" and neither a before nor an after label is in the material.**

No bench files or compare output are in the material, so the two figures have no named run behind them. The only committed run is readout-trace.json at 14650 tokens in and 741 out for one booking. Nothing says which of the two figures is the baseline or which lever moved it.

Run python3 bench.py --compare with your before and after labels and paste the output.

**3. followup_guidance in agent.py is a tool that costs tokens, and PITCH.md still says followon_guidance is planned and unbuilt.**

Your diff adds 333 lines and registers followup_guidance, with a 567-character description, and a LOCAL_TOOLS executor. PITCH.md names followon_guidance as not yet built and mentions no followup_guidance. The tool tax count is 10 schemas against the 9 the pack ships. The trace shows lookup_booking, get_flight_status and check_policy called, and no followup_guidance call.

Run python3 run.py --show-tools and paste the list, then run python3 run.py K7PQ2M --trace and paste whether followup_guidance is ever called.

**4. PITCH.md says "the tone instruction is empty" and TONE_ADDENDUM in agent.py is 0 characters, so the R8KD3F failure sits in a prompt gap.**

R8KD3F gets "a calm, normal resolution" to an abusive message. The only prompt text this build adds beyond the shipped pack is empty, since TONE_ADDENDUM is "". A larger model reading the same empty addendum receives the same instruction. Nothing in the material shows the abuse handling being tested on any model.

Run python3 run.py R8KD3F --trace and paste the final reply and the tool calls.

**5. There is no evals/cases.json, and your gate 1.2, 1.3 and 1.4 banking is the only pass evidence for the loop.**

readout.html banks gates 1.2, 1.3 and 1.4 for Room 7 on 2026-11-11. Gate 2.1 is claimed in PITCH.md and is absent from that list. The party-size case you name as next is not written down anywhere in the repository.

Run python3 verify.py 2.1 and paste the result, then run python3 eval_harness.py once cases exist and paste the summary.

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
