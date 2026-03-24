# Cross-Framework Marketability — Project Brief

## Problem Statement

Claude Night Market's 18 plugins contain 100+ skills, 20+ agents,
40+ commands, and 30+ hooks locked into Claude Code.
OpenClaw (220k+ GitHub stars, 13.7k ClawHub skills) and NemoClaw
(NVIDIA enterprise, GTC 2026) represent massive addressable
markets with a ~90% compatible skill format.
The upstream import proposal (openclaw/openclaw#5363) was closed,
so night-market must own the bridge.

## Goals

1. Make night-market skills discoverable and installable via
   ClawHub for OpenClaw and NemoClaw users
2. Expose key capabilities as MCP servers for universal
   framework compatibility (Cline, Cursor, VS Code agents)
3. Publish agents as A2A-compatible agent cards for
   cross-framework agent discovery and delegation
4. Maintain single-source-of-truth: no fork, no drift

## Success Criteria

- [ ] All 100+ skills pass both Claude Code and OpenClaw
      frontmatter validation
- [ ] Converter script generates valid ClawHub packages
- [ ] Bridge plugin installs and loads in OpenClaw
- [ ] At least 5 MCP servers expose core capabilities
- [ ] A2A agent cards published for top agents
- [ ] Zero regression in Claude Code plugin functionality

## Constraints

- **Format**: OpenClaw SKILL.md uses `metadata.openclaw` block;
  Claude Code uses `category`, `tags`, `dependencies`
- **License**: ClawHub requires MIT-0; we use MIT (compatible)
- **Naming**: ClawHub slugs must match `^[a-z0-9][a-z0-9-]*$`
- **Portability**: Commands, agents, hooks have no OpenClaw
  equivalent; must be creatively adapted
- **Security**: NemoClaw adds OpenShell sandbox policies;
  skills must declare filesystem/network needs
- **Size**: ClawHub 50MB bundle limit, text-only files

## Selected Approach: Full Ecosystem Play (Hybrid)

Combine universal frontmatter, bridge plugin, MCP servers,
and A2A agent cards for maximum cross-framework reach.

### Phase 1: Universal Frontmatter + Converter

- Extend SKILL.md frontmatter with OpenClaw-compatible fields
- Build `scripts/clawhub-export.py` converter
- Add `make clawhub-export` target
- Validate dual-schema compliance

### Phase 2: Bridge Plugin + ClawHub Publishing

- Create `night-market` OpenClaw bridge plugin
- Generate `openclaw.plugin.json` manifest
- Map commands to skill equivalents
- Publish top skills to ClawHub registry

### Phase 3: MCP Servers + A2A Agent Cards

- Package core capabilities as MCP servers
- Implement A2A agent card format for top agents
- Add framework auto-detection bootstrapper

## Trade-offs Accepted

- Larger frontmatter in SKILL.md files (dual schema)
- Maintenance of bridge plugin alongside core plugins
- MCP servers expose subset of full skill capabilities
- OpenClaw users get degraded experience vs Claude Code
  (no hooks, no agent orchestration)

## Out of Scope

- Full reimplementation of hooks for OpenClaw
- OpenClaw-to-Claude-Code reverse bridge
- Paid marketplace features
- NemoClaw-specific OpenShell policy generation
  (deferred until NemoClaw exits alpha)

## Next Steps

1. Create specification with acceptance criteria
2. Plan architecture and implementation order
3. Execute all three phases
