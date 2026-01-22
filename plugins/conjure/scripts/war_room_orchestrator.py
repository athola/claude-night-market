#!/usr/bin/env python3
"""War Room Orchestrator.

Orchestrates multi-LLM deliberation sessions for strategic decision making.
Composes delegation calls to manage expert panels, anonymization, and synthesis.

Note: Uses asyncio.create_subprocess_exec (safe, no shell injection).

Usage:
    from war_room_orchestrator import WarRoomOrchestrator

    orchestrator = WarRoomOrchestrator()
    session = await orchestrator.convene(
        problem="What architecture should we use?",
        context_files=["src/**/*.py"],
        mode="lightweight"
    )
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess  # nosec B404 - Used safely with create_subprocess_exec (no shell)
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class DeliberationNode:
    """A single contribution in the deliberation graph."""

    node_id: str
    parent_id: str | None
    round_number: int
    phase: str
    anonymous_label: str
    content: str
    expert_role: str
    expert_model: str
    content_hash: str
    metadata_hash: str
    combined_hash: str
    timestamp: str


@dataclass
class MerkleDAG:
    """Directed Acyclic Graph tracking deliberation history."""

    session_id: str
    sealed: bool = True
    root_hash: str | None = None
    nodes: dict[str, DeliberationNode] = field(default_factory=dict)
    label_counter: dict[str, int] = field(default_factory=dict)

    def add_contribution(  # noqa: PLR0913
        self,
        content: str,
        phase: str,
        round_number: int,
        expert_role: str,
        expert_model: str,
        parent_id: str | None = None,
    ) -> DeliberationNode:
        """Add a contribution and compute hashes."""
        content_hash = sha256(content.encode()).hexdigest()
        metadata_hash = sha256(f"{expert_role}:{expert_model}".encode()).hexdigest()
        combined_hash = sha256(f"{content_hash}:{metadata_hash}".encode()).hexdigest()

        label = self._generate_label(phase)

        node = DeliberationNode(
            node_id=combined_hash[:16],
            parent_id=parent_id,
            round_number=round_number,
            phase=phase,
            anonymous_label=label,
            content=content,
            expert_role=expert_role,
            expert_model=expert_model,
            content_hash=content_hash,
            metadata_hash=metadata_hash,
            combined_hash=combined_hash,
            timestamp=datetime.now().isoformat(),
        )

        self.nodes[node.node_id] = node
        self._update_root_hash()
        return node

    def _generate_label(self, phase: str) -> str:
        """Generate anonymous label for phase."""
        if phase not in self.label_counter:
            self.label_counter[phase] = 0
        self.label_counter[phase] += 1
        count = self.label_counter[phase]

        if phase == "coa":
            return f"Response {chr(64 + count)}"  # A, B, C...
        return f"Expert {count}"

    def _update_root_hash(self) -> None:
        """Update root hash from all leaf nodes."""
        if not self.nodes:
            self.root_hash = None
            return
        combined = ":".join(sorted(n.combined_hash for n in self.nodes.values()))
        self.root_hash = sha256(combined.encode()).hexdigest()

    def get_anonymized_view(self, phase: str | None = None) -> list[dict[str, Any]]:
        """Return contributions with attribution masked."""
        nodes_iter = list(self.nodes.values())
        if phase:
            nodes_iter = [n for n in nodes_iter if n.phase == phase]
        return [
            {
                "label": node.anonymous_label,
                "content": node.content,
                "phase": node.phase,
                "round": node.round_number,
                "hash": node.node_id,
            }
            for node in nodes_iter
        ]

    def unseal(self) -> list[dict[str, Any]]:
        """Reveal full attribution after decision is made."""
        self.sealed = False
        return [
            {
                "label": node.anonymous_label,
                "content": node.content,
                "phase": node.phase,
                "round": node.round_number,
                "expert_role": node.expert_role,
                "expert_model": node.expert_model,
                "hash": node.node_id,
            }
            for node in self.nodes.values()
        ]

    def to_dict(self) -> dict[str, Any]:
        """Serialize for persistence."""
        return {
            "session_id": self.session_id,
            "sealed": self.sealed,
            "root_hash": self.root_hash,
            "label_counter": self.label_counter,
            "nodes": {
                nid: {
                    "node_id": n.node_id,
                    "parent_id": n.parent_id,
                    "round_number": n.round_number,
                    "phase": n.phase,
                    "anonymous_label": n.anonymous_label,
                    "content": n.content,
                    "expert_role": n.expert_role if not self.sealed else "[SEALED]",
                    "expert_model": n.expert_model if not self.sealed else "[SEALED]",
                    "content_hash": n.content_hash,
                    "metadata_hash": n.metadata_hash,
                    "combined_hash": n.combined_hash,
                    "timestamp": n.timestamp,
                }
                for nid, n in self.nodes.items()
            },
        }


@dataclass
class ExpertConfig:
    """Configuration for a War Room expert."""

    role: str
    service: str
    model: str
    description: str
    phases: list[str]
    dangerous: bool = True
    command: list[str] | None = None
    command_resolver: str | None = None


@dataclass
class WarRoomSession:
    """Active War Room deliberation session."""

    session_id: str
    problem_statement: str
    mode: str = "lightweight"
    status: str = "initialized"
    merkle_dag: MerkleDAG = field(default_factory=lambda: MerkleDAG(""))
    phases_completed: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    escalated: bool = False
    escalation_reason: str | None = None

    def __post_init__(self) -> None:
        """Initialize session with session_id on merkle_dag if not set."""
        if not self.merkle_dag.session_id:
            self.merkle_dag.session_id = self.session_id


# ---------------------------------------------------------------------------
# Expert Configuration
# ---------------------------------------------------------------------------

EXPERT_CONFIGS: dict[str, ExpertConfig] = {
    "supreme_commander": ExpertConfig(
        role="Supreme Commander",
        service="native",
        model="claude-opus-4",
        description="Final decision authority and synthesis",
        phases=["synthesis"],
        dangerous=False,
    ),
    "chief_strategist": ExpertConfig(
        role="Chief Strategist",
        service="native",
        model="claude-sonnet-4",
        description="Approach generation and trade-off analysis",
        phases=["assessment", "coa"],
        dangerous=False,
    ),
    "intelligence_officer": ExpertConfig(
        role="Intelligence Officer",
        service="gemini",
        model="gemini-2.5-pro-exp",
        description="Deep context analysis with 1M+ token window",
        phases=["intel"],
        command=["gemini", "--model", "gemini-2.5-pro-exp", "-p"],
    ),
    "field_tactician": ExpertConfig(
        role="Field Tactician",
        service="glm",
        model="glm-4.7",
        description="Implementation feasibility assessment",
        phases=["coa"],
        command_resolver="get_glm_command",
    ),
    "scout": ExpertConfig(
        role="Scout",
        service="qwen",
        model="qwen-turbo",
        description="Rapid reconnaissance and data gathering",
        phases=["intel"],
        command=["qwen", "--model", "qwen-turbo", "-p"],
    ),
    "red_team": ExpertConfig(
        role="Red Team Commander",
        service="gemini",
        model="gemini-2.0-flash-exp",
        description="Adversarial challenge and failure mode identification",
        phases=["red_team", "premortem"],
        command=["gemini", "--model", "gemini-2.0-flash-exp", "-p"],
    ),
    "logistics_officer": ExpertConfig(
        role="Logistics Officer",
        service="qwen",
        model="qwen-max",
        description="Resource estimation and dependency analysis",
        phases=["coa"],
        command=["qwen", "--model", "qwen-max", "-p"],
    ),
}

LIGHTWEIGHT_PANEL = ["supreme_commander", "chief_strategist", "red_team"]
FULL_COUNCIL = list(EXPERT_CONFIGS.keys())

# Track which experts have been tested and their availability
_expert_availability: dict[str, bool] = {}
_haiku_fallback_notices: list[str] = []


# ---------------------------------------------------------------------------
# Command Resolution
# ---------------------------------------------------------------------------


def get_haiku_command() -> list[str]:
    """Get command to invoke Claude Haiku as fallback.

    Used when external LLMs (Gemini, Qwen, GLM) are unavailable.
    Provides diversity through smaller/faster Claude model.
    """
    if shutil.which("claude"):
        return ["claude", "--model", "claude-haiku-3", "-p"]
    raise RuntimeError("Claude CLI not found - cannot use Haiku fallback")


async def test_expert_availability(expert: ExpertConfig) -> bool:
    """Test if an external expert is available with a lightweight probe.

    Returns True if expert responds successfully, False otherwise.
    Results are cached to avoid repeated probes.
    """
    cache_key = f"{expert.service}:{expert.model}"

    # Check cache first
    if cache_key in _expert_availability:
        return _expert_availability[cache_key]

    # Native experts are always available
    if expert.service == "native":
        _expert_availability[cache_key] = True
        return True

    try:
        cmd = get_expert_command(expert)
        # Use minimal probe prompt
        probe_cmd = cmd + ["respond with 'ok'"]

        proc = await asyncio.create_subprocess_exec(
            *probe_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=10.0)

        available = proc.returncode == 0
        _expert_availability[cache_key] = available
        return available

    except (TimeoutError, FileNotFoundError, RuntimeError):
        _expert_availability[cache_key] = False
        return False


def get_fallback_notice() -> str:
    """Get accumulated fallback notices for user display."""
    if not _haiku_fallback_notices:
        return ""
    notices = "\n".join(f"  - {n}" for n in _haiku_fallback_notices)
    return f"\n⚠️ External LLM Fallbacks:\n{notices}\n"


def clear_availability_cache() -> None:
    """Clear the expert availability cache (useful for testing)."""
    _expert_availability.clear()
    _haiku_fallback_notices.clear()


def get_glm_command() -> list[str]:
    """Resolve GLM-4.7 invocation command with fallback.

    Priority:
    1. ccgd (alias) - if available in PATH
    2. claude-glm --dangerously-skip-permissions - explicit fallback
    3. ~/.local/bin/claude-glm - direct path fallback
    """
    if shutil.which("ccgd"):
        return ["ccgd", "-p"]

    if shutil.which("claude-glm"):
        return ["claude-glm", "--dangerously-skip-permissions", "-p"]

    local_bin = Path.home() / ".local" / "bin" / "claude-glm"
    if local_bin.exists():
        return [str(local_bin), "--dangerously-skip-permissions", "-p"]

    raise RuntimeError(
        "GLM-4.7 not available. Install claude-glm or configure ccgd alias.\n"
        "Add to ~/.bashrc: alias ccgd='claude-glm --dangerously-skip-permissions'"
    )


def get_expert_command(expert: ExpertConfig) -> list[str]:
    """Get the command to invoke an expert."""
    if expert.command_resolver:
        resolver = globals().get(expert.command_resolver)
        if resolver and callable(resolver):
            cmd = resolver()
            if isinstance(cmd, list):
                return cmd
            raise RuntimeError(
                f"Resolver {expert.command_resolver} did not return list"
            )
        raise RuntimeError(f"Unknown command resolver: {expert.command_resolver}")
    if expert.command:
        return expert.command.copy()
    raise RuntimeError(f"No command configured for {expert.role}")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class WarRoomOrchestrator:
    """Orchestrates multi-LLM deliberation sessions.

    Responsibilities:
    - Expert panel management
    - Phase sequencing
    - Parallel dispatch
    - Response aggregation
    - Merkle-DAG maintenance
    - Strategeion persistence
    """

    def __init__(self, strategeion_path: Path | None = None) -> None:
        """Initialize orchestrator with Strategeion storage path."""
        self.strategeion = strategeion_path or (
            Path.home() / ".claude" / "memory-palace" / "strategeion"
        )
        self.strategeion.mkdir(parents=True, exist_ok=True)

    async def convene(
        self,
        problem: str,
        context_files: list[str] | None = None,
        mode: str = "lightweight",
    ) -> WarRoomSession:
        """Convene a new War Room session.

        Args:
            problem: The problem/decision to deliberate
            context_files: Optional file globs for context
            mode: "lightweight" or "full_council"

        Returns:
            Completed WarRoomSession with decision

        """
        # Clear availability cache for fresh session
        clear_availability_cache()

        session = self._initialize_session(problem, mode)
        session.metrics["start_time"] = datetime.now().isoformat()

        try:
            # Phase 1: Intelligence
            await self._phase_intel(session, context_files)

            # Phase 2: Assessment
            await self._phase_assessment(session)

            # Phase 3: COA Development
            await self._phase_coa_development(session)

            # Escalation check
            if mode == "lightweight" and await self._should_escalate(session):
                session.escalated = True
                session.mode = "full_council"
                await self._escalate(session, context_files)

            # Phase 4: Red Team
            await self._phase_red_team(session)

            # Phase 5: Voting
            await self._phase_voting(session)

            # Phase 6: Premortem
            await self._phase_premortem(session)

            # Phase 7: Synthesis
            await self._phase_synthesis(session)

            session.status = "completed"

        except Exception as e:
            session.status = f"failed: {e}"
            raise

        finally:
            session.metrics["end_time"] = datetime.now().isoformat()
            # Capture any fallback notices
            fallback_notice = get_fallback_notice()
            if fallback_notice:
                session.artifacts["fallback_notice"] = fallback_notice
            self._persist_session(session)

        return session

    def _initialize_session(self, problem: str, mode: str) -> WarRoomSession:
        """Create new session with unique ID."""
        session_id = f"war-room-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return WarRoomSession(
            session_id=session_id,
            problem_statement=problem,
            mode=mode,
            merkle_dag=MerkleDAG(session_id),
        )

    async def _invoke_expert(
        self,
        expert_key: str,
        prompt: str,
        session: WarRoomSession,
        phase: str,
    ) -> str:
        """Invoke a single expert and record contribution.

        For external LLMs (Gemini, Qwen, GLM), tests availability first.
        Falls back to Haiku if external LLM is unavailable.
        """
        expert = EXPERT_CONFIGS[expert_key]
        actual_model = expert.model

        if expert.service == "native":
            # Native experts (Opus, Sonnet) handled by orchestrating Claude
            result = f"[Native expert {expert.role} response placeholder]"
        elif await test_expert_availability(expert):
            # External expert is available - invoke directly
            result = await self._invoke_external(expert, prompt)
        else:
            # Fallback to Haiku
            actual_model = "claude-haiku-3"
            notice = (
                f"{expert.role} ({expert.model}) unavailable, using Haiku as fallback"
            )
            if notice not in _haiku_fallback_notices:
                _haiku_fallback_notices.append(notice)
            result = await self._invoke_haiku_fallback(expert, prompt)

        # Record in Merkle-DAG
        session.merkle_dag.add_contribution(
            content=result,
            phase=phase,
            round_number=len(session.phases_completed) + 1,
            expert_role=expert.role,
            expert_model=actual_model,
        )

        return result

    async def _invoke_haiku_fallback(self, expert: ExpertConfig, prompt: str) -> str:
        """Invoke Haiku as fallback for unavailable external expert.

        Prefixes prompt with role context to maintain expert perspective.
        """
        role_prefix = (
            f"You are acting as the {expert.role} in a strategic War Room.\n"
            f"Your expertise: {expert.description}\n\n"
        )
        full_prompt = role_prefix + prompt

        try:
            cmd = get_haiku_command()
            cmd.append(full_prompt)

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=120.0,
            )

            if proc.returncode != 0:
                err = stderr.decode()[:500]
                return f"[{expert.role} (Haiku fallback) failed: {err}]"

            return stdout.decode()

        except TimeoutError:
            return f"[{expert.role} (Haiku fallback) timed out after 120s]"
        except FileNotFoundError:
            return f"[{expert.role} fallback failed: Claude CLI not found]"
        except Exception as e:
            return f"[{expert.role} (Haiku fallback) error: {e}]"

    async def _invoke_external(self, expert: ExpertConfig, prompt: str) -> str:
        """Invoke external expert via CLI.

        Uses asyncio.create_subprocess_exec (safe, no shell injection).
        Arguments passed as list, not through shell.
        """
        cmd = get_expert_command(expert)
        cmd.append(prompt)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=120.0,
            )

            if proc.returncode != 0:
                return f"[{expert.role} failed: {stderr.decode()[:500]}]"

            return stdout.decode()

        except TimeoutError:
            return f"[{expert.role} timed out after 120s]"
        except FileNotFoundError:
            return f"[{expert.role} command not found: {cmd[0]}]"
        except Exception as e:
            return f"[{expert.role} error: {e}]"

    async def _invoke_parallel(
        self,
        expert_keys: list[str],
        prompts: dict[str, str],
        session: WarRoomSession,
        phase: str,
    ) -> dict[str, str]:
        """Invoke multiple experts in parallel."""
        tasks = {
            key: self._invoke_expert(
                key, prompts.get(key, prompts.get("default", "")), session, phase
            )
            for key in expert_keys
            if key in EXPERT_CONFIGS
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        output: dict[str, str] = {}
        for key, result in zip(tasks.keys(), results, strict=False):
            if isinstance(result, BaseException):
                output[key] = f"[Error: {result}]"
            elif isinstance(result, str):
                output[key] = result
            else:
                output[key] = str(result)  # type: ignore[unreachable]
        return output

    # ---------------------------------------------------------------------------
    # Prompt Templates
    # ---------------------------------------------------------------------------

    INTEL_PROMPT_SCOUT = """You are the Scout in a strategic War Room deliberation.

MISSION: Rapid reconnaissance of the problem terrain.

PROBLEM STATEMENT:
{problem}

CONTEXT FILES PROVIDED: {context_files}

Provide a concise reconnaissance report covering:
1. **Terrain Overview**: What kind of problem is this?
   (architecture, design, trade-off, etc.)
2. **Key Landmarks**: Major components, systems, or concepts involved
3. **Potential Hazards**: Obvious risks or constraints
4. **Quick Wins**: Any low-hanging fruit or clear opportunities

Keep response under 500 words. Speed over depth."""

    INTEL_PROMPT_OFFICER = """You are the Intelligence Officer in War Room deliberation.

MISSION: Deep analysis of problem context using your extended context window.

PROBLEM STATEMENT:
{problem}

CONTEXT FILES PROVIDED: {context_files}

Provide a comprehensive intelligence report covering:
1. **Context Analysis**: Deep dive into provided files and their relationships
2. **Historical Patterns**: Similar decisions or approaches in the codebase
3. **Dependencies**: What systems/components would be affected
4. **Constraints**: Technical, organizational, or resource limitations
5. **Unknowns**: What information is missing that would aid decision-making

Be thorough. Use your large context window to full advantage."""

    ASSESSMENT_PROMPT = """You are the Chief Strategist in War Room deliberation.

