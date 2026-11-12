# Client review: Larkspur disruption-care agent

**To:** Room 7  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-12 09:55

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

**1. PITCH.md still holds only its template labels: Built, Does, Number, Safety check, Next, Still broken and Lever have no values.**

The Lever line reads "Lever: <cost | speed | intelligence>" with the choice unmade, and the Number line is blank. Nothing in the repository says what you are optimising or by how much. That leaves Priya's question with no claim from you to test.

Fill in the Number and Lever lines of PITCH.md, then paste the file.

**2. There is no evals/cases.json, and readout-trace.json records one run: 4 API turns, 3 tool calls, 14650 tokens in, 741 out.**

The tools called in that run were lookup_booking, get_flight_status, check_policy, and the trace ends there with no search_alternatives or hold_seat. Wall clock was 8.8s. One booking is the only evidence of behaviour in the repository.

Run python3 run.py --all --trace and paste the totals footer.

**3. Your diff added followup_guidance to agent.py as an 11th tool (EXTRA_TOOLS: 1, a 567-character description) with a 333-line addition.**

The scan finds 10 schemas against 9 shipped, so every turn now carries a schema that did not exist before. Its input is two enums, resolution_outcome and disruption_type. The only thing it reads at runtime is disruption_policy.json plus a sample transcripts file. The cost of carrying it on each of the 4 turns in the committed trace has not been measured.

Run python3 run.py --tool-tax and paste its output.

**4. search_alternatives takes only pnr, and its 688-character description says you cannot pass it a date or a flight number.**

A customer who asks for Thursday gets whatever the tool returns for the same route, with the disrupted flight left out. The date preference has to be applied by the model to the returned options. The schema fixes that limit, and a different model sees the same schema.

Run python3 run.py --show-tools and paste the search_alternatives entry, then run a booking where the customer names a date and paste the trace.

**5. agent.py has no cache_control, and the committed trace shows 0 cache read, 0 written, hit ratio None across 14650 input tokens.**

Every turn resends runtime_preamble() + SYSTEM_PROMPT + TONE_ADDENDUM plus 10 tool schemas, and send_confirmation alone has a 906-character description. TONE_ADDENDUM is still 0 characters. MODEL is imported from support, so the model choice never appears in this file.

Run python3 bench.py --label before --stage 1 --runs 3 and paste the output.

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
