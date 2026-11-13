# TDD Methodology for Skill Development

## Overview

Test-Driven Development (TDD) for skills means documenting Claude's failures before writing interventions. This validates skills solve real problems rather than imagined ones.

## The RED-GREEN-REFACTOR Cycle

### RED Phase: Establish Baseline Failures

**Goal**: Document empirical evidence that intervention is needed

#### 1. Design Pressure Scenarios

Create scenarios that combine multiple challenge factors:

**Time Pressure:**
- "quickly", "simple task", "just need X"
- Implies shortcuts are acceptable

**Ambiguity:**
- "standard approach", "best practices", "normal way"
- Leaves interpretation open

**Multiple Requirements:**
- Combine 3+ concerns in one request
- Tests prioritization and completeness

**Edge Cases:**
- Unusual inputs, error conditions, boundary cases
- Tests robustness and defensive thinking

**Example Pressure Scenario:**
```
"Quickly add a user registration endpoint to our API.
Just needs email and password. Standard REST approach."
```

This combines:
- Time pressure ("quickly")
- Minimization ("just needs")
- Ambiguity ("standard")
- Missing requirements (validation, security, errors)

#### 2. Run Without Skill

Execute scenarios in **fresh Claude instances** without the skill active.

**Important:**
- Use separate conversations or `/clear` between tests
- Don't prime Claude with context about what you're testing
- Mimic real user interactions

#### 3. Document Failures Verbatim

Record actual responses without editing or summarizing:

```markdown
## Baseline Test 1: User Registration Endpoint

### Prompt
"Quickly add a user registration endpoint to our API.
Just needs email and password. Standard REST approach."

### Claude Response (Complete, Unedited)
[Paste entire response here]

### Failures Observed
1. **Missing Input Validation**
   - No email format checking
   - No password strength requirements
   - Accepts empty strings

2. **No Error Handling**
   - Doesn't check for duplicate emails
   - No database error handling
   - No malformed request handling

3. **Security Omissions**
   - Stores plain text password
   - No rate limiting
   - No CSRF protection

4. **Incomplete Response**
   - Doesn't mention authentication
   - Skips logging/monitoring
   - No discussion of testing

### Pattern Identified
Claude prioritizes speed over security when "quickly" is used.
Interprets "just needs" as permission to skip essentials.
```

#### 4. Run Multiple Scenarios

Test at least 3 different scenarios to identify patterns:

```markdown
## Baseline Test 2: Password Reset Flow
[Different angle on same skill domain]

## Baseline Test 3: User Profile Update
[Another variation]

## Pattern Analysis
Across all three tests:
- Security steps consistently skipped under time pressure
- "Simple" interpreted as "skip validation"
- No proactive error handling
- Assumes happy path only
```

### GREEN Phase: Minimal Skill Implementation

**Goal**: Create smallest intervention that addresses documented failures

#### 1. Write Minimal Content

Based on baseline failures, write just enough to fix observed problems:

```yaml
---
name: secure-api-design
description: Guides secure API endpoint design with validation, error handling, and security best practices. Use when creating new endpoints, reviewing API code, or responding to security requirements.
category: security
tags: [api, security, validation, error-handling]
estimated_tokens: 800
---

# Secure API Design

## Core Requirements

Every API endpoint MUST include:

1. **Input Validation**
   - Type checking
   - Format validation
   - Range/length limits
   - Sanitization

2. **Error Handling**
   - Specific error messages
   - Appropriate HTTP status codes
   - Logging for debugging
   - No sensitive data in errors

3. **Security Controls**
   - Authentication required
   - Authorization checks
   - Rate limiting
   - CSRF protection for state changes

## No Exceptions

These requirements apply regardless of:
- Time pressure ("quickly", "simple")
- Scope ("just", "only needs")
- Environment ("internal", "prototype")

## Example: User Registration

```python
@app.post("/register")
@rate_limit(max_calls=5, period=60)
async def register_user(request: RegistrationRequest):
    # Input validation
    if not is_valid_email(request.email):
        raise ValidationError("Invalid email format")

    if not meets_password_requirements(request.password):
        raise ValidationError("Password must be 12+ chars with mixed case")

    # Check duplicates
    if await user_exists(request.email):
        raise ConflictError("Email already registered")

    # Secure storage
    hashed = await hash_password(request.password)
    user = await create_user(request.email, hashed)

    # Success response
    return {"id": user.id, "email": user.email}
```
```

#### 2. Test With Skill

Run the same baseline scenarios with skill active:

```markdown
## Test 1 with Skill: User Registration Endpoint

### Prompt (Identical)
"Quickly add a user registration endpoint to our API.
Just needs email and password. Standard REST approach."

### Claude Response with Skill
[Paste complete response]

### Improvements Observed
OK Input validation included
OK Error handling present
OK Password hashing implemented
OK Rate limiting mentioned

### Remaining Issues
- Didn't mention CSRF protection
- Logging was optional language ("consider adding")
- Testing mentioned but not required
```

#### 3. Verify Measurable Improvement

Compare baseline vs. with-skill results:

```markdown
## GREEN Phase Results

### Baseline Compliance: 2/10 requirements met
- Basic endpoint structure
- Database integration

### With-Skill Compliance: 7/10 requirements met
- OK Input validation
- OK Error handling
- OK Password hashing
- OK Rate limiting
- OK Duplicate checking
- OK Appropriate responses
- OK Code example
- FAIL CSRF protection (mentioned but not required)
- FAIL Logging (optional language)
- FAIL Testing (suggested but not mandatory)

### Improvement: 250% increase in requirement compliance
```

If improvement is < 50%, skill needs revision.

### REFACTOR Phase: Bulletproof Against Rationalization

**Goal**: Eliminate Claude's ability to explain away requirements