MISSION: Synthesize intelligence into actionable strategic assessment.

PROBLEM STATEMENT:
{problem}

SCOUT REPORT:
{scout_report}

INTELLIGENCE REPORT:
{intel_report}

Provide a situation assessment covering:
1. **Refined Problem Statement**: Clarify the core decision to be made
2. **Prioritized Constraints**: Rank the most important limitations (1-5)
3. **Strategic Opportunities**: What advantages can we leverage?
4. **COA Guidance**: What types of approaches should experts consider?
5. **Success Criteria**: How will we know we made the right choice?

Be decisive. This assessment guides all subsequent analysis."""

    COA_PROMPT = """You are {role} in a strategic War Room deliberation.

MISSION: Develop a distinct course of action (COA) for this decision.

PROBLEM STATEMENT:
{problem}

SITUATION ASSESSMENT:
{assessment}

YOUR EXPERTISE: {expertise}

Propose ONE well-developed course of action:

## COA: [Name]

### Summary
[2-3 sentence description]

### Approach
[Detailed approach - what would we actually do?]

### Pros
- [Advantage 1]
- [Advantage 2]
- [...]

### Cons
- [Disadvantage 1]
- [Disadvantage 2]
- [...]

### Risks
- [Risk 1 with mitigation]
- [Risk 2 with mitigation]

