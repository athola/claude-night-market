"""Prompt templates for War Room deliberation phases.

All prompt constants used by the orchestrator and Delphi mode.
"""

from __future__ import annotations

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
