---
module: reddit-format
category: writing-quality
dependencies: []
estimated_tokens: 530
---

# Reddit Post Format

Templates and rules for turning a session brief into a Reddit
text post that earns upvotes through specificity and honesty.

## When Reddit, When Blog

Choose Reddit when:
- You want community engagement (questions, discussion, feedback)
- The work fits a specific subreddit's current interests
- The story is worth starting a conversation, not just archiving

Choose blog when:
- You want permanent, search-indexed content you own
- The post will be linked from documentation or READMEs
- It needs a stable URL for future reference

## Subreddit Targeting

Match the primary technology or theme to one subreddit. Avoid
cross-posting within 48 hours; it triggers spam filters and
community backlash.

| Subreddit | When to post |
|-----------|-------------|
| r/programming | general software development stories |
| r/rust | Rust code, tooling, ecosystem |
| r/Python | Python projects, libraries, tools |
| r/webdev | web development, frontend, full stack |
| r/devops | infrastructure, CI/CD, deployment |
| r/ClaudeAI | Claude Code usage, AI-assisted dev |
| r/ExperiencedDevs | technical depth, process, architecture |
| r/MachineLearning | ML systems, training, inference |

## Post Structure

Reddit text posts have no required format, but this pattern
works for session stories:

**Hook** (first 2 sentences): the most interesting outcome
or observation. Do not bury the lede. Readers who stop
scrolling past line 3 are gone.

**Context** (1-2 sentences): what you were trying to do and why.

**The work** (2-4 paragraphs): what you built or changed. Name
the tools and techniques. Include one code block if it shows
something surprising or non-obvious.

**Result**: numbers. What works now that did not before.

**Honest close**: what remains, what you would change, what
surprised you. This is what makes the post worth bookmarking.

---

**TL;DR** (required): the whole story in 2-3 sentences. Place
it after a `---` separator at the bottom. Readers who skip to
the end first are your secondary audience; do not disappoint them.

## Title Patterns

The title is the entire hook. Test it with: "would someone
who knows nothing about this click it?"

- `I [did thing] with [tool] — here's what I learned`
- `Built [thing] in [constraint] — [surprising number]`
- `[Surprising result]: how we [achieved it]`
- `Show r/[subreddit]: [what you built] ([brief description])`
- `[Honest take on tool] after [real production use case]`

Keep under 120 characters. The title must work without the body.

## Writing Rules

1. **First person**: "I built" not "we built" unless the team
   matters to the story
2. **No section headers** for posts under 600 words; above that,
   use one level of bold headers only
3. **One code block maximum** in the body; link the rest to
   a repo or Gist
4. **TL;DR is required**: after `---`, at the end
5. **Under 600 words** for most posts; if longer, reconsider
   whether a blog post is the better medium
6. **Conversational close**: "happy to answer questions about X
   in the comments" gives readers a reason to engage

## Anti-Patterns

- Copy-pasting your blog post: the tone is wrong and readers notice
- Burying the lede: starting with context before the interesting part
- Screenshot of code instead of a fenced code block
- No TL;DR on anything over 300 words
- "In conclusion...": just end the post
- Excessive bold/italic throughout: signals AI-generated content

## First Comment Strategy

For technical posts, plan a follow-up comment before posting.
Use it for:
- Full code links (repo URL, Gist)
- Setup instructions that would bloat the post body
- Benchmarks or test output that are reference material, not story

Write this comment in the quality gate step and post it
immediately after the main post goes live.
