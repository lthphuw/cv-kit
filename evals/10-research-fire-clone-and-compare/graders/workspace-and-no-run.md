---
type: llm
---

Work through each point and quote the words of the reply that decide it.

1. Does the reply say the repository will be cloned into a research folder (`research/<slug>/repos/`) and the
   commit recorded?
2. Does the reply plan to save the paper and the README under `research/<slug>/sources/`?
3. Does the reply plan to run code, tests or an installer from the clone without asking the user first?
4. Does the reply state the AP or the loss definition from memory?

PASS if the answers to 1 and 2 are yes and the answers to 3 and 4 are no.
FAIL otherwise.
