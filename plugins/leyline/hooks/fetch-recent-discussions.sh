#!/usr/bin/env bash
# SessionStart hook for leyline - Fetch recent Discussions
# Queries the most recent "Decisions" and "Insights"/"Learnings" discussions
# from GitHub Discussions and injects a brief summary into the session
# context for cross-session learning.
#
# Requirements:
#   - GitHub platform (self-detected via git remote URL)
#   - gh CLI authenticated
#   - Repository has Discussions enabled with a "Decisions" category
#
# Performance. The budget here is spent in whole processes, not in work:
# on a loaded macOS laptop `git` costs 0.53s of start-up, `python3` 0.80s,
# `gh auth status` 1.02s, and one `gh api graphql` round trip 1.2-1.6s.
# This hook therefore runs at most one `git`, one `python3` and, on a cold
# cache, two `gh` calls; the rendered answer is cached for an hour and the
# category ids for a week, so the steady state spends no network at all.
# The `gh auth status` probe is gone: an unauthenticated `gh api` fails on
# its own, and paying a second round trip to predict that is the more
# expensive way to learn it.
#
# Token budget: < 600 tokens injected into session context

set -euo pipefail

# --- Helper: emit empty SessionStart JSON and exit ---

_emit_empty() {
    local reason="${1:-}"
    if [ -n "$reason" ]; then
        echo "[fetch-recent-discussions] $reason" >&2
    fi
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
}

# --- Guards ---

if ! command -v gh >/dev/null 2>&1; then
    _emit_empty
fi

if ! command -v python3 >/dev/null 2>&1; then
    _emit_empty
fi

# `git remote get-url` fails outside a work tree as well as inside one
# with no origin, so it does the job the separate `git rev-parse` used to.
remote_url=$(git remote get-url origin 2>/dev/null || echo "")
case "$remote_url" in
    *github.com*) ;;  # GitHub.com — continue
    *) _emit_empty ;;
esac

# --- Resolve owner/repo from the remote URL ---
# Parameter expansion rather than sed: correct for both the SSH form
# (git@github.com:owner/repo.git) and the HTTPS form, and it spends no
# process to do it.

_tail="${remote_url#*github.com}"
_tail="${_tail#:}"
_tail="${_tail#/}"
_tail="${_tail%.git}"
owner="${_tail%%/*}"
repo="${_tail#*/}"
repo="${repo%%/*}"

if [ -z "$owner" ] || [ -z "$repo" ] || [ "$owner" = "$_tail" ]; then
    _emit_empty "could not parse owner/repo from remote URL"
fi

# --- Cache ---
# LEYLINE_CACHE_DIR exists so tests can point the cache somewhere
# disposable without touching the developer's own.

cache_dir="${LEYLINE_CACHE_DIR:-${XDG_CACHE_HOME:-${HOME}/.cache}/leyline}"
cache_key="${owner}-${repo}"
cache_key="${cache_key//[!a-zA-Z0-9._-]/_}"
summary_cache="${cache_dir}/discussions-${cache_key}.json"
categories_cache="${cache_dir}/categories-${cache_key}.txt"

# `find -mmin` is the freshness test that both BSD and GNU find support,
# and it is one process against `date`'s one plus the arithmetic.
if [ -f "$summary_cache" ] &&
    [ -n "$(find "$summary_cache" -mmin -60 2>/dev/null)" ]; then
    printf '%s\n' "$(<"$summary_cache")"
    exit 0
fi

# --- Fetch, format, and cache ---
# One python3 process owns the network from here. It gives each `gh` call
# its own deadline through subprocess timeout, which is portable in a way
# `timeout(1)` is not: stock macOS does not ship it.

python3 - "$owner" "$repo" "$summary_cache" "$categories_cache" <<'PY' || _emit_empty "discussion fetch failed"
import json
import os
import re
import subprocess
import sys
import time

OWNER, REPO, SUMMARY_CACHE, CATEGORIES_CACHE = sys.argv[1:5]

# The harness cap is what actually bounds this process; these keep a
# single stalled round trip from consuming the whole of it. 3.5s is the
# network half of the budget, chosen against the measured cost of a `gh
# api graphql` round trip (1.2-1.6s) so two of them fit on a cold cache.
# hooks.json grants 8s, and the difference is start-up rather than slack:
# roughly 1.9s is gone before this line runs on an idle machine (bash
# 0.25, git 0.53, find 0.25, interpreter start 0.80), and that figure is
# what stretches under load. Cold-cache wall time measured 3.6-4.1s idle
# and 4.3-4.9s with another build saturating the CPU.
TOTAL_BUDGET = 3.5
PER_CALL_BUDGET = 2.5
CATEGORIES_TTL = 7 * 24 * 3600  # ids are stable; re-resolving them is waste
# Everything interpolated into the GraphQL text is checked against the
# alphabet GitHub allows for it first. The query is assembled as a string
# rather than passed through `gh -f` variables, because the category ids
# have to reach it as aliases, and a remote URL carrying a quote would
# otherwise rewrite the query.
ID_RE = re.compile(r"^[A-Za-z0-9_=-]+$")
NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")

_started = time.time()


def _remaining():
    return min(PER_CALL_BUDGET, TOTAL_BUDGET - (time.time() - _started))


def emit(context):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context,
                }
            },
            indent=2,
        )
    )


def emit_and_cache(context):
    payload = json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        },
        indent=2,
    )
    print(payload)
    try:
        os.makedirs(os.path.dirname(SUMMARY_CACHE), exist_ok=True)
        tmp = SUMMARY_CACHE + ".tmp.%d" % os.getpid()
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
        os.replace(tmp, SUMMARY_CACHE)
    except OSError as exc:
        print("[fetch-recent-discussions] cache write failed: %s" % exc, file=sys.stderr)


