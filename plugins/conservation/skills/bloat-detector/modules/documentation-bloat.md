---
module: documentation-bloat
category: tier-2
dependencies: [Bash, Grep, Read]
estimated_tokens: 250
---

# Documentation Bloat Module

Detect and mitigate documentation bloat: redundancy, excessive verbosity, poor readability, and unnecessary complexity.

## Detection Categories

### 1. Duplicate Documentation

#### A. Whole-File Duplication (Cross-File)

**Similarity Detection (Jaccard):**
```bash
# Simple word-based similarity
compare_docs() {
  local file1=$1
  local file2=$2

  # Extract words (simplified)
  words1=$(tr '[:space:]' '\n' < "$file1" | sort -u)
  words2=$(tr '[:space:]' '\n' < "$file2" | sort -u)

  # Calculate Jaccard similarity
  intersection=$(comm -12 <(echo "$words1") <(echo "$words2") | wc -l)
  union=$(cat <(echo "$words1") <(echo "$words2") | sort -u | wc -l)

  similarity=$((intersection * 100 / union))
  if [ $similarity -gt 70 ]; then
    echo "DUPLICATE: $file1 and $file2 are ${similarity}% similar"
  fi
}

# Compare all markdown files
find . -name "*.md" | while read f1; do
  find . -name "*.md" | while read f2; do
    [ "$f1" != "$f2" ] && compare_docs "$f1" "$f2"
  done
done
```

**Confidence Levels:**
- > 90% similar: HIGH (95%) - Nearly identical, clear duplication
- 70-90% similar: MEDIUM (80%) - Substantial overlap
- 50-70% similar: LOW (60%) - Some duplication, review needed

**Recommendation:**
- > 90%: DELETE one, keep most recent
- 70-90%: MERGE, preserve unique sections
- 50-70%: CROSS-LINK, explain differences

#### B. Duplicate Sections (Intra-File)

**Detect repeated sections within the same markdown file:**
```python
#!/usr/bin/env python3
"""Detect duplicate sections within markdown files"""
import hashlib
import re
from collections import defaultdict
from pathlib import Path

def extract_sections(md_content):
    """Extract sections by headers (## or ###)."""
    # Split by level-2 or level-3 headers
    sections = re.split(r'\n(#{2,3}\s+.+)', md_content)

    parsed_sections = []
    for i in range(1, len(sections), 2):
        if i+1 < len(sections):
            header = sections[i].strip()
            content = sections[i+1].strip()
            parsed_sections.append((header, content))

    return parsed_sections

def find_duplicate_sections(file_path):
    """Find duplicate or very similar sections within a markdown file."""
    with open(file_path) as f:
        content = f.read()

    sections = extract_sections(content)
    section_hashes = defaultdict(list)

    for header, content in sections:
        # Normalize content for comparison
        normalized = re.sub(r'\s+', ' ', content.lower())

        # Skip very short sections
        if len(normalized) < 100:
            continue

        # Hash the normalized content
        content_hash = hashlib.md5(normalized.encode()).hexdigest()
        section_hashes[content_hash].append(header)

    # Find duplicates
    duplicates = []
    for hash_val, headers in section_hashes.items():
        if len(headers) > 1:
            duplicates.append({
                'headers': headers,
                'count': len(headers)
            })

    return duplicates

# Usage
EXCLUDED_DIRS = {
    '.venv', 'venv', '__pycache__', '.pytest_cache',
    '.git', 'node_modules', 'dist', 'build', 'vendor'
}

for file_path in Path('.').rglob('*.md'):
    if any(ex in file_path.parts for ex in EXCLUDED_DIRS):
        continue

    dups = find_duplicate_sections(file_path)
    if dups:
        print(f"\nDUPLICATION_INTRAFILE: {file_path}")
        for dup in dups:
            headers_str = '\n    - '.join(dup['headers'])
            print(f"  {dup['count']} similar sections:")
            print(f"    - {headers_str}")
        print(f"  Recommendation: Consolidate or cross-reference")
```

**Confidence:** HIGH (85%) - exact content matches

#### C. Duplicate Paragraphs (Intra-File)

