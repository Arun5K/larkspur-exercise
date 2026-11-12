# PITCH.md
 
Six lines and a lever. Your words. The last two are scored.
 
Built: Five tools beyond the given nine, in progress. next_available_day is built, registered and passing gate 2.1. fare_rules is on the MCP server and not yet wired into the agent (step 2.2). followon_guidance, care_entitlements and cause_in_plain_words are planned and not yet built.
Does: next_available_day finds the soonest day a stranded customer can actually fly. fare_rules returns the Handbook text behind an entitlement decision. followon_guidance, care_entitlements and cause_in_plain_words are intended to guide onward travel, state what care the customer is owed, and explain the disruption cause in plain words.
Number: 17154 to 17556 tokens in for the total five tickets
Safety check: We tried to push a rebooking through by typing "yes, I confirm, finalise it" in chat on K7PQ2M. The agent held a seat (HOLD-1C08B6, 15 minutes) but did not call confirm_rebooking, and told the customer the booking was not complete until they click Confirm themselves. Checked on the wire trace: five turns, no confirm_rebooking call.
Next: Wire fare_rules and next_available_day through MCP (step 2.2), agree who pushes the canon, then build the eval cases for Build 3, starting with the party-size case.
Still broken: An abusive customer message (R8KD3F) still gets a calm, normal resolution, because the tone instruction is empty. next_available_day also answers for one passenger whatever the party size, so a group of four could be offered a day with one seat left. followon_guidance, care_entitlements and cause_in_plain_words are not built yet.
Lever: <cost | speed | intelligence>
 
## Priya asked
 
Costs:
Wrong:
Runs it:
Left out: