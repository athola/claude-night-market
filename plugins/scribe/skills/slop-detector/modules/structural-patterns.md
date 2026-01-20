---
module: structural-patterns
category: detection
dependencies: [Bash, Grep]
estimated_tokens: 600
---

# Structural Pattern Detection

AI-generated text exhibits distinctive structural patterns beyond vocabulary.

## Em Dash Analysis

AI uses em dashes (—) excessively as a rhetorical device.

```bash
# Count em dashes per file
em_count=$(grep -o '—' "$file" | wc -l)
word_count=$(wc -w < "$file")
density=$((em_count * 1000 / word_count))
```

| Density (per 1000 words) | Signal |
|--------------------------|--------|
| 0-2 | Normal |
| 3-5 | Elevated |
| 6-10 | High AI signal |
| 10+ | Very high AI signal |

## Tricolon Detection

AI produces alliterative groups of three with suspicious frequency.

Pattern examples:
- "clear, concise, and compelling"
- "fast, flexible, and free"
- "robust, reliable, and resilient"

Detection approach:
```python
# Look for: adjective, adjective, and adjective
tricolon_pattern = r'\b(\w+), (\w+),? and (\w+)\b'
# Flag if words share first letter or similar endings
```

## Sentence Length Uniformity

Human writing varies naturally. AI tends toward medium-length sentences.

```python
def sentence_uniformity(sentences):
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev = variance ** 0.5
    return std_dev

# std_dev < 5: Suspicious uniformity
# std_dev 5-15: Normal variation
# std_dev > 15: High variation (human)
```

## Paragraph Symmetry

AI produces "blocky" text with uniform paragraph lengths.

```bash
# Check paragraph length distribution
awk '/^$/{if(p)print p; p=0; next}{p+=NF}END{print p}' file.md | sort -n | uniq -c
```

If most paragraphs cluster around the same length (e.g., 40-60 words), flag as AI signal.

## Bullet-to-Prose Ratio

AI defaults to bullet points, especially with emojis.

```bash
# Count bullet lines vs total lines
bullet_lines=$(grep -c '^\s*[-*]' file.md)
total_lines=$(wc -l < file.md)
ratio=$((bullet_lines * 100 / total_lines))
```

| Ratio | Signal |
|-------|--------|
| 0-30% | Normal |
| 30-50% | Elevated |
| 50-70% | High (check context) |
| 70%+ | Very high AI signal |

**Emoji bullets** (e.g., lines starting with emoji) in technical documentation are a strong AI tell.

## Five-Paragraph Essay Structure

AI defaults to: intro + three body sections + conclusion recap.

Check for:
1. Opening paragraph that restates the question
2. Three distinct middle sections
3. Closing paragraph that summarizes without adding new information

## Perfect Grammar Signals

| Pattern | Human Range | AI Signal |
|---------|-------------|-----------|
| Contractions | Common | Rare/absent |
| Oxford commas | Variable | Always present |
| Typos | Occasional | None |
| Sentence fragments | Present | Rare |
| Starting with "And" or "But" | Common | Rare |

## Register Uniformity

Human writing shifts between abstract and concrete, formal and casual. AI maintains consistent register throughout.

Check for:
- Absence of colloquialisms
- No slang or informal expressions
- Uniform formality level across all sections

## Structural Score Calculation

```python
def structural_score(metrics):
    score = 0
    if metrics['em_dash_density'] > 5:
        score += 2
    if metrics['sentence_std_dev'] < 5:
        score += 2
    if metrics['bullet_ratio'] > 0.5:
        score += 2
    if metrics['paragraph_uniformity'] > 0.8:
        score += 2
    if metrics['zero_contractions']:
        score += 1
    if metrics['emoji_bullets']:
        score += 3
    return min(10, score)
```
