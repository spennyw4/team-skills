---
name: skill-template
description: Use when adding a new skill or plugin to the team-skills marketplace, or when reviewing one before merge. Covers the directory layout, the SKILL.md frontmatter contract, how to register a plugin in .claude-plugin/marketplace.json, and how to validate the repo locally.
---

# Authoring a skill in this marketplace

This skill is both documentation and a working example — the directory you are
reading is the smallest complete plugin this marketplace accepts.

## Add a skill to an existing plugin

1. Create `plugins/<plugin>/skills/<skill-name>/SKILL.md`.
2. Give it frontmatter with exactly two required keys:

   ```yaml
   ---
   name: my-skill
   description: Use when <the situation that should trigger this>. <What it does.>
   ---
   ```

   - `name` must be kebab-case and match the directory name.
   - `description` is the only thing Claude sees when deciding whether to load
     the skill. Lead with the trigger condition ("Use when…"), not a summary of
     the contents. Name the concrete nouns a user would actually type.
3. Write the body as instructions to Claude, not prose about Claude. Keep it
   short; put long reference material in sibling files and link to them.
4. Run `python3 scripts/validate_marketplace.py`.

## Add a new plugin

1. Copy this directory:

   ```bash
   cp -r plugins/example-skill-pack plugins/<new-plugin>
   ```

2. Edit `plugins/<new-plugin>/.claude-plugin/plugin.json` — at minimum `name`
   (kebab-case, must match the directory name), `description`, `version`.
3. Register it in the root `.claude-plugin/marketplace.json` under `plugins`:

   ```json
   {
     "name": "<new-plugin>",
     "source": "./plugins/<new-plugin>",
     "description": "...",
     "version": "0.1.0"
   }
   ```

   The entry `name` must match the `name` in that plugin's `plugin.json`.
4. Run the validator, then open a PR.

## What else a plugin can hold

`skills/` is the common case. The same plugin directory can also carry
`commands/` (flat `.md` slash commands), `agents/` (subagent definitions),
`hooks/hooks.json`, `.mcp.json` (MCP servers), and `bin/` (executables added to
PATH). Each is picked up from its default location with no manifest changes.

## Review checklist

- [ ] `name` matches the directory name, in kebab-case
- [ ] `description` starts with the trigger condition and names real keywords
- [ ] No secrets, tokens, internal hostnames, or customer data in the body
- [ ] Plugin registered in `.claude-plugin/marketplace.json` (new plugins only)
- [ ] `python3 scripts/validate_marketplace.py` passes