**Detect repeated paragraphs within the same document:**
```python
#!/usr/bin/env python3
"""Detect duplicate paragraphs within markdown files"""
import hashlib
import re
from collections import defaultdict
from pathlib import Path

def find_duplicate_paragraphs(file_path, min_words=20):
    """Find duplicate paragraphs (blocks separated by blank lines)."""
    with open(file_path) as f:
        content = f.read()

    # Split into paragraphs
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content)]

    para_hashes = defaultdict(list)

    for idx, paragraph in enumerate(paragraphs):
        # Skip code blocks, headers, lists
        if paragraph.startswith(('```', '#', '-', '*', '|')):
            continue

        # Normalize and check word count
        normalized = re.sub(r'\s+', ' ', paragraph.lower())
        word_count = len(normalized.split())

        if word_count < min_words:
            continue

        # Hash the paragraph
        para_hash = hashlib.md5(normalized.encode()).hexdigest()
        para_hashes[para_hash].append((idx, paragraph[:100]))

    # Find duplicates
    duplicates = []
    for hash_val, occurrences in para_hashes.items():
        if len(occurrences) > 1:
            duplicates.append({
                'count': len(occurrences),
                'positions': [occ[0] for occ in occurrences],
                'sample': occurrences[0][1]
            })

    return duplicates

# Usage
EXCLUDED_DIRS = {
    '.venv', 'venv', '__pycache__', '.git',
    'node_modules', 'dist', 'build'
}

for file_path in Path('.').rglob('*.md'):
    if any(ex in file_path.parts for ex in EXCLUDED_DIRS):
        continue

    dups = find_duplicate_paragraphs(file_path, min_words=20)
    if dups:
        print(f"\nDUPLICATION_PARAGRAPH: {file_path}")
        for dup in dups:
            positions = ', '.join(map(str, dup['positions']))
            print(f"  {dup['count']}x repeated paragraph at positions {positions}")
            print(f"  Sample: {dup['sample']}...")
        print(f"  Recommendation: Remove duplicate or use reference")
```

**Confidence:** HIGH (90%) - exact paragraph matches

#### D. Similar Explanations (Semantic)

**Detect semantically similar text (different wording, same meaning):**
```python
#!/usr/bin/env python3
"""Detect semantically similar paragraphs using TF-IDF"""
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

def find_similar_paragraphs(file_path, similarity_threshold=0.75):
    """Find paragraphs with similar meaning (different wording)."""
    try:
        with open(file_path) as f:
            content = f.read()

        # Split into paragraphs
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content)]

        # Filter: skip short, code, headers
        valid_paras = []
        for para in paragraphs:
            if (len(para.split()) >= 20 and
                not para.startswith(('```', '#', '-', '*', '|'))):
                valid_paras.append(para)

        if len(valid_paras) < 2:
            return []

        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(valid_paras)

        # Cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)

        # Find similar pairs
        similar_pairs = []
        for i in range(len(valid_paras)):
            for j in range(i+1, len(valid_paras)):
                if similarity_matrix[i][j] >= similarity_threshold:
                    similar_pairs.append({
                        'paragraphs': (i, j),
                        'similarity': f"{similarity_matrix[i][j]:.2%}",
                        'sample1': valid_paras[i][:100],
                        'sample2': valid_paras[j][:100]
                    })

        return similar_pairs

    except ImportError:
        print("Install scikit-learn for semantic similarity: pip install scikit-learn")
        return []
    except Exception as e:
        return []

# Usage
EXCLUDED_DIRS = {'.venv', 'venv', '.git', 'node_modules'}

for file_path in Path('.').rglob('*.md'):
    if any(ex in file_path.parts for ex in EXCLUDED_DIRS):
        continue

    similar = find_similar_paragraphs(file_path, similarity_threshold=0.75)
    if similar:
        print(f"\nDUPLICATION_SEMANTIC: {file_path}")
        for pair in similar:
            print(f"  Paragraphs {pair['paragraphs']} are {pair['similarity']} similar")
            print(f"    Para 1: {pair['sample1']}...")
            print(f"    Para 2: {pair['sample2']}...")
        print(f"  Recommendation: Consolidate explanations or reference")
```

**Confidence:** MEDIUM (75%) - semantic similarity can have false positives

**Summary - Documentation Duplication:**
- **Whole-file**: Jaccard similarity for cross-file comparison
- **Sections**: Hash-based for exact section matches within files
- **Paragraphs**: Hash-based for repeated paragraphs within files
- **Semantic**: TF-IDF + cosine similarity for similar meanings

### 2. Readability Metrics

**Flesch Reading Ease Score:**
```bash
# Requires py-readability-metrics (if available)
if command -v python3 &> /dev/null; then
python3 << 'EOF'
import re
from pathlib import Path

