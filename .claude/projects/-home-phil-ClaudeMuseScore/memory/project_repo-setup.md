---
name: repo-setup
description: GitHub repo philkoh/ClaudeMuseScore with ED25519 deploy key and SSH alias github-ClaudeMuseScore
metadata:
  type: project
---

Repository: https://github.com/philkoh/ClaudeMuseScore (public)
Remote: git@github-ClaudeMuseScore:philkoh/ClaudeMuseScore.git
Deploy key: ED25519, stored at `deploy_key` (gitignored), public key `deploy_key.pub` tracked.
SSH config alias: `github-ClaudeMuseScore` in ~/.ssh/config, using IdentityFile at /home/phil/ClaudeMuseScore/deploy_key.

**Why:** Deploy key provides repo-scoped write access independent of the user's global GitHub token, and the SSH alias avoids conflicts with other repos.

**How to apply:** When pushing, the remote already uses the alias. If the user clones fresh, they'll need to restore the private `deploy_key` file and the SSH config entry (or push via HTTPS with their token). The public key is tracked for reference.

Related: [[standing-orders]]
