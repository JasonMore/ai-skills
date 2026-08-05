---
name: codespace-webstorm
description: Use this skill when the user asks to connect, open, or reconnect an existing GitHub Codespace in WebStorm or JetBrains Gateway through CLI and deep links (no UI automation).
---

# Codespace to WebStorm via JetBrains Gateway

Connects an existing GitHub Codespace to WebStorm remote development. Uses
`gh`, `ssh`, `curl`, and macOS `open` only. Never uses Computer Use or
AppleScript/UI automation.

## When to Use This Skill

- User wants to open an existing codespace in WebStorm through JetBrains
  Gateway.
- User wants a persistent SSH alias for a codespace that Gateway's generic
  "Connect via SSH" flow can use.
- User wants the WebStorm Linux backend installed (or reused) inside the
  codespace automatically.

This skill does not create codespaces. Use the `codespaces` skill for that.

## Prerequisites

- `gh` CLI authenticated with `codespace` scope.
- The target Codespace exists. Pass its name or unique VS Code display name.
- macOS, for the `open` command.
- JetBrains Gateway. If missing, this skill asks for confirmation before
  running `brew install --cask jetbrains-gateway`. It never installs without
  asking.

## Preflight: Check Auth Scope Before Running

An injected `GH_TOKEN` can shadow a keyring token with `codespace` scope:

1. Run `gh auth status` and check whether the active token's scopes include
   `codespace`.
2. If they don't, pass `--use-keyring-auth` (see below) so the script's
   subprocesses ignore the injected token and `gh` falls back to the
   keyring.

## How to Use This Skill

```bash
python3 scripts/open_codespace_webstorm.py --codespace NAME --repo owner/repo
```

After VS Code restarts a stopped Codespace, reconnect WebStorm with:

```bash
python3 scripts/open_codespace_webstorm.py --codespace NAME --repo owner/repo --reconnect
```

- `--reconnect`: skip opening VS Code. Wait for the Codespace and SSH to
  become ready, refresh SSH config, revive the backend, and open a fresh
  Gateway link. Use this after VS Code has restarted and connected.
- `--codespace NAME` (required): the codespace's actual `name`, or its VS
  Code `displayName` (the label shown in VS Code's window title, e.g.
  `stage-ui-for-you-analytics`, which is NOT always the same as the actual
  `name`, e.g. `stage-ui-for-you-analytics-7wvww9grg3xqp6`). The script
  resolves an exact `name` match immediately; otherwise it looks for a
  unique `displayName` match. A display name matching more than one
  codespace fails rather than guessing — pass the exact `name` instead.
- `--repo owner/repo`: derives the remote project path
  `/workspaces/<repo>`. Use `--remote-project-path` instead for a path that
  doesn't match `owner/repo`.
- `--arch`: override the codespace's CPU architecture
  (`x86_64`/`amd64`/`aarch64`/`arm64`). Omit it; the script detects the real
  architecture remotely with `uname -m` and never assumes x86_64.
- `--install-gateway`: pass this only after the user confirms installing
  JetBrains Gateway via Homebrew.
- `--use-keyring-auth`: strip `GH_TOKEN`/`GITHUB_TOKEN` from every child
  subprocess's environment (gh, ssh, curl, and anything ssh's
  `ProxyCommand` execs), forcing `gh` to fall back to its keyring-stored
  credentials. Use this when the preflight check above shows the active
  token lacks `codespace` scope. This process's own environment is never
  touched.
- `--dry-run`: print every command the script would run, and stop. Use this
  first to preview the plan and confirm the codespace name and paths look
  right before doing anything live.
- `--start-timeout` (default 180s) / `--poll-interval` (default 3s): how
  long to poll `remote-dev-server.sh status` for a ready `gatewayLink`
  before failing, and how often to check.
- `--codespace-timeout` (default 180s) / `--ssh-timeout` (default 120s):
  reconnect wait limits for Codespace state and SSH readiness.

Run `--dry-run` first unless the user asks to skip it.

## What the Script Does

1. Resolves `--codespace` to the actual codespace `name` via
   `gh codespace list --json name,displayName,repository,state` (see
   above). Every later stage uses this resolved name.
2. For a first connect, opens the Codespace with `gh codespace code -c NAME`.
   For `--reconnect`, waits for the instance VS Code already started. VS Code
   owns port discovery and forwarding in both cases.
