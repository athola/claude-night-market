# Anti-Patterns: Eight Named Drift Rails

Each drift rail names a specific way LLM-driven coding
goes wrong, with a trigger pattern, a short bad
example, a short good example, and a one-sentence
test you can apply to your own diff. Naming the rail
helps recall.

Adapted from observations distilled by Forrest Chang
from Karpathy's notes; see
`references/source-attribution.md` for the citation
chain. Examples are rewritten in our own prose to
illustrate the failure shape, not lifted verbatim.

## AP-1: Hidden Assumptions

**Maps to**: Principle 1 (Think Before Coding)

**Trigger**: User asks for a feature with multiple
unstated dimensions (scope, format, volume, privacy).
The agent picks one silently and ships.

**Bad shape**

```python
def export_users(format='json'):
    users = User.query.all()
    if format == 'json':
        with open('users.json', 'w') as f:
            json.dump([u.to_dict() for u in users], f)
```

Assumed: all users (privacy?), file path, fields,
volume.

**Good shape**

> Before implementing, I want to confirm:
>
> - Scope: all users, or filtered?
> - Format: download, background job, or API endpoint?
> - Fields: which? Some are sensitive.
> - Volume: thousands or millions?
>
> Default proposal: a paginated JSON endpoint. Adjust?

**Test**: count silent assumptions in the diff. Three
or more is a rail violation.

## AP-2: Multiple Interpretations Picked Silently

**Maps to**: Principle 1 (Think Before Coding)

**Trigger**: A request like "make the search faster"
has at least three valid readings (response time,
throughput, perceived speed). The agent picks one and
implements 200 lines without flagging the choice.

**Bad shape**

```python
@lru_cache(maxsize=1000)
async def search(query: str) -> List[Result]:
    # 200 lines of caching, async, indexes, all picked
    # without confirming what "faster" means
    ...
```

**Good shape**

> "Faster" could mean response time, throughput, or
> perceived speed. Each is a different fix:
>
> 1. Response time: indexes plus query caching (~2h)
> 2. Throughput: async path plus pooling (~4h)
> 3. Perceived: progressive load and partial results
>    (~3h)
>
> Current: ~500ms typical. Which axis matters?

**Test**: when the verb in the request is ambiguous
(faster, better, cleaner, simpler), did the agent name
the alternatives or pick one?

## AP-3: Strategy Pattern for One Function

**Maps to**: Principle 2 (Simplicity First)

**Trigger**: User asks for a single function. The
agent ships an abstract base class, two implementing
classes, a config dataclass, and a coordinator class
for ten lines of arithmetic.

**Bad shape**

```python
class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, amount: float) -> float: ...

class PercentageDiscount(DiscountStrategy):
    def __init__(self, p): self.p = p
    def calculate(self, a): return a * (self.p / 100)

# Plus FixedDiscount, DiscountConfig, DiscountCalculator
# for what should be one function
```

**Good shape**

```python
def calculate_discount(amount: float, percent: float) -> float:
    return amount * (percent / 100)
```

**Test**: count types and classes added per actual use
case. If types-added exceeds use-cases-served, the
pattern is premature.

## AP-4: Speculative Features

**Maps to**: Principle 2 (Simplicity First)

**Trigger**: "Save user preferences to database"
becomes a class with optional caching, validation,
notification hooks, and merge semantics. None were
asked for.

**Bad shape**

```python
class PreferenceManager:
    def __init__(self, db, cache=None, validator=None):
        ...
    def save(self, user_id, prefs,
             merge=True, validate=True, notify=False):
        # 60 lines of optional behavior
```

**Good shape**

```python
def save_preferences(db, user_id: int, preferences: dict):
    db.execute(
        "UPDATE users SET preferences = ? WHERE id = ?",
        (json.dumps(preferences), user_id),
    )
```

**Test**: list every parameter that was not in the
request. If you cannot point at a sentence in the
request that demanded it, delete the parameter.

## AP-5: Drive-by Refactoring

**Maps to**: Principle 3 (Surgical Changes)

