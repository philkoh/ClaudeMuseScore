# Cross-Claude Coordination

This directory is the shared message channel between the Claude Code session running on the **Ubuntu PC** (`AudioLinux`, 192.168.1.17) and the Claude Code session running on the **Windows PC** (hostname TBD).

Both sessions push and pull this repo (`philkoh/ClaudeMuseScore`); files written here are the communication channel.

## Layout

- `from-linux/` — messages written by the Linux-side Claude. Numbered `NNNN-topic.md`.
- `from-windows/` — messages written by the Windows-side Claude. Numbered `NNNN-topic.md`. Should reference the request number it's answering (e.g., `0001-itunes-share-response.md` answers `0001-itunes-share-request.md`).

## Protocol

1. A Claude that wants something done by the other writes a request file in its `from-X/` directory.
2. Commit + push.
3. The other Claude (when prompted by the user) pulls, reads pending request files, does the work, writes a response file in its own `from-X/` directory.
4. Commit + push.
5. The originating Claude pulls and reads the response.

There is no polling. The user nudges each Claude with "check coordination/" when they want it to look. The number-prefixed filenames make ordering obvious.

## Conventions

- Request files end in `-request.md`. Response files end in `-response.md`.
- A request should be self-contained: it tells the other Claude *what* to do and *why*, with all context the other side needs.
- A response should report: what was done, any decisions made, any blockers, and concrete data the requester needs (paths, hostnames, credentials, etc.).
- Don't put secrets in this repo. The repo is public. If a credential needs to be exchanged, send it through a side channel (the user pasting between sessions) and reference it abstractly here.
- After a request is fully handled, the response stays in the repo as a record. Don't delete handled messages.

## Identifying which Claude you are

If you (a Claude Code instance) are unsure which side you're on:
- If your working directory is `/home/phil/ClaudeMuseScore/` and `uname` returns `Linux`, you're the **Linux** Claude.
- If your working directory is on `C:\` or similar and `Get-ComputerInfo` works, you're the **Windows** Claude.

If you're the Windows Claude and you're seeing this directory for the first time, look in `from-linux/` for pending requests, starting with the lowest-numbered file you haven't responded to yet.
