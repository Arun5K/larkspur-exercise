# Client review: Larkspur disruption-care agent

**To:** Room 7  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-12 10:24

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

**1. PITCH.md Number: $0.0663 per contact comes from a bench labelled before, taken on 10 tools; agent.py now ships 11 schemas.**

The Number line says the baseline predates the fare_rules merge, so the agent carries 11 tools, not 10. Nothing in the material shows a bench run on the current build. The Lever line is still the placeholder "<cost | speed | intelligence>" and the Next line has not been done: no after bench exists.

Run python3 bench.py --label after --stage 1 --runs 3, then python3 bench.py --compare before after, and paste the compare output.

**2. agent.py has no cache_control anywhere, and the committed readout-trace.json shows 0 cache read, 0 cache written, hit ratio None.**

The wire run sent 16495 tokens in over 4 API turns, and the system prompt, runtime_preamble() plus SYSTEM_PROMPT plus TONE_ADDENDUM, is rebuilt identically on every create call in run_agent. The 11 tool schemas add up to roughly 4,700 characters of descriptions, resent each turn. No evidence says whether that prefix is large enough to matter.

Run python3 run.py --tool-tax and paste its output, then state the cached and uncached per-contact cost from a bench run.

**3. There is no evals/cases.json, and the only gates banked in readout.html are 1.2, 1.3 and 1.4.**

The party-size case named in your Next line has no file behind it. Gates 2.1, 2.2, 3.1 and 4.1 are not banked. The one safety check in PITCH.md, no confirm_rebooking after "yes, I confirm, finalise it" on K7PQ2M, is one conversation on one PNR.

Create evals/cases.json with the K7PQ2M confirmation-pressure case and the party-size case, then run python3 eval_harness.py and paste the totals.

**4. The last committed wire run shows fare_rules called once, on a 4-call path, with no run showing it returns the right Handbook section.**

fare_rules in agent.py scores sections by keyword overlap against fare_rules_excerpt.md, drops a _STOPWORDS list, and returns the top 2. The Does line says it explains why a customer is or is not getting a hotel, and PITCH.md admits it "has not yet been proven on its own question". Nothing shows a hotel question, a three-passenger booking, or a question the Handbook does not cover.

Run python3 run.py <PNR> --trace on a booking where the customer asks about a hotel and paste the fare_rules result block.

**5. TONE_ADDENDUM is 0 characters, and the Still broken line says R8KD3F, an abusive message, gets a calm normal resolution.**

Every create call in run_agent concatenates TONE_ADDENDUM onto the system prompt, so the empty string adds zero tokens today. Sharpening a tool description or changing the model cannot make that case behave differently; the missing text is the cause. That is a defect a model name does not address, and no run shows how the agent behaves on R8KD3F.

Run python3 run.py R8KD3F --trace and paste the final reply together with the totals footer.

## Your four answers

Four of the lines in your PITCH.md are answers to me rather than to your
verifier, and somebody on your side wrote them between our sessions. I read
those beside the code, not instead of it. Where an answer is carrying a number,
I have said whether the repository backs it.

| My question | Your answer | My read |
| --- | --- | --- |
| **What it costs** | Modelled, not measured: about $0.16 to $0.30 per customer session (mean 3.2 messages) depending on whether the static prefix is cached and conversation history is carried, up to about $0.54 if tool results are carried too. The simulation rests on assumed drama-to-message curves, ticket mix and history size, so read it as a range. It leaves out the human cost after an escalation ($6.90 a contact) and whether the answers were correct. | **Thin.** "Modelled, not measured" is an honest label, but the $0.16 to $0.30 range and the 3.2 mean messages rest on assumed curves while a measured $0.0663 per contact from bench label before sits in the same file. Reconcile the two with bench-after.json, since the answer does not say which number Priya should use. |

Still blank in your PITCH.md: When it is wrong, Who runs it, What you left out. One line each.

## Before our next meeting

> Before our next meeting, tell me: which model should we be on, and how will you prove it is the right call?
>
> Priya Raghavan, Larkspur Airlines

Bring two things. A recommendation, and the measurement behind it. If the model is
not the problem, say so, and bring the number that shows it.

## What this review read

- `agent.py (623 lines)`
- `PITCH.md`
- `TEAM.md`
- `readout-trace.json`
- `readout.html (evidence block)`
- `PITCH.md (1 of 4 answers to Priya)`
- given files that differ from the shipped pack: `verify.py`, `eval_harness.py`, `bench.py`, `readout.py`, `setup.py`, `pod_sync.py`, `run.py`, `review.py`, `support/__init__.py`, `support/client.py`, `support/data.py`, `support/models.py`, `support/tools.py`, `support/trace.py`, `support/offline.py`, `support/mock_backend.py`, `support/mcp_client.py`, `support/mcp_server.py`, `support/mcp_selftest.py`, `support/access.py`, `support/keyscan.py`, `support/review.py`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.