**Trigger**: User reports a single bug. The agent
fixes the bug, then "improves" three other functions,
adds docstrings, and tightens validation logic that
nobody asked about.

**Bad shape**: a 90-line diff to fix a 4-line bug,
with related but unrequested cleanups across two more
files.

**Good shape**: a 4-line diff that fixes only the
reported bug. If you noticed unrelated issues, list
them in the response and ask before touching them.

**Test**: read the diff line by line. For each
changed line, ask "which sentence in the user's
request demanded this?" Lines without an answer are
candidates for removal from the diff.

## AP-6: Style Drift During Edit

**Maps to**: Principle 3 (Surgical Changes)

**Trigger**: User asks for one logging line in an
upload function. The agent ships type hints,
docstrings, single-quote-to-double-quote conversion,
and a flattened control flow.

**Bad shape**

```diff
- def upload_file(file_path, destination):
+ def upload_file(file_path: str, destination: str) -> bool:
+     """Upload file to destination."""
      try:
-         with open(file_path, 'rb') as f:
+         with open(file_path, "rb") as f:
              ...
```

**Good shape**

```diff
+ logger = logging.getLogger(__name__)
+
  def upload_file(file_path, destination):
+     logger.info(f'Starting upload: {file_path}')
      try:
          with open(file_path, 'rb') as f:
              ...
```

**Test**: the diff should not change quote style,
type hint presence, docstring presence, or whitespace
patterns unless the request named them.

## AP-7: Vague Success Criteria

**Maps to**: Principle 4 (Goal-Driven Execution)

**Trigger**: "Fix the authentication system." The
agent responds "I will review the code, identify
issues, make improvements, and test." That is a plan
shape, not a verification plan.

**Bad shape**: a four-step list of verbs (review,
identify, improve, test) with no checkable signal per
step.

**Good shape**

> "Fix authentication" is too broad to verify. Best
> guess at the actual problem: sessions stay alive
> after password change. Plan:
>
> 1. Write failing test: change password, prior
>    session is rejected.
> 2. Implement: invalidate sessions on change.
> 3. Edge cases: concurrent change, multi-session.
> 4. Regression: full auth suite green.
>
> Is the password-change-stale-session bug the right
> target?

**Test**: each step in the plan should have a one-
sentence "verify by ..." attached. If a step lacks
one, the step is ill-specified.

## AP-8: Multi-Step Plan Without Verification Gates

**Maps to**: Principle 4 (Goal-Driven Execution)

**Trigger**: "Add rate limiting." The agent ships 300
lines with Redis backend, configuration system, and
monitoring in one commit, with no per-step
verification.

**Bad shape**: one large commit covering basic limits,
middleware extraction, Redis integration, and
configuration. Nothing is independently shippable or
revertible.

**Good shape**

> Plan, each step independently verifiable:
>
> 1. In-memory limit on one endpoint. Verify: 11
>    requests, the 11th gets 429.
> 2. Extract to middleware, apply broadly. Verify:
>    /users and /posts both rate-limit; existing tests
>    pass.
> 3. Redis backend. Verify: limits persist across
>    restarts; two instances share counters.
> 4. Per-endpoint config. Verify: /search 10/min,
>    /users 100/min, parsed config tested.
>
> Start with step 1?

**Test**: each step in the plan should be revertible
on its own. If reverting step 3 breaks step 4, the
steps are not independent and the plan needs a redraw.

## How to Use This Module

When reviewing your own diff or someone else's, name
the rail you see. "This is AP-5: drive-by
refactoring" travels faster than "this could be
simpler somehow." Naming the rail is the first half
of fixing the rail.

Cross-references for the rails:

- AP-3, AP-4 connect to `Skill(imbue:scope-guard)` and
  `Skill(leyline:additive-bias-defense)`
- AP-5, AP-6 connect to `Skill(imbue:justify)` and
  the `bounded-discovery.md` rule
- AP-7, AP-8 connect to `Skill(imbue:proof-of-work)`
  and `Skill(superpowers:test-driven-development)`
