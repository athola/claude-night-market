"""Language detection skill for parseltongue."""

from __future__ import annotations

import re
from typing import Any


class LanguageDetectionSkill:
    """Skill for detecting programming languages in code."""

    # Extension to language mapping
    _EXT_MAP: dict[str, tuple[str, float]] = {
        ".py": ("python", 0.95),
        ".js": ("javascript", 0.95),
        ".jsx": ("javascript", 0.95),
        ".ts": ("typescript", 0.95),
        ".tsx": ("typescript", 0.95),
        ".rs": ("rust", 0.95),
        ".go": ("go", 0.95),
    }

    # Language keyword sets
    _PYTHON_KW = {
        "def",
        "class",
        "import",
        "from",
        "async",
        "await",
        "yield",
        "lambda",
        "with",
        "elif",
        "except",
        "raise",
        "pass",
        "True",
        "False",
        "None",
    }
    _JS_KW = {
        "function",
        "const",
        "let",
        "var",
        "class",
        "constructor",
        "this",
        "prototype",
        "async",
        "await",
        "new",
        "typeof",
        "undefined",
        "null",
        "=>",
    }
    _TS_KW = {
        "interface",
        "type",
        "enum",
        "namespace",
        "declare",
        "readonly",
        "abstract",
        "implements",
    }
    _RUST_KW = {
        "fn",
        "let",
        "mut",
        "impl",
        "struct",
        "enum",
        "trait",
        "pub",
        "use",
        "mod",
        "crate",
        "match",
        "unsafe",
    }

    def __init__(self) -> None:
        """Initialize the language detection skill."""
        pass

    def detect_language(self, code: str, filename: str = "") -> dict[str, Any]:
        """Detect the programming language of the provided code.

        Args:
            code: Code to analyze
            filename: Optional filename hint

        Returns:
            Dictionary containing language detection results

        Raises:
            TypeError: If code is not a string
        """
        if code is None:
            msg = "code must be a string, not None"  # type: ignore[unreachable]
            raise TypeError(msg)
        if not isinstance(code, str):
            msg = f"code must be a string, got {type(code).__name__}"  # type: ignore[unreachable]
            raise TypeError(msg)

        # Try filename first
        for ext, (language, confidence) in self._EXT_MAP.items():
            if filename.endswith(ext):
                features = self._detect_features_for_language(code, language)
                return {
                    "language": language,
                    "confidence": confidence,
                    "features": features,
                }

        return self._detect_from_content(code)

    def _detect_from_content(self, code: str) -> dict[str, Any]:
        """Detect language from code content using heuristics."""
        if not code or not code.strip():
            return {
                "language": "unknown",
                "confidence": 0,
                "features": [],
                "reasoning": [],
            }

        scores: dict[str, float] = {
            "python": 0,
            "javascript": 0,
            "typescript": 0,
            "rust": 0,
        }
        reasoning: list[str] = []
        detected_keywords: list[str] = []

        # Python indicators
        for kw in self._PYTHON_KW:
            if re.search(r"\b" + re.escape(kw) + r"\b", code):
                scores["python"] += 1
                detected_keywords.append(kw)
        # Exclusive Python syntax: def keyword is unique to Python
        if re.search(r"\bdef\s+\w+", code):
            scores["python"] += 1
        if re.search(r"@\w+", code):
            scores["python"] += 0.5
        if "self" in code and "def " in code:
            scores["python"] += 2

        # TypeScript indicators (check before JS)
        ts_specific_count = 0
        for kw in self._TS_KW:
            if re.search(r"\b" + re.escape(kw) + r"\b", code):
                scores["typescript"] += 2
                ts_specific_count += 1
                detected_keywords.append(kw)
        # TS type annotations in params and return types
        ts_type_annotations = len(
            re.findall(
                r"(?:\w+|\))\s*:\s*"
                r"(?:string|number|boolean|void|any|never"
                r"|Promise|Map|Set|Array)\b",
                code,
            )
        )
        if ts_type_annotations:
            scores["typescript"] += 2 * ts_type_annotations
            ts_specific_count += ts_type_annotations

        # JavaScript indicators
        js_score_raw = 0.0
        for kw in self._JS_KW:
            if re.search(r"\b" + re.escape(kw) + r"\b", code):
                scores["javascript"] += 1
                js_score_raw += 1
                detected_keywords.append(kw)
        # JS-specific syntax: function/method with braces
        if re.search(r"\w+\s*\([^)]*\)[^{\n]*\{", code):
            scores["javascript"] += 1.5
            js_score_raw += 1.5
        # Class with braces (JS/TS, not Python)
        if re.search(r"\bclass\s+\w+\s*\{", code):
            scores["javascript"] += 1.5
            js_score_raw += 1.5
        # C-style comments (// or /* */)
        if re.search(r"//\s", code) or re.search(r"/\*", code):
            scores["javascript"] += 1
            js_score_raw += 1

        # TypeScript is a superset of JavaScript: when TS-specific
        # keywords are present, JS keywords also count toward TS
        if ts_specific_count > 0:
            scores["typescript"] += js_score_raw

        # Rust indicators (higher weight: Rust keywords are unique)
        for kw in self._RUST_KW:
            if re.search(r"\b" + re.escape(kw) + r"\b", code):
                scores["rust"] += 2
                detected_keywords.append(kw)

        # Find best match
        best_lang = max(scores, key=lambda k: scores[k])
        best_score = scores[best_lang]

        # Require a minimum score to declare a language detected
        if best_score < 1.5:
            return {
                "language": "unknown",
                "confidence": 0,
                "features": [],
                "detected_keywords": detected_keywords,
                "reasoning": ["No strong language indicators found"],
            }

        # Normalize confidence
        total = sum(scores.values())
        confidence = best_score / total if total > 0 else 0
        confidence = min(0.99, max(0.51, confidence))

        # Boost confidence for strong signals
        if best_score >= 10:
            confidence = max(confidence, 0.95)
        elif best_score >= 5:
            confidence = max(confidence, 0.91)

        features = self._detect_features_for_language(code, best_lang)
        reasoning.append(f"Detected {best_lang} with score {best_score:.1f}")

        return {
            "language": best_lang,
            "confidence": confidence,
            "features": features,
            "detected_keywords": detected_keywords,
            "reasoning": reasoning,
        }

    def _detect_features_for_language(self, code: str, language: str) -> list[str]:
        """Detect language-specific features in code."""
        features: list[str] = []

        if language == "python":
            features.append("python")
            if re.search(r":\s*\w+", code) and "def " in code:
                features.append("type_hints")
            if "class " in code:
                features.append("classes")
            if "async " in code:
                features.append("async_functions")
            if "@" in code:
                features.append("decorators")

        elif language == "javascript":
            if "class " in code:
                features.append("classes")
            if "async " in code:
                features.append("async_methods")
            if "prototype" in code or ".push(" in code:
                features.append("prototype")
            if "=>" in code:
                features.append("arrow_functions")

        elif language == "typescript":
            if "interface " in code:
                features.append("interfaces")
            if re.search(r"\w+\s*:\s*(string|number|boolean)", code):
                features.append("type_annotations")
            if "<" in code and ">" in code:
                features.append("generics")

        elif language == "rust":
            if "struct " in code:
                features.append("structs")
            if "trait " in code or "impl " in code:
                features.append("traits")
            if re.search(r"&'\w+", code) or re.search(r"&(?:self|mut\s|\[)", code):
                features.append("lifetime_annotations")
            if "Result<" in code or "Err(" in code:
                features.append("error_handling")

        return features

    def analyze_features(self, code: str, language: str) -> dict[str, Any]:
        """Analyze language-specific features in code.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            Dictionary containing feature analysis
        """
        features: dict[str, Any] = {
            "functions": 0,
            "classes": 0,
            "class_names": [],
            "imports": 0,
            "decorators": 0,
            "data_structures": {},
            "keywords": [],
        }

        if not code:
            return {"features": features}

        if language == "python":
            features["functions"] = len(re.findall(r"\bdef\s+\w+", code))
            features["classes"] = len(re.findall(r"\bclass\s+\w+", code))
            features["class_names"] = re.findall(r"\bclass\s+(\w+)", code)
            features["imports"] = len(re.findall(r"\b(?:import|from)\s+\w+", code))
            features["decorators"] = len(re.findall(r"@\w+", code))
            features["async_methods"] = len(re.findall(r"\basync\s+def\s+", code))

            # Detect keywords
            for kw in self._PYTHON_KW:
                if re.search(r"\b" + re.escape(kw) + r"\b", code):
                    features["keywords"].append(kw)

            # Detect features list items
            if "@dataclass" in code:
                features["dataclass"] = True
            if re.search(r":\s*\w+", code) and "def " in code:
                features["type_hint"] = True
            if "async " in code:
                features["async"] = True

        elif language == "javascript":
            features["classes"] = len(re.findall(r"\bclass\s+\w+", code))
            features["class_names"] = re.findall(r"\bclass\s+(\w+)", code)
            features["async_methods"] = len(re.findall(r"\basync\s+\w+", code))
            features["data_structures"] = {
                "Map": len(re.findall(r"\bnew\s+Map\b", code)),
                "Set": len(re.findall(r"\bnew\s+Set\b", code)),
                "Array": len(re.findall(r"\[\]|Array\b", code)),
            }

        elif language == "typescript":
            features["interfaces"] = len(re.findall(r"\binterface\s+\w+", code))
            features["interface_names"] = re.findall(r"\binterface\s+(\w+)", code)
            features["type_annotations"] = len(
                re.findall(
                    r":\s*(?:string|number|boolean|void|any|"
                    r"Promise|Map|User\b|\w+\[\])",
                    code,
                )
            )
            features["optional_properties"] = len(re.findall(r"\w+\?\s*:", code))
            features["classes"] = len(re.findall(r"\bclass\s+\w+", code))
            features["class_names"] = re.findall(r"\bclass\s+(\w+)", code)

        elif language == "rust":
            features["structs"] = len(re.findall(r"\bstruct\s+\w+", code))
            features["struct_names"] = re.findall(r"\bstruct\s+(\w+)", code)
            features["impl_blocks"] = len(re.findall(r"\bimpl\s+\w+", code))
            features["error_handling"] = {
                "Result": len(re.findall(r"\bResult<", code)),
                "Option": len(re.findall(r"\bOption<", code)),
            }
            features["concurrency"] = {
                "Arc": len(re.findall(r"\bArc<", code)),
                "Mutex": len(re.findall(r"\bMutex<", code)),
            }
            # Detect keywords
            for kw in self._RUST_KW:
                if re.search(r"\b" + re.escape(kw) + r"\b", code):
                    features["keywords"].append(kw)

        elif language == "go":
            features["functions"] = len(re.findall(r"\bfunc\s+\w+", code))
            features["goroutines"] = len(re.findall(r"\bgo\s+func\b", code))
            features["channels"] = len(re.findall(r"\bmake\(chan\b", code))

        return {"features": features}

    def analyze_python_version(self, code: str) -> dict[str, Any]:
        """Analyze which Python version features are used.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing version analysis
        """
        features: list[str] = []
        min_version = "3.6"

        if "from __future__ import" in code:
            features.append("future_import")

        if re.search(r"\bmatch\s+\w+.*:\s*\n\s*case\s+", code, re.DOTALL):
            features.append("match_statement")
            min_version = "3.10"

        if re.search(r"\bTypeAlias\b", code):
            features.append("type_alias")
            min_version = max(min_version, "3.10")

        if re.search(r":\s*\w+\s*\|\s*\w+", code):
            features.append("union_syntax")
            min_version = max(min_version, "3.10")

        if ":=" in code:
            features.append("walrus_operator")
            min_version = max(min_version, "3.8")

        return {
            "minimum_version": min_version,
            "features": features,
        }

    def analyze_javascript_version(self, code: str) -> dict[str, Any]:
        """Analyze which ES version features are used.

        Args:
            code: JavaScript code to analyze

        Returns:
            Dictionary containing version analysis
        """
        features: list[str] = []
        es_version = "ES5"

        if "class " in code:
            features.append("class_syntax")
            es_version = "ES2015"

        if "async " in code or "await " in code:
            features.append("async_await")
            es_version = "ES2018"

        if "=>" in code:
            features.append("arrow_functions")
            es_version = max(es_version, "ES2015")

        if "const " in code or "let " in code:
            features.append("block_scoping")
            es_version = max(es_version, "ES2015")

        if "..." in code:
            features.append("spread_operator")
            es_version = max(es_version, "ES2015")

        return {"es_version": es_version, "features": features}

    def analyze_typescript_version(self, code: str) -> dict[str, Any]:
        """Analyze which TypeScript version features are used.

        Args:
            code: TypeScript code to analyze

        Returns:
            Dictionary containing version analysis
        """
        features: list[str] = []
        ts_version = "2.0"

        if "interface " in code:
            features.append("interfaces")

        if re.search(r"<\w+>", code):
            features.append("generic_classes")
            ts_version = max(ts_version, "2.0")

        if re.search(r"\breadonly\b", code):
            features.append("readonly_properties")
            ts_version = max(ts_version, "3.0")

        if "?." in code:
            features.append("optional_chaining")
            ts_version = max(ts_version, "3.7")

        if "??" in code:
            features.append("nullish_coalescing")
            ts_version = max(ts_version, "3.7")

        if "as const" in code:
            features.append("const_assertions")
            ts_version = max(ts_version, "3.4")

        return {
            "typescript_version": ts_version,
            "features": features,
        }

    def analyze_rust_edition(self, code: str) -> dict[str, Any]:
        """Analyze which Rust edition features are used.

        Args:
            code: Rust code to analyze

        Returns:
            Dictionary containing edition analysis
        """
        features: list[str] = []
        edition = "2018"

        if "async " in code or "await " in code:
            features.append("async_await")
            edition = "2018"

        if re.search(r"\bArc<", code) or re.search(r"\bMutex<", code):
            features.append("async_await")
            edition = max(edition, "2018")

        if "Result<" in code:
            features.append("result_type")

        if "#[derive" in code and "Serialize" in code:
            features.append("serde_derive")

        if "dyn " in code:
            features.append("dyn_trait")
            edition = max(edition, "2018")

        return {"edition": edition, "features": features}

    def detect_frameworks(self, code: str, language: str) -> dict[str, Any]:
        """Detect frameworks and libraries used in code.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            Dictionary containing framework analysis
        """
        frameworks: dict[str, Any] = {}

        if language == "python":
            if "django" in code.lower():
                components: dict[str, bool] = {}
                if "models" in code:
                    components["models"] = True
                if "views" in code or "View" in code:
                    components["views"] = True
                if "serializers" in code:
                    components["serializers"] = True
                frameworks["django"] = {"components": components}

            if "rest_framework" in code:
                frameworks["djangorestframework"] = {
                    "components": {"serializers": True},
                }

            if "flask" in code.lower():
                frameworks["flask"] = {"detected": True}

            if "fastapi" in code.lower():
                frameworks["fastapi"] = {"detected": True}

        return {"frameworks": frameworks}

    def detect_design_patterns(self, code: str, language: str) -> dict[str, Any]:
        """Detect design patterns in code.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            Dictionary containing design pattern analysis
        """
        patterns: list[str] = []

        if "Service" in code:
            patterns.append("service")
        if "Repository" in code:
            patterns.append("repository")
        elif "def get_" in code and "def create_" in code:
            patterns.append("repository-like")

        return {"patterns": patterns}

    def detect_primary_language(self, code: str) -> dict[str, Any]:
        """Detect the primary language in mixed-language content.

        Args:
            code: Mixed-language code

        Returns:
            Dictionary containing primary language detection
        """
        if not code or not code.strip():
            return {
                "primary_language": "unknown",
                "confidence": 0,
                "detected_languages": [],
            }

        result = self._detect_from_content(code)
        detected: list[str] = []

        # Check for multiple languages
        scores: dict[str, int] = {}
        for kw in self._PYTHON_KW:
            if re.search(r"\b" + re.escape(kw) + r"\b", code):
                scores["python"] = scores.get("python", 0) + 1
        for kw in self._JS_KW:
            if re.search(r"\b" + re.escape(kw) + r"\b", code):
                scores["javascript"] = scores.get("javascript", 0) + 1
        for kw in self._TS_KW:
            if re.search(r"\b" + re.escape(kw) + r"\b", code):
                scores["typescript"] = scores.get("typescript", 0) + 1
        for kw in self._RUST_KW:
            if re.search(r"\b" + re.escape(kw) + r"\b", code):
                scores["rust"] = scores.get("rust", 0) + 1

        for lang, score in scores.items():
            if score > 0:
                detected.append(lang)

        return {
            "primary_language": result["language"],
            "confidence": result["confidence"],
            "detected_languages": detected,
        }

    def analyze_complexity(self, code: str, language: str = "python") -> dict[str, Any]:
        """Analyze code complexity metrics.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            Dictionary containing complexity metrics
        """
        if not code:
            return {
                "cyclomatic_complexity": 1,
                "nesting_depth": 0,
                "complexity_level": "low",
                "suggestions": [],
                "recommendations": [],
            }

        # Calculate cyclomatic complexity
        branch_keywords = [
            "if ",
            "elif ",
            "else:",
            "for ",
            "while ",
            "except ",
            "case ",
            "and ",
            "or ",
        ]
        complexity = 1
        for kw in branch_keywords:
            complexity += code.count(kw)

        # Calculate nesting depth
        max_depth = 0
        for line in code.split("\n"):
            stripped = line.rstrip()
            if stripped:
                indent = len(line) - len(line.lstrip())
                depth = indent // 4
                max_depth = max(max_depth, depth)

        # Determine complexity level
        if complexity <= 5:
            level = "low"
        elif complexity <= 10:
            level = "medium"
        elif complexity <= 20:
            level = "high"
        else:
            level = "very_high"

        suggestions: list[str] = []
        recommendations: list[str] = []
        if max_depth > 4:
            suggestions.append("Reduce nesting depth")
            recommendations.append("Extract deeply nested code into helper functions")
        if complexity > 10:
            suggestions.append("Reduce cyclomatic complexity")
            recommendations.append("Break up complex functions")

        return {
            "cyclomatic_complexity": complexity,
            "nesting_depth": max_depth,
            "complexity_level": level,
            "suggestions": suggestions,
            "recommendations": recommendations,
        }

    def analyze_async_features(self, code: str, language: str) -> dict[str, Any]:
        """Analyze async-specific features in code.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            Dictionary containing async feature analysis
        """
        async_features: dict[str, int] = {
            "async_functions": 0,
            "async_context_managers": 0,
            "await_calls": 0,
        }

        if language == "python":
            async_features["async_functions"] = len(
                re.findall(r"\basync\s+def\s+", code)
            )
            async_features["async_context_managers"] = len(
                re.findall(r"\basync\s+with\b", code)
            ) + len(re.findall(r"__aenter__", code))
            async_features["await_calls"] = len(re.findall(r"\bawait\s+", code))

        return {"async_features": async_features}

    def analyze_dependencies(self, code: str, language: str) -> dict[str, Any]:
        """Analyze code dependencies and imports.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            Dictionary containing dependency analysis
        """
        dependencies: dict[str, Any] = {
            "standard_library": [],
            "third_party": [],
            "local": [],
        }

        if not code:
            return {"dependencies": dependencies}

        if language == "python":
            stdlib_modules = {
                "os",
                "sys",
                "re",
                "json",
                "typing",
                "asyncio",
                "pathlib",
                "collections",
                "functools",
                "itertools",
                "math",
                "datetime",
                "logging",
                "io",
                "abc",
                "dataclasses",
                "contextlib",
                "unittest",
                "tempfile",
                "shutil",
                "subprocess",
                "threading",
                "multiprocessing",
                "copy",
                "enum",
                "warnings",
                "textwrap",
                "hashlib",
                "time",
                "signal",
                "socket",
                "http",
                "urllib",
            }

            # Parse import statements
            for match in re.finditer(r"^import\s+(\w+)", code, re.MULTILINE):
                mod = match.group(1)
                if mod in stdlib_modules:
                    if mod not in dependencies["standard_library"]:
                        dependencies["standard_library"].append(mod)
                elif mod not in dependencies["third_party"]:
                    dependencies["third_party"].append(mod)

            for match in re.finditer(r"^from\s+(\S+)\s+import", code, re.MULTILINE):
                raw_mod = match.group(1)
                if raw_mod.startswith("."):
                    if raw_mod not in dependencies["local"]:
                        dependencies["local"].append(raw_mod)
                else:
                    mod = raw_mod.split(".")[0]
                    if mod in stdlib_modules:
                        if mod not in dependencies["standard_library"]:
                            dependencies["standard_library"].append(mod)
                    elif mod not in dependencies["third_party"]:
                        dependencies["third_party"].append(mod)

        return {"dependencies": dependencies}
