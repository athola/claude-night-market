# Voice Craft Research Findings

Research conducted 2026-04-10 across code, discourse, and
academic channels.

## Key Academic Findings

### PROSE (2025) - Iterative Profile Refinement

The most directly applicable paper. Infers user writing
preferences from samples via iterative refinement and
cross-sample verification. Outperforms CIPHER by 33% and
combined with ICL improves 47%.

**Implication**: Add convergence verification to our
extraction. Generate sample text with the profile, compare
to user samples, iterate if match is poor.

### Contrastive In-Context Learning (AAAI 2024)

Using the model's own zero-shot outputs as negative
examples is as effective as human-written negatives.
76% vs 64% win rate over standard few-shot.

**Implication**: Our SICO comparative approach (showing
Claude its own output alongside user samples) is
empirically validated.

### Hard Ceiling for Implicit Style (EMNLP 2025)

More examples DON'T help beyond 2-5 samples. LLMs plateau
regardless of example count. The solution is explicit
feature extraction, not implicit in-context learning.

**Implication**: Our approach (extracting explicit features
rather than relying on few-shot examples) is correct.
Feature descriptions are the mechanism that crosses the
plateau.

### Fast-DetectGPT / Probability Curvature

AI text occupies "positive curvature" - token choices are
consistently better than alternatives. Human text is locally
suboptimal but globally meaningful. This is WHY detection
works and WHY style instructions can't fix it.

**Implication**: We can't beat detection through prompting
alone (confirmed by prose-craft experiments). Focus on
voice quality rather than detectability.

### StyleDistance (NAACL 2025)

40 distinct style features for contrastive learning.
Content-independent style embeddings trained on synthetic
parallel data.

**Implication**: The 40-feature taxonomy is a useful
vocabulary for our extraction prompts. Could inform the
categories we ask the model to analyze.

### TinyStyler (EMNLP 2024)

800M parameter specialized model beats GPT-4 on authorship
style transfer with proper style representations.

**Implication**: Explicit style representations matter more
than model scale. Our extraction.md IS the style
representation that enables voice-accurate generation.

## Key Discourse Findings

### Strategic Inefficiencies (Scale AI)

LLMs optimize away the deliberate detours, pauses, and
syntactic variations that make writing feel human. Voice
extraction must specifically identify and preserve these.

### Negation Methodology (Artificial Corner)

"Most of a good voice profile is about what you reject."
Defining what a writer would NEVER do is more revealing
than positive preferences.

### Cross-LLM Meta-Analysis

Feeding voice descriptions from one model to another asking
"anything missing?" produces better results than single-model
extraction.

### Blandification Effect (NBC/Academic Study)

Heavy AI users lose 50% of pronouns and 69% of opinionation.
AI "replaces a much larger fraction of the original writing
than humans do." Voice profiles must counter this drift.

### RLHF as Detection Source (HN Discussion)

Corporate safety fine-tuning produces the mechanical output
that detectors catch. The model's pretrained base is more
natural than its RLHF-tuned chat persona.

## Key Code Findings

### Gap in Existing Tools

No repository combines all three needs:
(a) automated multi-dimensional extraction from samples
(b) comparative analysis against AI baselines
(c) prompt generation from extracted profile

Our implementation fills this gap.

### dome317/ai-social-engine

4-layer validation: regex, embeddings, LLM judge, stylometry.
Edit-diff learning with pattern decay.

**Implication**: Multi-layer validation is the gold standard.
Our prose + craft dual review approximates this.

### blader/humanizer (13.2k stars)

29 AI patterns across 5 categories. Voice calibration from
samples. Two-pass processing pipeline.

**Implication**: Our banned-phrase and pattern detection
in the prose reviewer should cover these categories.

## Enhancements Informed by Research

1. **Convergence verification** (from PROSE paper):
   After extraction, generate sample text and compare to
   user samples. If match is poor, iterate.

2. **Strategic inefficiencies** (from Scale AI):
   Explicitly extract deliberate detours, pauses, and
   syntactic variations in Pass 1.

3. **Negation extraction** (from Artificial Corner):
   Pass 1 now asks "what would this writer NEVER do?"

4. **Cross-model meta-analysis** (from Scale AI):
   Optional enrichment pass using a second model to
   review the extraction for gaps.

5. **40-feature taxonomy** (from StyleDistance):
   Inform extraction categories with academic feature
   vocabulary for more systematic coverage.
