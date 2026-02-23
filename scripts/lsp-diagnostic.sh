#!/usr/bin/env bash
# LSP Diagnostic Script for Claude Code
# Verifies LSP setup and helps troubleshoot issues

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Claude Code LSP Diagnostic Tool${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo

# Function to check status
check_status() {
    local name="$1"
    local command="$2"
    local description="$3"

    echo -n "Checking $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description"
        return 1
    fi
}

# Function to get path
get_path() {
    local name="$1"
    local path=$(which "$name" 2>/dev/null || echo "")
    if [ -n "$path" ]; then
        echo -e "  ${BLUE}→${NC} $path"
    fi
}

echo -e "${YELLOW}1. Environment Configuration${NC}"
echo "─────────────────────────────"

# Check ENABLE_LSP_TOOL
if [ "${ENABLE_LSP_TOOL:-}" = "1" ]; then
    echo -e "${GREEN}✓${NC} ENABLE_LSP_TOOL=1 (correctly set)"
else
    echo -e "${RED}✗${NC} ENABLE_LSP_TOOL not set to 1"
    echo -e "  ${YELLOW}Fix:${NC} export ENABLE_LSP_TOOL=1"
fi

# Check if it's in shell rc
if grep -q "ENABLE_LSP_TOOL" ~/.bashrc ~/.zshrc 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Found in shell RC file (persisted)"
else
    echo -e "${YELLOW}⚠${NC}  Not found in ~/.bashrc or ~/.zshrc"
    echo -e "  ${YELLOW}Tip:${NC} Add 'export ENABLE_LSP_TOOL=1' to make permanent"
fi

echo

echo -e "${YELLOW}2. Claude Code Version${NC}"
echo "─────────────────────────────"
claude_version=$(claude --version 2>&1 | head -1 || echo "unknown")
echo -e "  Version: $claude_version"

# Check if version is 2.0.74+
if [[ "$claude_version" =~ ([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
    major="${BASH_REMATCH[1]}"
    minor="${BASH_REMATCH[2]}"
    patch="${BASH_REMATCH[3]}"

    if [ "$major" -ge 2 ] && [ "$minor" -ge 0 ] && [ "$patch" -ge 74 ]; then
        echo -e "${GREEN}✓${NC} Version supports native LSP (requires 2.0.74+)"
    else
        echo -e "${RED}✗${NC} Version too old for native LSP support"
        echo -e "  ${YELLOW}Upgrade:${NC} Update Claude Code to 2.0.74 or later"
    fi
fi

echo

echo -e "${YELLOW}3. Language Servers Installed${NC}"
echo "─────────────────────────────"

# Python - pyright
if check_status "Python (pyright)" "command -v pyright" "pyright installed"; then
    get_path "pyright"
    pyright_ver=$(pyright --version 2>/dev/null | head -1 || echo "unknown")
    echo -e "  ${BLUE}→${NC} $pyright_ver"

    # Check for pyright-langserver
    if command -v pyright-langserver > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} pyright-langserver binary found"
        get_path "pyright-langserver"
    else
        echo -e "  ${YELLOW}⚠${NC}  pyright-langserver not found (may still work)"
    fi
fi

echo

# TypeScript/JavaScript
if check_status "TypeScript/JS (typescript-language-server)" "command -v typescript-language-server" "typescript-language-server installed"; then
    get_path "typescript-language-server"
    ts_ver=$(typescript-language-server --version 2>/dev/null || echo "unknown")
    echo -e "  ${BLUE}→${NC} Version: $ts_ver"
fi

echo

# Rust
if check_status "Rust (rust-analyzer)" "command -v rust-analyzer" "rust-analyzer installed"; then
    get_path "rust-analyzer"
else
    echo -e "  ${BLUE}ℹ${NC}  Optional: Install with 'rustup component add rust-analyzer'"
fi

echo

echo -e "${YELLOW}4. Claude Code LSP Plugins${NC}"
echo "─────────────────────────────"

plugin_dir="$HOME/.claude/plugins/cache/claude-plugins-official"

# Check for LSP plugins
if [ -d "$plugin_dir" ]; then
    lsp_plugins=$(ls -1 "$plugin_dir" 2>/dev/null | grep -i lsp || echo "")

    if [ -n "$lsp_plugins" ]; then
        echo "$lsp_plugins" | while read -r plugin; do
            if [ -d "$plugin_dir/$plugin" ]; then
                version=$(ls -1 "$plugin_dir/$plugin" 2>/dev/null | head -1 || echo "unknown")
                echo -e "${GREEN}✓${NC} $plugin (v$version)"
            fi
        done
    else
        echo -e "${RED}✗${NC} No LSP plugins found in claude-plugins-official"
    fi
else
    echo -e "${RED}✗${NC} Plugin directory not found: $plugin_dir"
fi

# Check settings.json for enabled plugins
settings_file="$HOME/.claude/settings.json"
if [ -f "$settings_file" ]; then
    enabled_lsp=$(grep -o '"[^"]*lsp[^"]*"[[:space:]]*:[[:space:]]*true' "$settings_file" 2>/dev/null | grep -o '"[^"]*lsp[^"]*"' | tr -d '"' || echo "")

    if [ -n "$enabled_lsp" ]; then
        echo
        echo -e "${BLUE}Enabled in settings.json:${NC}"
        echo "$enabled_lsp" | while read -r plugin; do
            echo -e "  ${GREEN}✓${NC} $plugin"
        done
    fi
fi

echo

echo -e "${YELLOW}5. Active LSP Servers${NC}"
echo "─────────────────────────────"

# Check for running language servers
lsp_processes=$(ps aux | grep -E "pyright|typescript-language-server|rust-analyzer" | grep -v grep || echo "")

if [ -n "$lsp_processes" ]; then
    echo -e "${GREEN}✓${NC} Language servers are running:"
    echo "$lsp_processes" | while read -r line; do
        echo -e "  ${BLUE}→${NC} $(echo $line | awk '{print $11, $12, $13}')"
    done
else
    echo -e "${YELLOW}⚠${NC}  No language servers currently running"
    echo -e "  ${BLUE}ℹ${NC}  This is normal - servers start on-demand when needed"
fi

echo

echo -e "${YELLOW}6. Project Detection${NC}"
echo "─────────────────────────────"

# Check for project configuration files
current_dir=$(pwd)
echo -e "Current directory: ${BLUE}$current_dir${NC}"

project_files_found=false

if [ -f "pyproject.toml" ]; then
    echo -e "${GREEN}✓${NC} Python project detected (pyproject.toml)"
    project_files_found=true
fi

if [ -f "package.json" ]; then
    echo -e "${GREEN}✓${NC} Node.js project detected (package.json)"
    project_files_found=true
fi

if [ -f "tsconfig.json" ]; then
    echo -e "${GREEN}✓${NC} TypeScript project detected (tsconfig.json)"
    project_files_found=true
fi

if [ -f "Cargo.toml" ]; then
    echo -e "${GREEN}✓${NC} Rust project detected (Cargo.toml)"
    project_files_found=true
fi

if [ -f "go.mod" ]; then
    echo -e "${GREEN}✓${NC} Go project detected (go.mod)"
    project_files_found=true
fi

if [ "$project_files_found" = false ]; then
    echo -e "${YELLOW}⚠${NC}  No project configuration files found"
    echo -e "  ${BLUE}ℹ${NC}  LSP works best in projects with config files"
fi

echo

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Diagnostic Summary${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"

# Final recommendation
all_good=true

if [ "${ENABLE_LSP_TOOL:-}" != "1" ]; then
    all_good=false
    echo -e "${RED}✗${NC} Environment variable not set"
    echo -e "  ${YELLOW}Action:${NC} Run 'export ENABLE_LSP_TOOL=1' and add to ~/.bashrc"
fi

if ! command -v pyright > /dev/null 2>&1; then
    all_good=false
    echo -e "${RED}✗${NC} Python language server not installed"
    echo -e "  ${YELLOW}Action:${NC} Run 'npm install -g pyright'"
fi

if [ ! -d "$plugin_dir" ] || [ -z "$(ls -1 "$plugin_dir" 2>/dev/null | grep -i lsp)" ]; then
    all_good=false
    echo -e "${RED}✗${NC} LSP plugins not installed"
    echo -e "  ${YELLOW}Action:${NC} Run Claude Code and install plugins:"
    echo -e "    ${BLUE}→${NC} /plugin install pyright-lsp@claude-plugins-official"
    echo -e "    ${BLUE}→${NC} /plugin install typescript-lsp@claude-plugins-official"
fi

if [ "$all_good" = true ]; then
    echo
    echo -e "${GREEN}✓ LSP is correctly configured!${NC}"
    echo
    echo -e "${BLUE}How to use LSP:${NC}"
    echo -e "  1. Language servers start automatically when Claude accesses code files"
    echo -e "  2. Use semantic queries like:"
    echo -e "     ${YELLOW}→${NC} \"Find all references to the X function\""
    echo -e "     ${YELLOW}→${NC} \"Go to definition of Y class\""
    echo -e "     ${YELLOW}→${NC} \"Show me all call sites of Z method\""
    echo -e "  3. LSP provides semantic understanding (not just text matching)"
    echo
    echo -e "${YELLOW}Note:${NC} Plugins installed via marketplace are available immediately (Claude Code 2.1.45+)."
    echo -e "  ${BLUE}→${NC} For older versions, restart Claude Code after installing plugins."
fi

echo