3. Fetches this one codespace's SSH config block with
   `gh codespace ssh -c NAME --config`, then merges/replaces only that
   codespace's `Host` block into the existing `~/.ssh/codespaces` file
   (creating it if missing), in place at its original position. Every
   other byte — other codespaces' blocks (including ones that are
   currently Shutdown), any `Host *` wildcard block, and any preamble
   comments or global directives before the first `Host` line — is
   preserved untouched and in its original order. (`gh codespace ssh
   --config` without `-c` regenerates every visible codespace at once,
   but fails outright if *any* of them isn't
   "Available" — fetching just the target sidesteps that entirely.) Adds
   one `Include ~/.ssh/codespaces` line to `~/.ssh/config` if it isn't
   already there; all other config content is preserved untouched.
4. Parses the SSH alias/user before writing. A reconnect retries SSH while
   the restarted Codespace boots. Auth failures stop at once.
5. Detects the codespace's CPU architecture with `uname -m` (skipped if
   `--arch` was passed).
6. Reuses an existing, verified WebStorm backend on the codespace (checked
   against `product-info.json`, never some other JetBrains product sharing
   the same dist dir), or downloads and installs the latest one from the
   JetBrains releases API. The installed path is always rediscovered and
   re-verified after extraction; a guessed path is never trusted. This is
   the WebStorm IDE backend only — separate from Gateway's own worker
   binary and JetBrains Client (see below), which this skill never touches.
7. Checks for an already-running backend for this project via
   `remote-dev-server.sh status` and reuses its Gateway link if ready.
   Project match uses a literal `projectPath` field or the `gatewayLink`'s
   own `projectPath` param — never `idePath` (the backend install dir).
   Otherwise starts the backend detached (`nohup ... & disown`, logging to
   a stable per-project log file) and polls `status` every
   `--poll-interval` seconds (default 3s) until it reports a ready
   `gatewayLink`, up to `--start-timeout` seconds (default 180s). Never
   waits on `run` itself — it's a long-lived server that never exits.
8. Opens that link with `open -a <Gateway.app>` when a local Gateway.app
   path is known, targeting it explicitly rather than relying only on the
   registered URL handler. Falls back to plain `open` otherwise. This
   dispatches the link; it does not finish the connection (see below).

See `references/cli-flow.md` for the full per-stage detail, exact commands,
and the shell-quoting rules used for remote command construction.

## Error Handling

Each stage fails on its own, with no silent fallback to a different
codespace, repo, backend, or release. Report the failing stage and its
message to the user; do not retry with different assumptions.

## Reconnect After a Stop

The old JetBrains Client cannot restart a backend lost when the Codespace
stopped. Once VS Code shows the Codespace as connected, rerun with
`--reconnect`. The script refreshes SSH, starts or reuses the remote backend,
and opens a fresh Gateway link. Close the stale **No connection** client
window if JetBrains leaves it open.

## Manual Steps (Not Automated)

The first time Gateway or WebStorm launches, the user must accept the EULA
and activate a WebStorm license inside the Gateway/WebStorm window. The
`remote-dev-server.sh` backend may also prompt on its very first run inside
a codespace. This skill cannot and does not automate either step. Tell the
user to expect it, and if the run hangs or fails on a brand-new codespace,
suggest SSHing in once to run the backend interactively and accept the
prompt, then retrying.

Gateway prefills its SSH form but does not click **Check Connection and
Continue**. The user must click it after every connect or reconnect. This
skill does not automate that UI step.

After Continue, Gateway manages its worker and JetBrains Client. This skill
manages only the remote WebStorm backend.

## Boundaries

**Will:**
- Resolve a codespace by its actual name or unique displayName; refuse to
  guess on ambiguous display names.
- Reuse an existing codespace and its SSH connection.
- Keep `~/.ssh/config` and `~/.ssh/codespaces` in sync, non-destructively,
  merging in only the target codespace's block and preserving every other
  codespace's alias untouched.
- Install or reuse a verified WebStorm backend on the codespace.
- Reuse an already-running remote-dev-server backend for the same project
  instead of starting a duplicate.
- Detect the codespace's CPU architecture instead of assuming one.
- Open the Gateway deep link with `open`, targeting the known Gateway.app
  path explicitly when possible. This dispatches the link; it does not
  click through Gateway's own connection-confirmation UI.
- Strip injected `GH_TOKEN`/`GITHUB_TOKEN` from its own subprocesses only,
  when `--use-keyring-auth` is passed.

**Will not:**
- Create, delete, or rebuild codespaces.
- Use AppleScript, `osascript`, or any Computer Use/UI automation.
- Install JetBrains Gateway without explicit user confirmation.
- Fall back to a different codespace, repo, backend, or release on failure.
- Automate the Gateway/WebStorm EULA or license activation.
- Click Gateway's "Check Connection and Continue" button or otherwise
  finish the connection after opening the link — that is a manual step.
- Install, upload, or manage Gateway's own worker binary or the local
  JetBrains Client — Gateway handles both itself once the user confirms.
- Guess which codespace a duplicate or absent displayName refers to.
