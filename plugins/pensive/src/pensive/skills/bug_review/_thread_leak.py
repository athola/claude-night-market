"""Whether code starts a Thread nothing joins, read from its source text."""

from __future__ import annotations

import re

_THREAD_LEAK = "Resource leak: Thread started - potential leak without join()"

# `t = Thread(`, `t: T = Thread(`, `(t := Thread(`. ` *`, not `\s*`: no `try:` binding.
_THREAD_BINDING = re.compile(r"\b(\w+) *(?:: *[\w.]+ *=|:=|=(?!=))\s*[\w.]*Thread\(")
# Started where built, so nothing can join it. `=` excludes the walrus.
_STARTED_UNBOUND = re.compile(r"(?<!=\s)(?<!=)(?:\w+\.)*Thread\(.*?\)\.start\(")
# A join on a name or subscript: how a thread held in a collection is joined.
_RECEIVER_JOIN = re.compile(r"(\w+|[\])])\.join\(")
_THREAD_OPEN = re.compile(r"[\w.]*Thread\(")


def _blank_daemon_threads(code: str) -> str:
    """Replace each daemon=True Thread call, matched to any depth, with None."""
    out, pos = [], 0
    for match in _THREAD_OPEN.finditer(code):
        if match.start() < pos:
            continue
        depth, end = 1, match.end()
        while end < len(code) and depth:
            depth += {"(": 1, ")": -1}.get(code[end], 0)
            end += 1
        if "daemon=True" in code[match.start() : end]:
            out.append(code[pos : match.start()] + "None")
            pos = end
    return "".join(out) + code[pos:]


def _leaks_a_thread(content: str) -> bool:
    """Whether the code, comments stripped, starts an unjoined non-daemon Thread.

    A bound Thread is joined on its name (`foot.join` is not `t`'s) or appended
    to a collection, whose Threads any join not on a string or `path` covers.
    """
    code = "\n".join(line.split("#", 1)[0] for line in content.splitlines())
    daemon_attr = set(re.findall(r"\b(\w+)\.daemon *= *True", code))
    code = _blank_daemon_threads(code)  # per thread, not per file
    if "Thread(" not in code:
        return False
    bound = _THREAD_BINDING.findall(code)
    names = [n for n in bound if n not in daemon_attr]
    joins = set(_RECEIVER_JOIN.findall(code)) - {"path"}
    appended = set(re.findall(r"\.append\(\s*(\w+)\s*\)", code)) if joins else set()
    if set(names) - joins - appended or _STARTED_UNBOUND.search(code):
        return True
    return code.count("Thread(") > len(bound) and not joins
