---
name: standing-orders
description: Always commit+push+save memory when a new feature is added; commit after passing tests, never in broken state
metadata:
  type: feedback
---

Always commit, push, and save to memory whenever a new feature is successfully added — do this autonomously without being asked.

**Why:** The user may delete the local directory at any time and resume by cloning from GitHub. All progress (including memories) must be preserved in the repo.

**How to apply:** After any successful feature addition or passing test suite, stage appropriate files (including .claude/ memory directory), commit with a descriptive message, and push to origin. Avoid committing when tests fail or the codebase is in a broken state. Ensure .claude/ project memory files are always tracked so context survives a fresh clone.

Related: [[repo-setup]]
