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

## Safety rules — READ BEFORE COMMITTING (both Claudes)

Two Claude sessions pushing to the same remote can collide. These rules prevent that:

1. **Always `git pull --rebase` before any commit, and always before any push.** This catches the other Claude's work. If a rebase produces conflicts, resolve them carefully — usually by keeping both changes, since you and the other Claude are working on different things.

2. **Never `git push --force` or `git push --force-with-lease`.** Period. If you need to "fix history," talk to Phil first via a new request file.

3. **Never delete or rewrite the other Claude's files in `coordination/from-other/`.** Treat the other side's subdirectory as read-only. Only write to your own `from-X/` directory.

4. **Never modify the MuseScore submodule pointer** (the line in `.gitmodules` or the gitlink at `MuseScore`) unless Phil explicitly approves a version bump. If you need a newer upstream, write a request file first. Casual submodule pointer churn would force the other Claude into a full rebuild.

5. **Per-machine file ownership — write only to files in your domain:**

   | File / area | Owner | Notes |
   |-------------|-------|-------|
   | `analyze_*.py`, `align_versions.py`, `musescore_path.py` | Either — pull first | Cross-platform code. Touch with care. |
   | `CLAUDE.md`, `MEMORY.md`, `MEMORY` files | Either — pull first | Common state. Append-only when possible; never wholesale rewrite. |
   | `patches/*.patch` | Either — pull first | Customizations. Don't squash. |
   | `patches/save-patches.sh` / `apply-patches.sh` | Linux Claude primary | |
   | `patches/save-patches.ps1` / `apply-patches.ps1` | Windows Claude primary | |
   | `MuseScore/build/` | Each machine independently | Already gitignored. |
   | `coordination/from-linux/` | Linux Claude only | |
   | `coordination/from-windows/` | Windows Claude only | |

6. **Don't push secrets.** Deploy keys, API keys, Windows passwords, SSH credentials — never commit. Exchange out-of-band via Phil pasting into the other session.

7. **Don't run `git clean -fd` or `rm -rf` on the working tree.** Always investigate unexpected files; they may be the other Claude's in-progress work.

8. **If a push fails as non-fast-forward,** the right response is: `git pull --rebase`, resolve any conflicts, push again. Do NOT `git push --force` to "fix" it.

9. **Each machine has its own git identity and auth.** Don't try to use the other side's deploy key. The Linux side uses the `deploy_key` file in the repo root via the `github-ClaudeMuseScore` SSH alias. The Windows side will use whatever Phil set up there (likely a separate deploy key or PAT). Don't change the other side's auth.

10. **When in doubt, write a coordination message instead of acting.** A 30-second exchange in this directory is cheaper than untangling a botched merge.

## Blast-radius summary (what could go wrong, and what won't)

- **Cannot break MuseScore source:** it's a submodule. Each machine checks out its own copy. The pointer in our repo only changes when explicitly bumped.
- **Cannot break the venv:** `venv/` is gitignored and per-machine.
- **Cannot break the audio cache:** `audio/*` is gitignored.
- **Could conflict on shared files:** `CLAUDE.md`, `MEMORY.md`, `analyze_*.py`. The rebase discipline above mitigates this.
- **Could accidentally rebuild the other machine:** if either changes a MuseScore patch file, the other will be prompted to rebuild on next pull. That's annoying but not destructive.
- **Could lose work via force-push:** the rule against force pushing eliminates this risk.