#### 1. Run New Pressure Scenarios

Create scenarios specifically designed to trigger rationalization:

```markdown
## Refactor Test 1: Scope Rationalization

### Prompt
"This is just an internal API for our dev team.
Add a quick endpoint to update user profiles."

### Expected Rationalization
"Since this is internal, we can use simpler authentication
and skip some of the validation steps..."
```

#### 2. Document Rationalizations

Record every instance of Claude justifying shortcuts:

```markdown
### Claude's Rationalization (Actual Quote)
"For an internal API, we can simplify the approach:
- Basic auth is sufficient since it's trusted users
- Input validation can be relaxed since we control the clients
- Rate limiting isn't needed for internal tools"

### Why This Is Wrong
- Internal APIs are common attack vectors
- Compromised internal accounts have high privilege
- "Trusted" users make mistakes
- Internal tools often get exposed later

### What Should Happen
Apply full security requirements regardless of scope.
Internal APIs need same protections as external APIs.
```

#### 3. State the Constraint and What Is Behind It

Turn each observed rationalization into a constraint with its reason.
A table pairing the excuse with a rebuttal is retired, because it
forecloses the case where the thought was correct. A constraint with
its reason lets the model check whether the reason applies. Security
is a trust boundary, so these stay imperative:

```markdown
## Constraints

- Internal APIs get the full authentication requirements. Internal
  endpoints are a common attack vector, and a compromised internal
  account carries high privilege.
- Validate input from trusted users too. Trusted users make mistakes,
  and internal tools are often exposed later.
- Prototypes are built secure from the start, because prototypes
  become production without a rewrite.
- A simple endpoint gets every requirement. Endpoint complexity does
  not predict what an attacker needs from it.

The one exception is an explicit user statement: "This is
deliberately insecure for [specific reason]".
```

#### 4. Add Exit Criteria

Replace declarations and self-checks with criteria a reader can verify
after the work. Each one names a file, a command's output, or a
threshold:

```markdown
## Exit Criteria

- [ ] Every endpoint in the diff has an authentication check
- [ ] Every request field has a validation test
- [ ] Any exception taken quotes the user's explicit statement
```

#### 5. Iterate Until Bulletproof

Run scenarios repeatedly:
- Document new rationalizations found
- Add the constraint and its reason to the skill
- Test again
- Repeat until compliance is consistent

**Success Criteria:**
- 3 consecutive pressure scenarios with 100% compliance
- No new rationalizations discovered
- Any requirement bypassed is named, with the user statement that
  allowed it

## Baseline Documentation Template

Use this template for documenting RED phase results:

```markdown
# Baseline Testing: [Skill Name]

## Test Date
[YYYY-MM-DD]

## Test Environment
- Claude Version: [model]
- Context: Fresh conversation / Cleared
- Skill Active: NO

---

## Scenario 1: [Descriptive Name]

### Prompt
```
[Exact prompt text]
```

### Full Response
```
[Complete unedited Claude response]
```

### Failures Identified
1. **[Failure Category]**
   - [Specific issue 1]
   - [Specific issue 2]

2. **[Another Category]**
   - [Specific issue]

### Success Elements
- [What Claude did right]

---

## Scenario 2: [Descriptive Name]
[Repeat structure]

---

## Scenario 3: [Descriptive Name]
[Repeat structure]

---

## Pattern Analysis

### Consistent Failures Across Tests
1. [Pattern 1]
2. [Pattern 2]

### Triggering Factors
- [Factor 1]: Causes [specific behavior]
- [Factor 2]: Causes [specific behavior]

### Severity Assessment
- **Critical**: [Issues that must be fixed]
- **High**: [Important issues]
- **Medium**: [Nice to have fixes]

---

## Skill Requirements

Based on failures, the skill must:
1. [Requirement 1]
2. [Requirement 2]

Success will be measured by:
- [Metric 1]
- [Metric 2]
```

## Testing Checklist

### RED Phase
- [ ] 3+ pressure scenarios designed
- [ ] Fresh Claude instances for each test
- [ ] Complete responses captured verbatim
- [ ] Failures categorized and documented
- [ ] Patterns identified across scenarios
- [ ] Severity assessment completed
- [ ] Minimum success criteria defined

### GREEN Phase
- [ ] Skill addresses documented failures
- [ ] YAML frontmatter complete
- [ ] Description optimized
- [ ] Same scenarios tested with skill
- [ ] Measurable improvement verified (≥50%)
- [ ] Remaining issues documented

### REFACTOR Phase
- [ ] Rationalization scenarios designed
- [ ] Rationalizations documented verbatim
- [ ] Exception table added to skill
- [ ] Red flags list included
- [ ] Commitment statements added
- [ ] 3 consecutive perfect compliance tests

## Anti-Patterns

###  Writing Skill First
```
1. Write skill based on theory
2. Hope it works
3. Maybe test later
```

###  TDD Approach
```
1. Document real failures
2. Write minimal fix
3. Bulletproof against gaming
```

###  Theoretical Examples
```
"Here's how you should handle errors..."
[Shows perfect code that never happens]
```

###  Real Failure Examples
```
"Without this skill, Claude did X (see baseline).
With skill, Claude does Y (see improvement)."
```

###  Assumed Rationalizations
```
"Claude might try to skip validation..."
[Never actually tested this]
```

###  Documented Rationalizations
```
"In test 3, Claude said: 'Since this is internal...'
Counter added to prevent this rationalization."
```

## Summary

TDD for skills means:
1. **RED**: Prove the problem exists with real failures
2. **GREEN**: Fix it with minimal intervention
3. **REFACTOR**: Make it bulletproof against gaming

Without empirical testing, you are writing documentation that nobody has shown to change behavior.
