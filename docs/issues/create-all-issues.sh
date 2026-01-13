#!/bin/bash
# Script to create all code smell issues in GitHub
# Requires GitHub CLI (gh) to be installed and authenticated

set -e  # Exit on error

echo "=============================================="
echo "Creating Code Smell Issues for Expense Tracker"
echo "=============================================="
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed."
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI."
    echo "Please run: gh auth login"
    exit 1
fi

cd "$(dirname "$0")"

echo "Creating issues in priority order..."
echo ""

# High Priority Issues
echo "📌 Creating HIGH PRIORITY issues..."

gh issue create \
  --title "Bug: Variable Shadowing (Duplicate Assignment)" \
  --body-file 08-variable-shadowing-bug.md \
  --label "bug,high-priority,easy-fix"
echo "✓ Created: Variable Shadowing Bug (#8)"

# Medium Priority Issues
echo ""
echo "📋 Creating MEDIUM PRIORITY issues..."

gh issue create \
  --title "Code Smell: Duplicate Month Mapping Dictionaries" \
  --body-file 01-duplicate-month-mappings.md \
  --label "code-quality,refactoring,medium-priority"
echo "✓ Created: Duplicate Month Mappings (#1)"

gh issue create \
  --title "Code Smell: Duplicate Date Normalization Logic" \
  --body-file 02-duplicate-date-normalization.md \
  --label "code-quality,refactoring,medium-priority"
echo "✓ Created: Duplicate Date Normalization (#2)"

gh issue create \
  --title "Code Smell: Long Method (_parse_credit_card_purchase)" \
  --body-file 04-long-method-parse-credit-card.md \
  --label "code-quality,refactoring,medium-priority"
echo "✓ Created: Long Method (#4)"

gh issue create \
  --title "Code Smell: Double Session Commit" \
  --body-file 09-double-session-commit.md \
  --label "code-quality,performance,medium-priority,database"
echo "✓ Created: Double Session Commit (#9)"

gh issue create \
  --title "Code Smell: Data Clump (email_message Dictionary)" \
  --body-file 11-data-clump-email-message.md \
  --label "code-quality,refactoring,medium-priority,design"
echo "✓ Created: Data Clump (#11)"

gh issue create \
  --title "Code Smell: Inconsistent Error Handling" \
  --body-file 13-inconsistent-error-handling.md \
  --label "code-quality,refactoring,medium-priority,error-handling"
echo "✓ Created: Inconsistent Error Handling (#13)"

gh issue create \
  --title "Bug: Inconsistent Body Selection Logic" \
  --body-file 14-inconsistent-body-selection.md \
  --label "bug,code-quality,medium-priority"
echo "✓ Created: Inconsistent Body Selection (#14)"

# Low Priority Issues
echo ""
echo "📝 Creating LOW PRIORITY issues..."

gh issue create \
  --title "Code Smell: Magic Number (maxResults=500)" \
  --body-file 03-magic-number-max-results.md \
  --label "code-quality,refactoring,low-priority"
echo "✓ Created: Magic Number (#3)"

gh issue create \
  --title "Code Smell: Feature Envy in Parser Return Type" \
  --body-file 05-feature-envy-parser-return-type.md \
  --label "code-quality,refactoring,low-priority,design"
echo "✓ Created: Feature Envy (#5)"

gh issue create \
  --title "Code Smell: Missing Explicit Return Statement" \
  --body-file 06-missing-explicit-return.md \
  --label "code-quality,refactoring,low-priority"
echo "✓ Created: Missing Explicit Return (#6)"

gh issue create \
  --title "Code Smell: Dead Code (PAYPAL Bank Definition)" \
  --body-file 07-dead-code-paypal.md \
  --label "code-quality,cleanup,low-priority"
echo "✓ Created: Dead Code - PAYPAL (#7)"

gh issue create \
  --title "Bug: Logging Duplicate category_id" \
  --body-file 10-logging-bug-duplicate-category.md \
  --label "bug,low-priority,easy-fix"
echo "✓ Created: Logging Bug (#10)"

gh issue create \
  --title "Code Smell: Class Variable Used as Instance Variable" \
  --body-file 12-class-variable-as-instance.md \
  --label "code-quality,refactoring,low-priority,design"
echo "✓ Created: Class Variable as Instance (#12)"

echo ""
echo "=============================================="
echo "✅ All 14 issues created successfully!"
echo "=============================================="
echo ""
echo "Summary:"
echo "  • 1 High Priority bug"
echo "  • 7 Medium Priority issues"
echo "  • 6 Low Priority issues"
echo ""
echo "View all issues at:"
echo "  https://github.com/javrr-ui/expense-tracker/issues"
echo ""