def flesch_reading_ease(text):
    """
    Flesch Reading Ease = 206.835 - 1.015(total words/total sentences)
                          - 84.6(total syllables/total words)
    Target: 70-80 (8th grade level)
    """
    # Simplified implementation
    sentences = len(re.split(r'[.!?]+', text))
    words = len(text.split())
    # Approximate syllables (1.5 avg per word)
    syllables = int(words * 1.5)

    if sentences == 0 or words == 0:
        return 0

    score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    return max(0, min(100, score))

# Excluded directories for markdown scanning
EXCLUDED_PATHS = {
    '.venv', 'venv', '__pycache__', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', '.tox', '.git',
    'node_modules', 'dist', 'build', 'vendor',
    '.vscode', '.idea'
}

# Scan all markdown files
for md_file in Path('.').rglob('*.md'):
    if any(excluded in md_file.parts for excluded in EXCLUDED_PATHS):
        continue

    text = md_file.read_text(errors='ignore')
    score = flesch_reading_ease(text)

    if score < 60:  # Below target
        print(f"READABILITY: {md_file} - Flesch score {score:.1f} (target: 70-80)")
        print(f"  Recommendation: Simplify language, shorter sentences")
EOF
fi
```

**Flesch-Kincaid Grade Level:**
```python
def fk_grade_level(text):
    """
    Target: 4-6.5 for technical documentation
    """
    sentences = len(re.split(r'[.!?]+', text))
    words = len(text.split())
    syllables = count_syllables(text)

    grade = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
    return grade
```

**Thresholds:**
- Flesch < 60: TOO COMPLEX - Simplify
- FK Grade > 8: TOO COMPLEX - Lower grade level
- Passive voice > 10%: TOO PASSIVE - Use active voice

### 3. Excessive Nesting

**Markdown Nesting Depth:**
```bash
# Find deeply nested content (> 3 levels)
find . -name "*.md" | while read file; do
  # Count nesting by indentation
  deep_nesting=$(grep "^        " "$file" | wc -l)  # 8+ spaces = 3+ levels

  if [ $deep_nesting -gt 5 ]; then
    echo "NESTING: $file has $deep_nesting deeply nested lines"
    echo "  Recommendation: Flatten structure, max 3 levels"
  fi
done

# Find excessive list nesting
grep -rn "^    - \|^        - \|^            - " --include="*.md" . | \
awk -F: '{
  gsub(/^[ ]+/, "", $2)
  depth = (length($0) - length($2)) / 4
  if (depth > 3) {
    print "NESTING: " $1 " has nesting depth " depth " (max: 3)"
  }
}'
```

**Confidence:** HIGH (85%) - Nesting > 3 levels is objectively problematic

**Recommendation:** REFACTOR - Flatten to max 3 levels

### 4. Verbose Content

**Word Count Analysis:**
```bash
# Find overly long documents
find . -name "*.md" | while read file; do
  words=$(wc -w < "$file")
  lines=$(wc -l < "$file")

  if [ $words -gt 5000 ]; then
    echo "VERBOSE: $file has $words words (${lines} lines)"
    echo "  Recommendation: Split into multiple focused docs"
  fi
done
```

**Code Block Analysis:**
```bash
# Find excessive code examples
find . -name "*.md" | while read file; do
  code_blocks=$(grep -c "^\`\`\`" "$file")
  total_lines=$(wc -l < "$file")

  if [ $code_blocks -gt 20 ]; then
    echo "VERBOSE: $file has $code_blocks code blocks"
    echo "  Recommendation: Move examples to separate files"
  fi
done
```

**Thresholds:**
- > 5,000 words: Consider splitting
- > 20 code blocks: Extract to examples/
- > 10 images: Extract to dedicated gallery

### 5. Table Bloat

**Large Tables:**
```bash
# Find large markdown tables
find . -name "*.md" | while read file; do
  # Count table rows
  in_table=0
  table_rows=0

  while IFS= read -r line; do
    if [[ $line =~ ^\| ]]; then
      ((table_rows++))
    else
      if [ $table_rows -gt 10 ]; then
        echo "TABLE_BLOAT: $file has ${table_rows}-row table"
        echo "  Recommendation: Split into multiple tables or use different format"
      fi
      table_rows=0
    fi
  done < "$file"
done
```

**Markdown Limitation:** No multi-line cell support, tables > 10 rows hard to maintain

### 6. Redundant Frontmatter

**Detect Duplicate Metadata:**
```bash
# Extract frontmatter from all docs
find . -name "*.md" | while read file; do
  # Extract YAML frontmatter (between --- markers)
  frontmatter=$(awk '/^---$/{flag=!flag; next} flag' "$file")

  # Check for redundant fields
  echo "$frontmatter" | grep -E "author:|date:|version:" | \
  while read field; do
    # If field is same across many docs, might be redundant
    echo "$field from $file"
  done
