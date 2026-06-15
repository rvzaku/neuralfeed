---
name: verify-deployed
description: >
  Verify the DEPLOYED NeuralFeed frontend renders what was agreed in feedback, before
  asking the user to check the site. Use whenever you are about to say "check the deployed
  site", after merging any frontend change, or when the user asks to confirm a feedback
  item actually shipped. Prevents repeating the same feedback by checking the live site
  against `.dev-notes/frontend-acceptance.md` with real-browser evidence.
---

# Verify Deployed

Closes the feedback loop: instead of asking the user to eyeball the site and re-report
the same problems, an agent loads the **deployed** frontend and proves each agreed item
renders.

## When to run
- **Always** before you tell the user "please check the deployed site." Verify first;
  only surface items you've confirmed, and flag the ones still failing yourself.
- After any commit that touches `frontend/`.
- When the user gives new feedback — first translate it into rows in the acceptance
  contract, then run this to baseline what currently passes/fails.

## Steps
1. **Sync the contract.** Open `.dev-notes/frontend-acceptance.md`. If the latest user
   feedback isn't represented as rows, add them (status `TODO`) before verifying — this
   file is the rendering contract and must stay current with every feedback round.
2. **Delegate to the verifier agent.** Spawn the `frontend-verifier` subagent (Agent tool,
   `subagent_type: frontend-verifier`). Pass:
   - the row IDs in scope (or "all non-PASS rows"),
   - any test login credentials the user provided (the site is login-first; never invent
     credentials — ask the user if needed),
   - a reminder that the backend is on Render free tier and may cold-start.
3. **Relay results.** The agent updates the contract and returns a PASS/FAIL table. Report
   to the user only the confirmed-passing items plus an explicit "still failing" list with
   the observable gap for each. If everything in scope is PASS, say so plainly with the
   evidence; then it's safe to ask the user for a final human look.

## Notes
- The verifier uses the `chrome-devtools` MCP (already available in this workspace) to
  drive a real browser, take DOM snapshots/screenshots, and read the console.
- Evidence beats assertion: never report an item as done from code inspection — only from
  what rendered on `https://neuralfeed.vercel.app`.
- Keep the contract's "Verification log" as the running history of what was checked when.