### Effort Estimate
[Low/Medium/High with justification]

Think differently from other experts. Your COA should reflect your perspective."""

    RED_TEAM_PROMPT = """You are the Red Team Commander in War Room deliberation.

MISSION: Challenge all proposed courses of action. Find weaknesses.

PROBLEM STATEMENT:
{problem}

PROPOSED COAs (ANONYMIZED):
{anonymized_coas}

For EACH COA, provide:

## Challenge: [COA Label]

### Hidden Assumptions
- [Assumption that might not hold]

### Failure Scenarios
- [How this could fail catastrophically]

### Blind Spots
- [What the proposer might have missed]

### Cross-cutting Concerns
- [Issues that affect multiple COAs]

### Severity Rating
[Critical / High / Medium / Low]

Be adversarial but constructive. Your job is to make the final decision stronger."""

    VOTING_PROMPT = """You are {role} participating in War Room COA voting.

PROBLEM STATEMENT:
{problem}

COAs WITH RED TEAM CHALLENGES:
{coas_with_challenges}

Rank all COAs from best to worst. For each:

1. [COA Label] - [1-2 sentence justification]
2. [COA Label] - [1-2 sentence justification]
...

End with your TOP PICK and one sentence why."""

    PREMORTEM_PROMPT = """You are {role} participating in a premortem analysis.

MISSION: Imagine we chose this approach and it FAILED. Why did it fail?

SELECTED APPROACH:
{selected_coa}

PROBLEM CONTEXT:
{problem}

Imagine it's 6 months from now. This approach was implemented and it failed badly.

1. **What Went Wrong**: Describe the failure vividly
2. **Early Warning Signs**: What signals should we have watched for?
3. **Root Cause**: Why did we miss this?
4. **Prevention**: What could we do NOW to prevent this failure?
5. **Contingency**: If we see early warnings, what's the fallback?

Be pessimistic. Your imagination of failure helps us succeed."""

    SYNTHESIS_PROMPT = """You are the Supreme Commander making the final decision.

PROBLEM STATEMENT:
{problem}

FULL DELIBERATION RECORD:
---
Intelligence Reports:
{intel}

Situation Assessment:
{assessment}

All COAs (with attribution):
{coas_unsealed}

Red Team Challenges:
{red_team}

Expert Votes:
{voting}

Premortem Analysis:
{premortem}
---

Make your final decision. Output format:

## SUPREME COMMANDER DECISION

### Decision
**Selected Approach**: [Name]

### Rationale
[2-3 paragraphs explaining why this approach was selected over alternatives]

### Implementation Orders
1. [ ] [Immediate action]
2. [ ] [Short-term action]
3. [ ] [Medium-term action]

### Watch Points
[From premortem - what to monitor for early warning signs]

### Dissenting Views
[Acknowledge valuable opposing perspectives for the record]

### Confidence Level
[High / Medium / Low with explanation]