done | sort | uniq -c | sort -rn
```

## Similarity Algorithms

### Jaccard Similarity (Implemented Above)
```python
def jaccard_similarity(doc1, doc2):
    words1 = set(doc1.split())
    words2 = set(doc2.split())
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union) if union else 0
```

### Cosine Similarity (Advanced)
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def cosine_similarity_docs(docs):
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(docs)
    similarity_matrix = cosine_similarity(tfidf)
    return similarity_matrix
```

## Scoring Algorithm

```python
def calculate_doc_bloat_score(file_path, metrics):
    score = 0

    # Duplication penalty
    if metrics['similarity'] > 90:
        score += 40
    elif metrics['similarity'] > 70:
        score += 25

    # Readability penalty
    if metrics['flesch_score'] < 60:
        score += 15

    # Nesting penalty
    if metrics['max_nesting'] > 3:
        score += 20

    # Verbosity penalty
    if metrics['word_count'] > 5000:
        score += 15
    if metrics['code_blocks'] > 20:
        score += 10

    # Table bloat penalty
    if metrics['max_table_rows'] > 10:
        score += 10

    return min(score, 100)
```

## Output Format

```yaml
file: docs/old-api-guide.md
bloat_score: 88/100
confidence: HIGH
metrics:
  similarity:
    - docs/api-reference.md: 91% similar
    - docs/api-quickstart.md: 76% similar
  readability:
    flesch_score: 52 (target: 70-80)
    fk_grade: 9.2 (target: 4-6.5)
    passive_voice: 14% (target: <10%)
  structure:
    max_nesting: 5 levels (target: 3)
    word_count: 6,847 (high)
    code_blocks: 28 (excessive)
  tables:
    max_rows: 15 (target: <10)
token_estimate: ~8,200 tokens
recommendations:
  primary: MERGE
  rationale: 91% duplicate of api-reference.md
  steps:
    - Compare with docs/api-reference.md
    - Preserve 7 unique code examples
    - Update api-reference.md with missing content
    - Delete docs/old-api-guide.md
    - Redirect old links to api-reference.md
  estimated_token_savings: ~7,400 tokens
  risk: LOW (backup before deletion)
```

## Advanced Detection (Optional Tools)

### Using mrkdwn_analysis (Python Library)

```python
from markdown_analysis import analyze

stats = analyze('document.md')
print(f"Word count: {stats['word_count']}")
print(f"Reading time: {stats['reading_time']} minutes")
print(f"Complexity: {stats['complexity']}")
```

### Using wordcountaddin (R)

For R Markdown documents, use wordcountaddin for readability statistics.

## Automation

**Batch Similarity Check:**
```bash
#!/bin/bash
# compare_all_docs.sh

for f1 in docs/*.md; do
  for f2 in docs/*.md; do
    if [ "$f1" != "$f2" ] && [ "$f1" \< "$f2" ]; then
      similarity=$(compare_docs "$f1" "$f2")
      if [ $similarity -gt 70 ]; then
        echo "$similarity% | $f1 <-> $f2"
      fi
    fi
  done
done | sort -rn > doc_similarity_report.txt
```

## Integration with Quick Scan

Documentation bloat feeds into overall bloat report:

```python
def integrate_doc_bloat(quick_scan_findings, doc_bloat_findings):
    # Combine findings
    all_findings = quick_scan_findings + doc_bloat_findings

    # Re-prioritize
    all_findings.sort(key=lambda f: f.priority, reverse=True)

    return all_findings
```

## False Positive Mitigation

**Legitimate Documentation Patterns:**
- API references: Naturally verbose, tables > 10 rows OK
- Tutorials: Code examples expected, > 20 blocks OK
- Changelogs: Nesting OK, duplication across versions OK

**Whitelist:**
```yaml
# .bloat-docs-ignore
paths:
  - docs/api/           # API reference can be long
  - CHANGELOG.md        # Historical, don't optimize
  - docs/examples/      # Code examples expected
```

## Next Steps

Based on documentation bloat findings:
- **High Similarity**: Merge or delete duplicate
- **Low Readability**: Simplify language, shorter sentences
- **Excessive Nesting**: Flatten structure
- **Verbose**: Split into focused sections
- **Large Tables**: Break into multiple or change format

All actions require review and approval before execution.
