---
module: source-framing
category: voice-generation
dependencies: []
estimated_tokens: 400
---

# Source Framing Module

How source material is framed in the prompt is the single
largest variable in output quality. Larger than voice rules.
Larger than model choice.

## The Framing Lever

When material is framed as "raw notes I'm still thinking
through," the output is dramatically better than when framed
as "a transcript to draw on" or a bare topic sentence.

The framing changes how the model relates to the material:
- Notes to think through -> text that feels like thinking
- Summaries to report on -> text that feels like reporting
- Transcripts to draw from -> text that feels like paraphrase

## Default Framing (always use)

```
Below are my rough notes on this topic. I'm still working
through these ideas and haven't settled on a final structure.
Use them as raw material for thinking, not as an outline
to follow:

---
{source_material}
---

Write a piece that engages with these ideas in the voice
described above. You don't need to cover everything in the
notes. Follow where the interesting threads lead.
```

## When User Provides Structured Input

If the user gives bullet points or an outline, still
reframe as notes:

```
Below are my working notes. These bullet points represent
threads I'm pulling on, not a structure to reproduce:

---
{bullet_points}
---
```

## When User Provides a Topic Only

If just a topic sentence or phrase:

```
I want to write about: {topic}

Here's what I'm thinking so far: I don't have notes yet,
but the angle I'm interested in is {topic}. Write an
exploratory piece that discovers its argument as it goes.
```

## Override Framings

Only use these if the user explicitly requests a different
relationship to the source material:

### "Preserve my structure"
```
Below is an outline I want to follow. Keep the structure
but write each section in the voice described above:
```

### "Respond to this"
```
Below is something I'm responding to. Write a response
in the voice described above:
```

### "Expand these points"
```
Below are key points I want to develop. Expand each one
into full prose in the voice described above:
```
