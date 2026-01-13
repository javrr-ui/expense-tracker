#!/bin/bash
# Script to help create GitHub issues from the documented code smells
# 
# This script is meant to be used manually or integrated into CI/CD
# Since the GitHub CLI (gh) is typically available in CI environments,
# you can run this script to create all issues at once.
#
# Prerequisites:
#   - GitHub CLI (gh) installed and authenticated
#   - Run from repository root
#
# Usage:
#   cd .github/ISSUE_TEMPLATE
#   bash create-issues.sh

set -e

ISSUE_DIR="/home/runner/work/expense-tracker/expense-tracker/.github/ISSUE_TEMPLATE"

echo "Creating GitHub issues from documented code smells..."
echo "=================================================="
echo ""

# Function to create an issue from a markdown file
create_issue() {
    local issue_file="$1"
    local issue_name=$(basename "$issue_file" .md)
    
    echo "Processing: $issue_name"
    
    # Extract title from the first heading
    local title=$(grep -m 1 "^# " "$issue_file" | sed 's/^# //')
    
    # Get the content (skip the title)
    local body=$(tail -n +2 "$issue_file")
    
    # Extract labels from the Type field
    local labels="code-quality"
    if grep -q "Type.*Bug" "$issue_file"; then
        labels="bug,code-quality"
    fi
    if grep -q "Duplication" "$issue_file"; then
        labels="$labels,refactoring"
    fi
    if grep -q "Complexity" "$issue_file"; then
        labels="$labels,complexity"
    fi
    
    echo "  Title: $title"
    echo "  Labels: $labels"
    echo ""
    
    # Uncomment to actually create issues (requires gh CLI):
    # gh issue create --title "$title" --body "$body" --label "$labels"
}

# Process all issue files
for issue_file in "$ISSUE_DIR"/issue-*.md; do
    if [ -f "$issue_file" ]; then
        create_issue "$issue_file"
    fi
done

echo "=================================================="
echo "Done! To actually create the issues, uncomment the gh command in the script."
echo ""
echo "Manual creation instructions:"
echo "1. Review each issue-XXX-*.md file in this directory"
echo "2. Copy the content and create a new issue at:"
echo "   https://github.com/javrr-ui/expense-tracker/issues/new"
echo "3. Add appropriate labels (bug, code-quality, refactoring, etc.)"