Make a decisive call. The council has deliberated; now you must decide."""

    # ---------------------------------------------------------------------------
    # Phase Implementations
    # ---------------------------------------------------------------------------

    async def _phase_intel(
        self, session: WarRoomSession, context_files: list[str] | None
    ) -> None:
        """Phase 1: Intelligence Gathering (Scout + Intel Officer in parallel)."""
        context_str = ", ".join(context_files) if context_files else "None provided"
        experts_to_invoke = []
        prompts: dict[str, str] = {}

        # Scout always runs (fast, cheap)
        prompts["scout"] = self.INTEL_PROMPT_SCOUT.format(
            problem=session.problem_statement,
            context_files=context_str,
        )
        experts_to_invoke.append("scout")

        # Intel Officer only in full council mode
        if session.mode == "full_council":
            prompts["intelligence_officer"] = self.INTEL_PROMPT_OFFICER.format(
                problem=session.problem_statement,
                context_files=context_str,
            )
            experts_to_invoke.append("intelligence_officer")

        results = await self._invoke_parallel(
            experts_to_invoke, prompts, session, "intel"
        )

        session.artifacts["intel"] = {
            "scout_report": results.get("scout", "[Scout unavailable]"),
            "intel_report": results.get(
                "intelligence_officer", "[Intel Officer not invoked - lightweight mode]"
            ),
            "context_files": context_files,
        }
        session.phases_completed.append("intel")

    async def _phase_assessment(self, session: WarRoomSession) -> None:
        """Phase 2: Situation Assessment (Chief Strategist)."""
        intel = session.artifacts.get("intel", {})

        prompt = self.ASSESSMENT_PROMPT.format(
            problem=session.problem_statement,
            scout_report=intel.get("scout_report", "N/A"),
            intel_report=intel.get("intel_report", "N/A"),
        )

        # Chief Strategist is native (Sonnet) - invoke directly
        result = await self._invoke_expert(
            "chief_strategist", prompt, session, "assessment"
        )

        session.artifacts["assessment"] = {
            "content": result,
        }
        session.phases_completed.append("assessment")

    async def _phase_coa_development(self, session: WarRoomSession) -> None:
        """Phase 3: COA Development (parallel, anonymized)."""
        assessment = session.artifacts.get("assessment", {}).get("content", "N/A")

        experts_to_invoke = ["chief_strategist"]  # Always includes strategist
        if session.mode == "full_council":
            experts_to_invoke.extend(["field_tactician", "logistics_officer"])

        expertise_map = {
            "chief_strategist": "Strategic architecture and long-term viability",
            "field_tactician": "Implementation feasibility and technical complexity",
            "logistics_officer": "Resource requirements and dependency management",
        }

        prompts: dict[str, str] = {}
        for expert_key in experts_to_invoke:
            expert = EXPERT_CONFIGS.get(expert_key)
            if expert:
                prompts[expert_key] = self.COA_PROMPT.format(
                    role=expert.role,
                    problem=session.problem_statement,
                    assessment=assessment,
                    expertise=expertise_map.get(expert_key, "General analysis"),
                )

        results = await self._invoke_parallel(
            experts_to_invoke, prompts, session, "coa"
        )

        # Store raw COAs (with attribution sealed in Merkle-DAG)
        session.artifacts["coa"] = {
            "raw_coas": results,
            "count": len(results),
        }
        session.phases_completed.append("coa")

    async def _should_escalate(self, session: WarRoomSession) -> bool:
        """Check if Supreme Commander should escalate to full council.

        Escalation triggers:
        1. COA count < 2 (need more perspectives)
        2. Keywords indicating complexity in assessment
        3. High disagreement detected (placeholder for future)
        """
        coa_count = session.artifacts.get("coa", {}).get("count", 0)
        if coa_count < 2:
            session.escalation_reason = "Insufficient COA diversity"
            return True

        assessment = session.artifacts.get("assessment", {}).get("content", "")
        complexity_keywords = [
            "complex",
            "trade-off",
            "significant risk",
            "irreversible",
            "architectural",
            "migration",
            "breaking change",
            "high stakes",
        ]
        assessment_lower = assessment.lower()
        complexity_hits = sum(1 for kw in complexity_keywords if kw in assessment_lower)
        if complexity_hits >= 3:
            session.escalation_reason = (
                f"High complexity detected ({complexity_hits} indicators)"
            )
            return True

        return False

    async def _escalate(
        self, session: WarRoomSession, context_files: list[str] | None
    ) -> None:
        """Escalate to full council by invoking additional experts."""
        session.mode = "full_council"

        # Invoke additional intel if not already done
        if "intel_report" not in session.artifacts.get("intel", {}):
            context_str = ", ".join(context_files) if context_files else "None"
            prompt = self.INTEL_PROMPT_OFFICER.format(
                problem=session.problem_statement,
                context_files=context_str,
            )
            result = await self._invoke_expert(
                "intelligence_officer", prompt, session, "intel"
            )
            session.artifacts["intel"]["intel_report"] = result

        # Get additional COAs from new experts
        assessment = session.artifacts.get("assessment", {}).get("content", "N/A")
        additional_experts = ["field_tactician", "logistics_officer"]

        expertise_map = {
            "field_tactician": "Implementation feasibility and technical complexity",
            "logistics_officer": "Resource requirements and dependency management",
        }

        prompts: dict[str, str] = {}
        for expert_key in additional_experts:
            expert = EXPERT_CONFIGS.get(expert_key)
            if expert:
                prompts[expert_key] = self.COA_PROMPT.format(
                    role=expert.role,
                    problem=session.problem_statement,
                    assessment=assessment,
                    expertise=expertise_map.get(expert_key, "General analysis"),
                )

        results = await self._invoke_parallel(
            additional_experts, prompts, session, "coa"
        )

        # Merge with existing COAs
        existing_coas = session.artifacts.get("coa", {}).get("raw_coas", {})
        existing_coas.update(results)
        session.artifacts["coa"]["raw_coas"] = existing_coas
        session.artifacts["coa"]["count"] = len(existing_coas)
        session.artifacts["coa"]["escalated"] = True

    async def _phase_red_team(self, session: WarRoomSession) -> None:
        """Phase 4: Red Team Challenge."""
        # Get anonymized view of COAs
        anonymized_coas = session.merkle_dag.get_anonymized_view(phase="coa")
        coas_text = "\n\n---\n\n".join(
            f"### {coa['label']}\n{coa['content']}" for coa in anonymized_coas
        )

        prompt = self.RED_TEAM_PROMPT.format(
            problem=session.problem_statement,
            anonymized_coas=coas_text,
        )

        result = await self._invoke_expert("red_team", prompt, session, "red_team")

        session.artifacts["red_team"] = {
            "challenges": result,
            "coas_reviewed": len(anonymized_coas),
        }
        session.phases_completed.append("red_team")

    async def _phase_voting(self, session: WarRoomSession) -> None:
        """Phase 5: Voting and Narrowing using Borda count."""
        # Prepare COAs with Red Team challenges
        anonymized_coas = session.merkle_dag.get_anonymized_view(phase="coa")
        challenges = session.artifacts.get("red_team", {}).get("challenges", "N/A")

        coas_with_challenges = "\n\n".join(
            f"### {coa['label']}\n{coa['content']}" for coa in anonymized_coas
        )
        coas_with_challenges += f"\n\n## RED TEAM CHALLENGES\n{challenges}"

        # Get active panel for voting
        panel = FULL_COUNCIL if session.mode == "full_council" else LIGHTWEIGHT_PANEL
        voting_experts = [e for e in panel if e != "supreme_commander"]

        prompts: dict[str, str] = {}
        for expert_key in voting_experts:
            expert = EXPERT_CONFIGS.get(expert_key)
            if expert:
                prompts[expert_key] = self.VOTING_PROMPT.format(
                    role=expert.role,
                    problem=session.problem_statement,
                    coas_with_challenges=coas_with_challenges,
                )

        results = await self._invoke_parallel(
            voting_experts, prompts, session, "voting"
        )

        # Parse votes and compute Borda count
        coa_labels = [coa["label"] for coa in anonymized_coas]
        borda_scores = self._compute_borda_scores(results, coa_labels)

        # Select top 2-3 finalists
        sorted_coas = sorted(borda_scores.items(), key=lambda x: x[1], reverse=True)
        finalists = [label for label, _ in sorted_coas[: min(3, len(sorted_coas))]]

        session.artifacts["voting"] = {
            "raw_votes": results,
            "borda_scores": borda_scores,
            "finalists": finalists,
        }
        session.phases_completed.append("voting")

    def _compute_borda_scores(
        self, votes: dict[str, str], coa_labels: list[str]
    ) -> dict[str, int]:
        """Compute Borda count scores from expert votes.

        Borda count: N points for 1st, N-1 for 2nd, etc.
        """
        scores: dict[str, int] = dict.fromkeys(coa_labels, 0)
        n = len(coa_labels)

        for vote_text in votes.values():
            # Simple parsing: look for numbered list with COA labels
            for label in coa_labels:
                # Check if this label appears with a rank number
                for rank in range(1, n + 1):
                    if f"{rank}." in vote_text and label in vote_text:
                        # Approximate: give points based on where label appears
                        pos = vote_text.find(label)
                        rank_pos = vote_text.find(f"{rank}.")
                        if 0 <= rank_pos < pos < rank_pos + 200:
                            scores[label] += n - rank + 1
                            break

        return scores

    async def _phase_premortem(self, session: WarRoomSession) -> None:
        """Phase 6: Premortem Analysis on top finalist."""
        finalists = session.artifacts.get("voting", {}).get("finalists", [])
        if not finalists:
            session.artifacts["premortem"] = {"error": "No finalists to analyze"}
            session.phases_completed.append("premortem")
            return

        # Get the top COA content
        top_label = finalists[0]
        anonymized_coas = session.merkle_dag.get_anonymized_view(phase="coa")
        selected_coa = next(
            (c["content"] for c in anonymized_coas if c["label"] == top_label),
            "N/A",
        )

        # All active experts do premortem
        panel = FULL_COUNCIL if session.mode == "full_council" else LIGHTWEIGHT_PANEL
        premortem_experts = [e for e in panel if e != "supreme_commander"]

        prompts: dict[str, str] = {}
        for expert_key in premortem_experts:
            expert = EXPERT_CONFIGS.get(expert_key)
            if expert:
                prompts[expert_key] = self.PREMORTEM_PROMPT.format(
                    role=expert.role,
                    problem=session.problem_statement,
                    selected_coa=selected_coa,
                )

        results = await self._invoke_parallel(
            premortem_experts, prompts, session, "premortem"
        )

        session.artifacts["premortem"] = {
            "selected_coa": top_label,
            "analyses": results,
        }
        session.phases_completed.append("premortem")

    async def _phase_synthesis(self, session: WarRoomSession) -> None:
        """Phase 7: Supreme Commander Synthesis."""
        # Unseal the Merkle-DAG to reveal full attribution
        unsealed = session.merkle_dag.unseal()
        coa_entries = [n for n in unsealed if n["phase"] == "coa"]
        coas_unsealed = "\n\n".join(
            f"### {n['label']} (by {n['expert_role']} / {n['expert_model']})\n"
            f"{n['content']}"
            for n in coa_entries
        )

        intel = session.artifacts.get("intel", {})
        scout = intel.get("scout_report", "N/A")
        intel_rpt = intel.get("intel_report", "N/A")
        intel_text = f"Scout: {scout}\n\nIntel Officer: {intel_rpt}"

        prompt = self.SYNTHESIS_PROMPT.format(
            problem=session.problem_statement,
            intel=intel_text,
            assessment=session.artifacts.get("assessment", {}).get("content", "N/A"),
            coas_unsealed=coas_unsealed,
            red_team=session.artifacts.get("red_team", {}).get("challenges", "N/A"),
            voting=json.dumps(session.artifacts.get("voting", {}), indent=2),
            premortem=json.dumps(session.artifacts.get("premortem", {}), indent=2),
        )

        # Supreme Commander synthesis (native Opus)
        result = await self._invoke_expert(
            "supreme_commander", prompt, session, "synthesis"
        )

        session.artifacts["synthesis"] = {
            "decision": result,
            "attribution_revealed": True,
        }
        session.phases_completed.append("synthesis")

    # ---------------------------------------------------------------------------
    # Persistence (Phase 3: Enhanced Strategeion)
    # ---------------------------------------------------------------------------

    def _persist_session(self, session: WarRoomSession) -> None:
        """Save session to Strategeion with organized subdirectories."""
        session_dir = self.strategeion / "war-table" / session.session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories per Strategeion architecture
        intel_dir = session_dir / "intelligence"
        plans_dir = session_dir / "battle-plans"
        wargames_dir = session_dir / "wargames"
        orders_dir = session_dir / "orders"

        for d in [intel_dir, plans_dir, wargames_dir, orders_dir]:
            d.mkdir(exist_ok=True)

        # Save intelligence reports
        intel = session.artifacts.get("intel", {})
        if intel.get("scout_report"):
            (intel_dir / "scout-report.md").write_text(
                f"# Scout Report\n\n{intel['scout_report']}"
            )
        if intel.get("intel_report") and "[Intel Officer not invoked" not in str(
            intel.get("intel_report", "")
        ):
            (intel_dir / "intel-officer-report.md").write_text(
                f"# Intelligence Officer Report\n\n{intel['intel_report']}"
            )

        # Save assessment
        assessment = session.artifacts.get("assessment", {}).get("content")
        if assessment:
            (intel_dir / "situation-assessment.md").write_text(
                f"# Situation Assessment\n\n{assessment}"
            )

        # Save COAs (battle plans)
        coas = session.artifacts.get("coa", {}).get("raw_coas", {})
        for expert, coa_content in coas.items():
            (plans_dir / f"coa-{expert}.md").write_text(
                f"# Course of Action: {expert}\n\n{coa_content}"
            )

        # Save Red Team challenges and Premortem (wargames)
        red_team = session.artifacts.get("red_team", {}).get("challenges")
        if red_team:
            (wargames_dir / "red-team-challenges.md").write_text(
                f"# Red Team Challenges\n\n{red_team}"
            )

        premortem = session.artifacts.get("premortem", {}).get("analyses", {})
        if premortem:
            premortem_content = "\n\n---\n\n".join(
                f"## {expert}\n\n{analysis}" for expert, analysis in premortem.items()
            )
            (wargames_dir / "premortem-analyses.md").write_text(
                f"# Premortem Analyses\n\n{premortem_content}"
            )

        # Save final decision (orders)
        synthesis = session.artifacts.get("synthesis", {}).get("decision")
        if synthesis:
            (orders_dir / "supreme-commander-decision.md").write_text(synthesis)

        # Save main session file (includes all data for reconstruction)
        session_data = {
            "session_id": session.session_id,
            "problem_statement": session.problem_statement,
            "mode": session.mode,
            "status": session.status,
            "escalated": session.escalated,
            "escalation_reason": session.escalation_reason,
            "phases_completed": session.phases_completed,
            "artifacts": session.artifacts,
            "metrics": session.metrics,
            "merkle_dag": session.merkle_dag.to_dict(),
        }

        with open(session_dir / "session.json", "w") as f:
            json.dump(session_data, f, indent=2)

    def load_session(self, session_id: str) -> WarRoomSession | None:
        """Load session from Strategeion."""
        session_file = self.strategeion / "war-table" / session_id / "session.json"
        if not session_file.exists():
            return None

        with open(session_file) as f:
            data = json.load(f)

        # Reconstruct session
        session = WarRoomSession(
            session_id=data["session_id"],
            problem_statement=data["problem_statement"],
            mode=data["mode"],
            status=data["status"],
            escalated=data.get("escalated", False),
            escalation_reason=data.get("escalation_reason"),
            phases_completed=data["phases_completed"],
            artifacts=data["artifacts"],
            metrics=data["metrics"],
        )

        # Reconstruct MerkleDAG
        dag_data = data.get("merkle_dag", {})
        session.merkle_dag = MerkleDAG(session_id=dag_data.get("session_id", ""))
        session.merkle_dag.sealed = dag_data.get("sealed", True)
        session.merkle_dag.root_hash = dag_data.get("root_hash")
        session.merkle_dag.label_counter = dag_data.get("label_counter", {})

        # Reconstruct nodes
        for node_data in dag_data.get("nodes", {}).values():
            node = DeliberationNode(
                node_id=node_data["node_id"],
                parent_id=node_data.get("parent_id"),
                round_number=node_data["round_number"],
                phase=node_data["phase"],
                anonymous_label=node_data["anonymous_label"],
                content=node_data["content"],
                expert_role=node_data.get("expert_role", "[SEALED]"),
                expert_model=node_data.get("expert_model", "[SEALED]"),
                content_hash=node_data["content_hash"],
                metadata_hash=node_data["metadata_hash"],
                combined_hash=node_data["combined_hash"],
                timestamp=node_data["timestamp"],
            )
            session.merkle_dag.nodes[node.node_id] = node

        return session

    def archive_session(
        self, session_id: str, project: str | None = None
    ) -> Path | None:
        """Archive completed session to campaign-archive."""
        session = self.load_session(session_id)
        if not session or session.status != "completed":
            return None

        # Determine archive location
        project_name = project or "default"
        decision_date = datetime.now().strftime("%Y-%m-%d")
        archive_dir = (
            self.strategeion / "campaign-archive" / project_name / decision_date
        )
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Move session directory
        source = self.strategeion / "war-table" / session_id
        dest = archive_dir / session_id

        if source.exists():
            shutil.move(str(source), str(dest))
            return dest

        return None

    def list_sessions(self, include_archived: bool = False) -> list[dict[str, Any]]:
        """List all War Room sessions."""
        sessions = []

        # Active sessions
        war_table = self.strategeion / "war-table"
        if war_table.exists():
            for session_dir in war_table.iterdir():
                if session_dir.is_dir():
                    session_file = session_dir / "session.json"
                    if session_file.exists():
                        with open(session_file) as f:
                            data = json.load(f)
                        sessions.append(
                            {
                                "session_id": data["session_id"],
                                "problem": data["problem_statement"][:100],
                                "status": data["status"],
                                "mode": data["mode"],
                                "archived": False,
                            }
                        )

        # Archived sessions
        if include_archived:
            archive = self.strategeion / "campaign-archive"
            if archive.exists():
                for project_dir in archive.iterdir():
                    if project_dir.is_dir():
                        for date_dir in project_dir.iterdir():
                            if date_dir.is_dir():
                                for session_dir in date_dir.iterdir():
                                    session_file = session_dir / "session.json"
                                    if session_file.exists():
                                        with open(session_file) as f:
                                            data = json.load(f)
                                        sessions.append(
                                            {
                                                "session_id": data["session_id"],
                                                "problem": data["problem_statement"][
                                                    :100
                                                ],
                                                "status": data["status"],
                                                "mode": data["mode"],
                                                "archived": True,
                                                "project": project_dir.name,
                                            }
                                        )

        return sessions

    # ---------------------------------------------------------------------------
    # Delphi Mode (Phase 4: Iterative Convergence)
    # ---------------------------------------------------------------------------

    DELPHI_REVISION_PROMPT = """You are {role} in Delphi round {round_number}.

