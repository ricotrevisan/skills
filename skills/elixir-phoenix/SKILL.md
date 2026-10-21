---
name: elixir-phoenix
description: Elixir/Phoenix conventions for Rico's projects. Use when setting up or starting work in a Phoenix worktree (`mix setup`), when a Mix or PubSub socket error such as `:eperm` blocks a command, when editing an Ash resource, domain, or controller, or when adding or choosing an HTTP client.
---

# Elixir / Phoenix

Conventions for Elixir and Phoenix work in Rico's projects. Each section is a branch — reach it when it applies.

A project's own `AGENTS.md` holds that app's specifics and overrides anything here; this skill carries only what is common across Rico's Elixir projects.

## New worktree

In a fresh worktree that contains a Phoenix app, run `mix setup` before development, unless Rico opts out. It installs dependencies and prepares the database; commands run before it fail on missing setup.

## HTTP clients

Use Req for outbound HTTP. Don't add HTTPoison, hackney or Tesla. Req's Mint transport verifies against the OS CA store, so a CA incident is fixed by an image rebuild; hackney pins its own certifi bundle.

- Swoosh: `Swoosh.ApiClient.Req` (or `Finch`).
- ExAws: `config :ex_aws, http_client: ExAws.Request.Req`.

## Mix socket errors: `:eperm`

A `:eperm` on a local socket from `Mix.PubSub` usually means the sandbox, not a filesystem permission problem. Retry the command with authorized escalation. When escalation is unavailable, report the blocker — the command needs the sandbox lifted, not a workaround.

## Ash projects

In an Ash app, the resource action is the unit of data access.

- Data access lives in resource actions and domains.
- A controller parses params, calls an action, renders the result — a thin adapter.
- A raw SQL or Ecto query in a controller is the exception, and needs Rico's OK.
