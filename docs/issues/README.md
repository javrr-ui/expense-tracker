# Code Smell Issues Documentation

This directory contains detailed documentation for 14 code smells identified in the expense-tracker codebase.

## Quick Start - Creating GitHub Issues

Each file in this directory can be used to create a GitHub issue. Here's how:

### Automated Approach (Recommended)

Use the GitHub CLI to create issues from these files:

```bash
# For each issue file, create a GitHub issue
cd docs/issues

# Example for issue #1
gh issue create --title "Code Smell: Duplicate Month Mapping Dictionaries" \
  --body-file 01-duplicate-month-mappings.md \
  --label "code-quality,refactoring,medium-priority"
```

### Manual Approach

1. Go to https://github.com/javrr-ui/expense-tracker/issues/new
2. Open an issue file (e.g., `01-duplicate-month-mappings.md`)
3. Copy the title (first # heading)
4. Copy the body content
5. Add labels as specified in the file
6. Create the issue

## Issue Priority Summary

### High Priority (Fix Immediately)
- **#8** - Variable Shadowing Bug - Clear typo/bug in amount assignment

### Medium Priority (Address Soon)
- **#1** - Duplicate Month Mappings - 4 files have duplicate code
- **#2** - Duplicate Date Normalization - Same logic in 2 methods
- **#4** - Long Method - 67-line method with multiple responsibilities
- **#9** - Double Session Commit - Performance and atomicity issue
- **#11** - Data Clump - email_message dict used inconsistently
- **#13** - Inconsistent Error Handling - No unified error strategy
- **#14** - Inconsistent Body Selection (includes bug) - Rappi parser has bug

### Low Priority (Nice to Have)
- **#3** - Magic Number - Hardcoded 500 without constant
- **#5** - Feature Envy - Return type too specific
- **#6** - Missing Explicit Return - Implicit None return
- **#7** - Dead Code - PAYPAL defined but not implemented
- **#10** - Logging Bug - category_id logged twice
- **#12** - Class Variable as Instance - Confusing variable declaration

## Quick Wins (Easy Fixes)

These issues are straightforward to fix and would make good first contributions:

1. **#8** - Variable Shadowing (2 lines to fix)
2. **#10** - Logging Bug (1 line to fix)
3. **#3** - Magic Number (add constant)
4. **#6** - Missing Return (add explicit return)

## Related Issues

Some issues should be addressed together:

- **#1 + #2** - Both deal with date/month handling duplication
- **#5 + #6** - Both in the same method (`get_parser_for_email`)
- **#9 + #10** - Both in the same method (`save_transaction`)
- **#11 + #14** - Both deal with email_message structure

## Statistics

- **Total Issues:** 14
- **Bugs:** 4 (High priority: 1, Low priority: 3)
- **Code Duplication:** 2
- **Design Issues:** 5
- **Code Quality:** 3

## Files in This Directory

| File | Title | Priority | Type |
|------|-------|----------|------|
| 01-duplicate-month-mappings.md | Duplicate Month Mapping Dictionaries | Medium | Duplication |
| 02-duplicate-date-normalization.md | Duplicate Date Normalization Logic | Medium | Duplication |
| 03-magic-number-max-results.md | Magic Number (maxResults=500) | Low | Magic Number |
| 04-long-method-parse-credit-card.md | Long Method (_parse_credit_card_purchase) | Medium | Long Method |
| 05-feature-envy-parser-return-type.md | Feature Envy in Parser Return Type | Low | Design |
| 06-missing-explicit-return.md | Missing Explicit Return Statement | Low | Clarity |
| 07-dead-code-paypal.md | Dead Code (PAYPAL Bank Definition) | Low | Dead Code |
| 08-variable-shadowing-bug.md | Variable Shadowing (Duplicate Assignment) | High | Bug |
| 09-double-session-commit.md | Double Session Commit | Medium | Performance |
| 10-logging-bug-duplicate-category.md | Logging Duplicate category_id | Low | Bug |
| 11-data-clump-email-message.md | Data Clump (email_message Dictionary) | Medium | Design |
| 12-class-variable-as-instance.md | Class Variable Used as Instance Variable | Low | Design |
| 13-inconsistent-error-handling.md | Inconsistent Error Handling | Medium | Error Handling |
| 14-inconsistent-body-selection.md | Inconsistent Body Selection Logic | Medium | Bug |

## Creating All Issues at Once

If you want to create all issues at once using the GitHub CLI:

```bash
#!/bin/bash
# create-all-issues.sh

cd docs/issues

# High Priority
gh issue create --title "Bug: Variable Shadowing (Duplicate Assignment)" \
  --body-file 08-variable-shadowing-bug.md \
  --label "bug,high-priority,easy-fix"

# Medium Priority
gh issue create --title "Code Smell: Duplicate Month Mapping Dictionaries" \
  --body-file 01-duplicate-month-mappings.md \
  --label "code-quality,refactoring,medium-priority"

gh issue create --title "Code Smell: Duplicate Date Normalization Logic" \
  --body-file 02-duplicate-date-normalization.md \
  --label "code-quality,refactoring,medium-priority"

gh issue create --title "Code Smell: Long Method (_parse_credit_card_purchase)" \
  --body-file 04-long-method-parse-credit-card.md \
  --label "code-quality,refactoring,medium-priority"

gh issue create --title "Code Smell: Double Session Commit" \
  --body-file 09-double-session-commit.md \
  --label "code-quality,performance,medium-priority,database"

gh issue create --title "Code Smell: Data Clump (email_message Dictionary)" \
  --body-file 11-data-clump-email-message.md \
  --label "code-quality,refactoring,medium-priority,design"

gh issue create --title "Code Smell: Inconsistent Error Handling" \
  --body-file 13-inconsistent-error-handling.md \
  --label "code-quality,refactoring,medium-priority,error-handling"

gh issue create --title "Bug: Inconsistent Body Selection Logic" \
  --body-file 14-inconsistent-body-selection.md \
  --label "bug,code-quality,low-priority"

# Low Priority
gh issue create --title "Code Smell: Magic Number (maxResults=500)" \
  --body-file 03-magic-number-max-results.md \
  --label "code-quality,refactoring,low-priority"

gh issue create --title "Code Smell: Feature Envy in Parser Return Type" \
  --body-file 05-feature-envy-parser-return-type.md \
  --label "code-quality,refactoring,low-priority,design"

gh issue create --title "Code Smell: Missing Explicit Return Statement" \
  --body-file 06-missing-explicit-return.md \
  --label "code-quality,refactoring,low-priority"

gh issue create --title "Code Smell: Dead Code (PAYPAL Bank Definition)" \
  --body-file 07-dead-code-paypal.md \
  --label "code-quality,cleanup,low-priority"

gh issue create --title "Bug: Logging Duplicate category_id" \
  --body-file 10-logging-bug-duplicate-category.md \
  --label "bug,low-priority,easy-fix"

gh issue create --title "Code Smell: Class Variable Used as Instance Variable" \
  --body-file 12-class-variable-as-instance.md \
  --label "code-quality,refactoring,low-priority,design"

echo "All issues created successfully!"
```

Make the script executable and run it:
```bash
chmod +x create-all-issues.sh
./create-all-issues.sh
```

## Contributing

When fixing these issues:

1. **Reference the issue** in your PR description
2. **Add tests** if the fix changes behavior
3. **Run existing tests** to ensure no regressions
4. **Update documentation** if needed
5. **Consider related issues** - some should be fixed together

## Need Help?

If you need clarification on any of these issues or want to discuss the best approach:

1. Comment on the GitHub issue
2. Check the "Related Issues" section in each file
3. Review the "Acceptance Criteria" for specific requirements

---

*Generated: 2026-01-13*  
*Repository: javrr-ui/expense-tracker*  
*For questions, please open a discussion or comment on specific issues*
