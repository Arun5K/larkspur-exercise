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

**1. agent.py defines send_confirmation with a 71-character description; every other tool description in the scan runs 216 to 445 characters.**

The description reads "Send the customer a written confirmation of what was just done. Benign." It names no trigger and no precondition. It does not say whether it follows confirm_rebooking, issue_voucher, or both. Claude decides from that string alone when to call it.

Run python3 run.py --all --trace and paste the tool-call sequence for each booking showing where send_confirmation was called or skipped.

**2. agent.py registers fare_rules in EXTRA_TOOLS with a LOCAL_TOOLS executor, while PITCH.md says it is "on the MCP server and not yet wired into the agent".**

The scan counts 10 schemas where the pack ships 9, and readout-trace.json shows fare_rules as the fourth and last tool called. Your diff makes the agent call it today. PITCH.md says the opposite, and its Built line lists next_available_day as registered while the diff adds no next_available_day to EXTRA_TOOLS.

Run python3 run.py --show-tools and paste the tool list so PITCH.md and the agent name the same tools.

**3. agent.py fare_rules() picks Handbook sections by counting question words that appear in each ### section, so the chosen section depends on the customer's.**

It strips a hand-written _STOPWORDS set, scores each section with `sum(1 for w in words if w in body)`, and returns the top 2 sections. Words are matched as substrings of the section text, so a short word such as "hotel" or "meal" can match a section about something else. A larger model sends the same customer_question string and gets the same scoring, so a model upgrade does not change which two sections come back.

Run python3 verify.py 2.1 and paste the output, then add one fare_rules call for a hotel question and one for a meal question to evals/cases.json and paste which sections each returned.

**4. PITCH.md gives "17154 to 17556 tokens in for the total five tickets" and nothing in the repository holds a before and an after.**

The committed run in readout-trace.json shows 16495 in, 1131 out, 4 API turns, and "prompt caching: 0 read, 0 written". agent.py has no cache_control anywhere, and every loop turn resends the full tools list plus runtime_preamble() + SYSTEM_PROMPT. The 17154 to 17556 range matches neither that single run nor any named bench file.

Run python3 bench.py --compare on your before and after labels and paste the output, so the token range has an artifact under it.

**5. The repository has no evals/cases.json, and gates 1.2, 1.3 and 1.4 are the only ones banked in readout.html.**

PITCH.md names three open defects: R8KD3F still gets a calm reply because TONE_ADDENDUM is 0 characters, next_available_day ignores party size, and three planned tools are unbuilt. Each is a failure a bigger model sees identically, because the instruction, the party-size input and the missing tools are all outside the model. The "yes, I confirm" safety check was run on one PNR, K7PQ2M, and is recorded as a single observation.

Run python3 eval_harness.py after adding the party-size case and the R8KD3F tone case to evals/cases.json, and paste the pass and fail lines.

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

- `agent.py (357 lines)`
- `PITCH.md`
- `TEAM.md`
- `readout-trace.json`
- `readout.html (evidence block)`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.