PROBLEM STATEMENT:
{problem}

PREVIOUS ROUND FEEDBACK:
{feedback}

YOUR PREVIOUS POSITION:
{previous_position}

OTHER EXPERT POSITIONS (anonymized):
{other_positions}

Based on the Red Team feedback and other expert positions, REVISE your position:

1. **What you maintain**: [aspects you still believe are correct]
2. **What you've reconsidered**: [aspects you've changed based on feedback]
3. **Your updated recommendation**: [revised COA or position]

Be open to changing your mind based on valid arguments, but don't abandon
positions without substantive reason."""

    async def convene_delphi(
        self,
        problem: str,
        context_files: list[str] | None = None,
        max_rounds: int = 5,
        convergence_threshold: float = 0.85,
    ) -> WarRoomSession:
        """Convene Delphi-style War Room with iterative convergence.

        Args:
            problem: The problem/decision to deliberate
            context_files: Optional file globs for context
            max_rounds: Maximum Delphi rounds (default 5)
            convergence_threshold: Agreement threshold to stop (default 0.85)

        Returns:
            Completed WarRoomSession with Delphi convergence data

        """
        # Clear availability cache for fresh session
        clear_availability_cache()

        # Initialize with full council for Delphi
        session = self._initialize_session(problem, "full_council")
        session.metrics["start_time"] = datetime.now().isoformat()
        session.metrics["delphi_mode"] = True
        session.metrics["max_rounds"] = max_rounds
        session.metrics["convergence_threshold"] = convergence_threshold

        try:
            # Round 1: Standard generation
            await self._phase_intel(session, context_files)
            await self._phase_assessment(session)
            await self._phase_coa_development(session)
            await self._phase_red_team(session)
            await self._phase_voting(session)

            convergence = self._compute_convergence(session)
            session.metrics["round_1_convergence"] = convergence

            delphi_round = 2
            while convergence < convergence_threshold and delphi_round <= max_rounds:
                # Delphi revision round
                await self._delphi_revision_round(session, delphi_round)
                await self._phase_red_team(session)
                await self._phase_voting(session)

                convergence = self._compute_convergence(session)
                session.metrics[f"round_{delphi_round}_convergence"] = convergence
                delphi_round += 1

            session.metrics["final_convergence"] = convergence
            session.metrics["total_rounds"] = delphi_round - 1

            # Final phases
            await self._phase_premortem(session)
            await self._phase_synthesis(session)

            session.status = "completed"

        except Exception as e:
            session.status = f"failed: {e}"
            raise

        finally:
            session.metrics["end_time"] = datetime.now().isoformat()
            # Capture any fallback notices
            fallback_notice = get_fallback_notice()
            if fallback_notice:
                session.artifacts["fallback_notice"] = fallback_notice
            self._persist_session(session)

        return session

    async def _delphi_revision_round(
        self, session: WarRoomSession, round_number: int
    ) -> None:
        """Execute a Delphi revision round where experts revise positions."""
        # Get previous COAs and Red Team feedback
        red_team_feedback = session.artifacts.get("red_team", {}).get(
            "challenges", "N/A"
        )
        previous_coas = session.artifacts.get("coa", {}).get("raw_coas", {})

        # Get anonymized view for other positions
        anonymized = session.merkle_dag.get_anonymized_view(phase="coa")
        other_positions = "\n\n".join(
            f"### {c['label']}\n{c['content']}" for c in anonymized
        )

        # Revision prompts for each expert who contributed COAs
        panel = FULL_COUNCIL
        revision_experts = [
            e
            for e in panel
            if e in previous_coas and e not in ["supreme_commander", "red_team"]
        ]

        prompts: dict[str, str] = {}
        for expert_key in revision_experts:
            expert = EXPERT_CONFIGS.get(expert_key)
            if expert:
                prompts[expert_key] = self.DELPHI_REVISION_PROMPT.format(
                    role=expert.role,
                    round_number=round_number,
                    problem=session.problem_statement,
                    feedback=red_team_feedback,
                    previous_position=previous_coas.get(expert_key, "N/A"),
                    other_positions=other_positions,
                )

        results = await self._invoke_parallel(revision_experts, prompts, session, "coa")

        # Update COAs with revised positions
        session.artifacts["coa"]["raw_coas"].update(results)
        session.artifacts["coa"]["delphi_round"] = round_number

    def _compute_convergence(self, session: WarRoomSession) -> float:
        """Compute expert convergence score based on voting agreement.

        Returns a score between 0 and 1, where:
        - 1.0 = perfect agreement (all experts rank COAs identically)
        - 0.0 = complete disagreement

        """
        voting = session.artifacts.get("voting", {})
        borda_scores = voting.get("borda_scores", {})

        if not borda_scores or len(borda_scores) < 2:
            return 0.0

        # Compute normalized standard deviation of scores
        scores = list(borda_scores.values())
        if not scores:
            return 0.0

        mean_score = sum(scores) / len(scores)
        if mean_score == 0:
            return 0.0

        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        std_dev = variance**0.5

        # Normalize: higher score spread = higher convergence
        # (clear winner indicates agreement)
        max_possible_spread = mean_score  # Theoretical max
        if max_possible_spread == 0:
            return 0.0

        convergence: float = min(1.0, std_dev / max_possible_spread)
        return convergence

    # ---------------------------------------------------------------------------
    # Hook Auto-Trigger (Phase 4)
    # ---------------------------------------------------------------------------

    @staticmethod
    def should_suggest_war_room(
        user_message: str,
        complexity_threshold: float = 0.7,
    ) -> dict[str, Any]:
        """Determine if War Room should be suggested based on message analysis.

        Returns a dict with:
        - suggest: bool - whether to suggest War Room
        - confidence: float - confidence in suggestion (0-1)
        - reason: str - explanation for suggestion
        - keywords_matched: list[str] - which keywords triggered

        """
        message_lower = user_message.lower()

        # Strategic decision keywords
        strategic_keywords = [
            "architecture",
            "architectural",
            "trade-off",
            "tradeoff",
            "vs",
            "versus",
            "should we",
            "which approach",
            "best approach",
            "migration",
            "refactor",
            "rewrite",
            "platform",
            "strategic",
            "long-term",
            "irreversible",
            "breaking change",
        ]

        # High-stakes indicators
        stakes_keywords = [
            "critical",
            "important decision",
            "major",
            "significant",
            "risky",
            "uncertain",
            "complex",
            "complicated",
        ]

        # Multi-option indicators
        multi_option_keywords = [
            "options",
            "alternatives",
            "approaches",
            "microservices or monolith",
            "sql or nosql",
            "build or buy",
            "choice between",
        ]

        matched_strategic = [kw for kw in strategic_keywords if kw in message_lower]
        matched_stakes = [kw for kw in stakes_keywords if kw in message_lower]
        matched_multi = [kw for kw in multi_option_keywords if kw in message_lower]

        all_matched = matched_strategic + matched_stakes + matched_multi

        # Compute complexity score
        strategic_weight = len(matched_strategic) * 0.3
        stakes_weight = len(matched_stakes) * 0.25
        multi_weight = len(matched_multi) * 0.35

        complexity_score = min(1.0, strategic_weight + stakes_weight + multi_weight)

        suggest = complexity_score >= complexity_threshold

        if suggest:
            if matched_multi:
                reason = "Multiple approaches detected - War Room can help"
            elif matched_strategic:
                reason = "Strategic decision detected - expert council recommended"
            else:
                reason = "High-stakes decision - thorough analysis recommended"
        else:
            reason = "Standard task - War Room not needed"

        return {
            "suggest": suggest,
            "confidence": complexity_score,
            "reason": reason,
            "keywords_matched": all_matched,
        }


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    async def main() -> None:
        """CLI entry point for War Room orchestrator."""
        if len(sys.argv) < 2:
            print("Usage: war_room_orchestrator.py <problem_statement>")
            sys.exit(1)

        problem = " ".join(sys.argv[1:])
        orchestrator = WarRoomOrchestrator()
        session = await orchestrator.convene(problem=problem, mode="lightweight")
        print(f"Session completed: {session.session_id}")
        print(f"Status: {session.status}")
        print(f"Phases: {session.phases_completed}")

    asyncio.run(main())
