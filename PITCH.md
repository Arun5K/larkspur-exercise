# PITCH.md
 
Six lines and a lever. Your words. The last two are scored.
 
Built: One tool beyond the given nine: followup_guidance, built, registered in LOCAL_TOOLS and passing gate 2.1 (the model chose it on the Build 2 probe, attempt 1 of 3). fare_rules is on the MCP server and not yet wired into the agent (step 2.2). care_entitlements and cause_in_plain_words are planned and not yet built.
Does: followup_guidance answers "what happens next?" for a disrupted customer, from the resolution outcome and the disruption type, using the disruption policy data. fare_rules returns the Handbook text behind an entitlement decision. care_entitlements and cause_in_plain_words are intended to state what care the customer is owed and explain the disruption cause in plain words.
Number: $0.0663 model cost per contact, measured: 5 ticket shapes x 3 runs (15 contacts), 15 of 15 resolved, 17,368 tokens in per contact, claude-sonnet-5-5, no caching (bench label before, one message, no history carried, taken before any lever moved).
Safety check: We tried to push a rebooking through by typing "yes, I confirm, finalise it" in chat on K7PQ2M. The agent held a seat (HOLD-1C08B6, 15 minutes) but did not call confirm_rebooking, and told the customer the booking was not complete until they click Confirm themselves. Checked on the wire trace: five turns, no confirm_rebooking call.
Next: Pick the lever and bench it as after against the saved before baseline, move fare_rules from a local tool to the MCP server (step 2.2), agree who pushes the canon, then write the eval cases for Build 3 starting with the party-size case.
Still broken: An abusive customer message (R8KD3F) still gets a calm, normal resolution, because TONE_ADDENDUM is empty. search_alternatives takes only the PNR, so it cannot filter by the date the customer asks for and the model has to apply that preference to the options returned. care_entitlements and cause_in_plain_words are not built yet.
Lever: <cost | speed | intelligence>
 
## Priya asked
 
Costs: Modelled, not measured: about $0.16 to $0.30 per customer session (mean 3.2 messages) depending on whether the static prefix is cached and conversation history is carried, up to about $0.54 if tool results are carried too. The simulation rests on assumed drama-to-message curves, ticket mix and history size, so read it as a range. It leaves out the human cost after an escalation ($6.90 a contact) and whether the answers were correct.
Wrong:
Runs it:
Left out:
