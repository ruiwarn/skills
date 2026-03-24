---
name: soul-switch
version: 1.0.0
description: "Switch SOUL.md between normal and evil personas. Triggers: /soul_good, /soul_evil, /soul_status"
allowed-tools:
  - Bash
  - Read
user-invocable: true
---

# Soul Switch Skill

Toggle between normal (SOUL_GOOD.md) and evil (SOUL_EVIL.md) personas by overwriting SOUL.md.

## Trigger Patterns

- `/soul_good`  → restore normal persona
- `/soul_evil`  → activate evil persona (schemer)
- `/soul_status` → show current persona mode

## Usage

```bash
# From skill directory
./scripts/switch.sh status   # check current mode
./scripts/switch.sh good     # switch to normal
./scripts/switch.sh evil     # switch to evil
```

## Post-Switch

After switching, the agent MUST:
1. Run the script to perform the file swap
2. Commit and push the workspace change (SOUL.md)
3. Tell the user to run `/new` to reload the new persona (bootstrap re-injects SOUL.md on session start)

## File Layout

- `SOUL.md` — active persona (injected at bootstrap)
- `SOUL_GOOD.md` — backup of the normal persona
- `SOUL_EVIL.md` — the evil/schemer persona

## Notes

- The switch only takes effect after `/new` or gateway restart (SOUL.md is read at bootstrap time)
- Never delete SOUL_GOOD.md or SOUL_EVIL.md
