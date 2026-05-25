# ClaudeMuseScore

## Project
MuseScore project managed with Claude Code.

## Default User
Phil Koh <pk14225@gmail.com>

## Git
- Remote: git@github-ClaudeMuseScore:philkoh/ClaudeMuseScore.git (uses deploy key)
- Always commit and push after a new feature is successfully added
- Commit after successful tests; avoid committing in a broken state
- The .claude/projects/ memory directory is tracked in git so work can resume after a fresh clone

## Deploy Key
- Private key: `deploy_key` (gitignored, keep safe)
- Public key: `deploy_key.pub` (tracked)
- SSH config alias: `github-ClaudeMuseScore` (configured in ~/.ssh/config)

## Standing Orders
- Commit + push + save to memory whenever a new feature is successfully added (autonomously, without being asked)
- Track enough files so that cloning from GitHub allows continuing right where we left off, including memories