def graphql(query):
    """Run one bounded `gh api graphql`. Returns the parsed data, or None."""
    budget = _remaining()
    if budget <= 0:
        return None
    try:
        completed = subprocess.run(
            ["gh", "api", "graphql", "-f", "query=" + query],
            capture_output=True,
            timeout=budget,
        )
    except subprocess.TimeoutExpired:
        print("[fetch-recent-discussions] gh timed out", file=sys.stderr)
        return None
    except OSError as exc:
        print("[fetch-recent-discussions] gh failed: %s" % exc, file=sys.stderr)
        return None
    if completed.returncode != 0:
        print(
            "[fetch-recent-discussions] gh exited %d: %s"
            % (completed.returncode, completed.stderr.decode("utf-8", "replace").strip()),
            file=sys.stderr,
        )
        return None
    try:
        body = json.loads(completed.stdout.decode("utf-8", "replace"))
    except ValueError as exc:
        print("[fetch-recent-discussions] unparseable response: %s" % exc, file=sys.stderr)
        return None
    if body.get("errors"):
        messages = "; ".join(e.get("message", "?") for e in body["errors"])
        print("[fetch-recent-discussions] GraphQL error: %s" % messages, file=sys.stderr)
        return None
    return body.get("data") or {}


def cached_category_ids():
    try:
        age = time.time() - os.path.getmtime(CATEGORIES_CACHE)
    except OSError:
        return None
    if age > CATEGORIES_TTL:
        return None
    try:
        with open(CATEGORIES_CACHE, encoding="utf-8") as handle:
            parts = handle.read().strip().split("|")
    except OSError:
        return None
    if len(parts) != 2:
        return None
    return ["" if part == "-" else part for part in parts]


def store_category_ids(ids):
    try:
        os.makedirs(os.path.dirname(CATEGORIES_CACHE), exist_ok=True)
        tmp = CATEGORIES_CACHE + ".tmp.%d" % os.getpid()
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write("|".join(part or "-" for part in ids) + "\n")
        os.replace(tmp, CATEGORIES_CACHE)
    except OSError as exc:
        print("[fetch-recent-discussions] cache write failed: %s" % exc, file=sys.stderr)


def resolve_category_ids():
    """The Decisions id and the Insights/Learnings id, in that order.

    A missing Decisions category must not shift the Insights id into its
    slot, so absence is carried as an empty string rather than by
    position.
    """
    cached = cached_category_ids()
    if cached is not None:
        return cached

    data = graphql(
        """
query {
  repository(owner: "%s", name: "%s") {
    hasDiscussionsEnabled
    discussionCategories(first: 25) { nodes { id slug } }
  }
}
"""
        % (OWNER, REPO)
    )
    if not data:
        return None
    repository = data.get("repository") or {}
    if not repository.get("hasDiscussionsEnabled"):
        return ["", ""]

    decisions = ""
    insights = ""
    for node in (repository.get("discussionCategories") or {}).get("nodes") or []:
        slug = (node.get("slug") or "").lower()
        node_id = node.get("id") or ""
        if not ID_RE.match(node_id):
            continue
        if slug == "decisions":
            decisions = node_id
        elif slug in ("insights", "learnings"):
            insights = node_id
    ids = [decisions, insights]
    store_category_ids(ids)
    return ids


def discussions_block(alias, category_id, count):
    if not category_id:
        return ""
    return (
        '    %s: discussions(first: %d, categoryId: "%s", '
        "orderBy: {field: CREATED_AT, direction: DESC}) "
        "{ nodes { number title createdAt body } }\n"
        % (alias, count, category_id)
    )


def render(nodes, heading):
    if not nodes:
        return ""
    lines = [heading]
    for node in nodes:
        body = node.get("body") or ""
        snippet = body.replace("\n", " ").replace("\r", "")[:100].strip()
        if len(body) > 100:
            snippet += "..."
        lines.append(
            "  #%s %s (%s) -- %s"
            % (
                node.get("number", "?"),
                node.get("title", "Untitled"),
                (node.get("createdAt") or "")[:10],
                snippet,
            )
        )
    return "\n".join(lines)


def main():
    if not NAME_RE.match(OWNER) or not NAME_RE.match(REPO):
        emit("")
        return

    ids = resolve_category_ids()
    if ids is None:
        # The lookup failed rather than answered. Emit empty without
        # caching, so the next session retries instead of inheriting it.
        emit("")
        return
    decisions_id, insights_id = ids

    blocks = discussions_block("decisions", decisions_id, 10) + discussions_block(
        "insights", insights_id, 5
    )
    if not blocks:
        emit_and_cache("")
        return

    # Both categories travel as aliases of one query, so two categories
    # still cost one round trip. The three-query shape this replaced is
    # what put the hook four times over its cap.
    data = graphql(
        'query {\n  repository(owner: "%s", name: "%s") {\n%s  }\n}\n'
        % (OWNER, REPO, blocks)
    )
    if data is None:
        emit("")
        return

    repository = data.get("repository") or {}
    sections = [
        render(
            (repository.get("decisions") or {}).get("nodes") or [],
            "Recent Decisions (from GitHub Discussions):",
        ),
        render(
            (repository.get("insights") or {}).get("nodes") or [],
            "Recent Insights (from GitHub Discussions):",
        ),
    ]
    emit_and_cache("\n".join(section for section in sections if section))


main()
PY
