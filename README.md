# team-skills

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
for skills and plugins the team shares.

## Use it

Add the marketplace once, then install whatever you need:

```
/plugin marketplace add spennyw4/team-skills
/plugin install skill-creator@team-skills
```

Browse what's available with `/plugin` , and pull in later changes with
`/plugin marketplace update team-skills`.

To point at a local checkout while developing:

```
/plugin marketplace add ./path/to/team-skills
```

## Layout

```
.claude-plugin/
  marketplace.json          # the marketplace manifest — every plugin is registered here
plugins/
  example-skill-pack/
    .claude-plugin/
      plugin.json           # per-plugin manifest
    skills/
      skill-template/
        SKILL.md            # one directory per skill
  skill-creator/            # vendored from Anthropic's examples (Apache-2.0)
    LICENSE.txt
    NOTICE
    skills/skill-creator/
scripts/
  validate_marketplace.py   # CI-able consistency check
```

A plugin can also carry `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json`,
and `bin/`; each is discovered from its default location without manifest
changes. See the [plugins reference](https://code.claude.com/docs/en/plugins-reference).

## Contribute a skill

The `skill-template` skill in `example-skill-pack` documents the process and is
itself the smallest valid example — read
[`plugins/example-skill-pack/skills/skill-template/SKILL.md`](plugins/example-skill-pack/skills/skill-template/SKILL.md).

The short version:

1. **New skill in an existing plugin** — add
   `plugins/<plugin>/skills/<skill-name>/SKILL.md` with `name` and `description`
   frontmatter. The directory name and the `name` must match.
2. **New plugin** — copy `plugins/example-skill-pack`, edit its
   `.claude-plugin/plugin.json`, then register it in
   `.claude-plugin/marketplace.json` under `plugins` with a
   `"source": "./plugins/<name>"`.
3. Validate and open a PR:

   ```
   python3 scripts/validate_marketplace.py
   ```

### What makes a good `description`

It is the only text Claude sees when deciding whether to load a skill, so lead
with the triggering situation and name the words someone would actually type:

```yaml
# vague — rarely triggers
description: Helps with deployments.

# specific — triggers reliably
description: Use when deploying to staging or production, rolling back a
  release, or debugging a failed deploy. Covers the deploy script, required
  approvals, and how to read the rollout dashboard.
```

## Validation

`scripts/validate_marketplace.py` checks that `marketplace.json` parses, that
every local `source` path exists, that plugin names agree across the marketplace
entry, `plugin.json`, and the directory name, and that each skill has well-formed
frontmatter whose `name` matches its directory. It exits non-zero on any error,
so it can be wired straight into CI.

## Vendored plugins

Some plugins here are copies of third-party skills rather than team-authored
work. Each keeps its upstream license and a `NOTICE` recording provenance and
any modifications:

| Plugin | Upstream | License |
|---|---|---|
| `skill-creator` | Anthropic example skills | Apache-2.0 |

The repository's own MIT `LICENSE` covers team-authored content only; vendored
directories are governed by the license shipped inside them. When refreshing a
vendored copy, diff it against upstream and update its `NOTICE` if anything
diverges.
