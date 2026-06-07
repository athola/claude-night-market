---
name: destructive-command-guard
enabled: true
event: bash
action: warn
conditions:
  - field: command
    operator: regex_match
    pattern: (rm\s+-[rRf]*f[rRf]*\s|git\s+push\s+(-f|--force)|kubectl\s+delete\s|terraform\s+destroy|DROP\s+TABLE|DELETE\s+FROM|psql.*-c\s+'?DROP|psql.*-c\s+'?DELETE|mysql.*-e\s+'?DROP|mysql.*-e\s+'?DELETE)
  - field: command
    operator: regex_match
    pattern: (prod[^a-z]|production|[Pp][Rr][Oo][Dd]_[A-Z]|\blive\b|PROD_|PRODUCTION_|prod\.tfvars|\.prod\.|prod-[a-z]|namespace=prod)
---

Irreversible actions on production systems have caused
real data loss. The Replit/SaaStr incident (July 2025)
erased 1,200 executive records and 1,190 company records
during a code freeze. The design flaw: an agent could
reach a self-destruct button with no affordance making
the wrong action harder than the right one.
(Care, Reversibility)

**WARNING: Destructive command targeting production-shaped path or environment!**

You're about to run a destructive command on what looks
like a production resource.

## Why This Warns

Production data loss is rarely recoverable within an
agent session. This rule fires when:
- `rm -rf`, `git push --force`, `kubectl delete`,
  `terraform destroy`, `DROP TABLE`, or `DELETE FROM`
- **AND** the command references `prod`, `production`,
  `live`, `PROD_*` / `PRODUCTION_*` env-vars, or a
  prod-scoped namespace/workspace

## Before Proceeding, Verify

```bash
# What will this touch?
git diff --stat HEAD          # For git operations
kubectl get <resource> -n production   # For k8s deletes
terraform plan -var-file=prod.tfvars   # For infra ops

# Is there a snapshot or backup?
# Is this inside a code-freeze window?
# Have you confirmed the target environment?
```

## Safer Alternatives

| Destructive command | Safer first step |
|---------------------|-----------------|
| `rm -rf prod/...` | `ls -la prod/` then `mv` to backup |
| `git push --force origin production` | `git log origin/production..HEAD` first |
| `kubectl delete ... -n production` | `kubectl scale --replicas=0` then delete |
| `terraform destroy -var-file=prod.tfvars` | `terraform plan -destroy` first |
| `DROP TABLE` on prod DB | Take a pg_dump/mysqldump snapshot first |

## If You Are Sure

This is a warning rather than a block. The command will run.
If you are certain and want to silence this rule
temporarily:

```bash
# Edit .claude/hookify.destructive-command-guard.local.md
# Set: enabled: false
# Run your command
# Re-enable immediately after
```

## Related

- `block-destructive-git`: blocks irreversible local git ops
- `block-force-push`: blocks force push to main/master
- Source: HN #48022742, Replit/SaaStr incident (2025-07)
