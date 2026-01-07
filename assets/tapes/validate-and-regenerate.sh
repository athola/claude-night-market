#!/usr/bin/env bash
#
# Validate VHS tape commands and regenerate GIF
#
# Usage:
#   ./validate-and-regenerate.sh skills-showcase
#   ./validate-and-regenerate.sh --all
#

set -euo pipefail

TAPE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$TAPE_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

validate_tape() {
    local tape_file="$1"
    local tape_name="$(basename "$tape_file" .tape)"

    echo -e "${YELLOW}Validating $tape_name...${NC}"

    # Check for Output directive
    if ! grep -q '^Output ' "$tape_file"; then
        echo -e "${RED}ERROR: Missing Output directive${NC}"
        return 1
    fi

    # Check for balanced quotes in Type directives
    while IFS= read -r line; do
        quote_count=$(echo "$line" | tr -cd '"' | wc -c)
        if [ $((quote_count % 2)) -ne 0 ]; then
            echo -e "${RED}ERROR: Unbalanced quotes: $line${NC}"
            return 1
        fi
    done < <(grep '^Type ' "$tape_file")

    # Extract and count commands
    local cmd_count=$(grep -c '^Type ' "$tape_file" || echo "0")
    local sleep_count=$(grep -c '^Sleep ' "$tape_file" || echo "0")

    echo -e "${GREEN}✓ Syntax valid${NC}"
    echo "  Commands: $cmd_count"
    echo "  Sleeps: $sleep_count"

    return 0
}

regenerate_gif() {
    local tape_file="$1"
    local tape_name="$(basename "$tape_file" .tape)"

    echo -e "${YELLOW}Generating GIF for $tape_name...${NC}"

    # Run VHS
    if vhs "$tape_file"; then
        local gif_file="$PROJECT_ROOT/assets/gifs/${tape_name}.gif"
        if [ -f "$gif_file" ]; then
            local size=$(du -h "$gif_file" | cut -f1)
            echo -e "${GREEN}✓ GIF generated: $size${NC}"
        else
            echo -e "${RED}ERROR: GIF not found at $gif_file${NC}"
            return 1
        fi
    else
        echo -e "${RED}ERROR: VHS failed${NC}"
        return 1
    fi
}

main() {
    if [ $# -eq 0 ]; then
        echo "Usage: $0 <tape-name> | --all"
        echo ""
        echo "Examples:"
        echo "  $0 skills-showcase"
        echo "  $0 --all"
        exit 1
    fi

    if [ "$1" == "--all" ]; then
        for tape_file in "$TAPE_DIR"/*.tape; do
            if [ -f "$tape_file" ]; then
                echo ""
                validate_tape "$tape_file" && regenerate_gif "$tape_file"
            fi
        done
    else
        local tape_file="$TAPE_DIR/$1.tape"
        if [ ! -f "$tape_file" ]; then
            echo -e "${RED}ERROR: Tape not found: $tape_file${NC}"
            exit 1
        fi
        validate_tape "$tape_file" && regenerate_gif "$tape_file"
    fi

    echo -e "\n${GREEN}Done!${NC}"
}

main "$@"
