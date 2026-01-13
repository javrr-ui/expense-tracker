# Code Smell: Magic Number (maxResults=500)

**Labels:** `code-quality`, `refactoring`, `low-priority`  
**Type:** Magic Number

## Description

The Gmail API call in `fetch_emails.py` uses a hardcoded value `maxResults=500` without explanation or named constant.

## Location

- `core/fetch_emails.py` (line 23)

## Current Code

```python
response = (
    service.users()
    .messages()
    .list(userId="me", q=query, maxResults=500, pageToken=page_token)
    .execute()
)
```

## Impact

- **Unclear Intent:** Why 500? Is it the API limit? Performance tuning?
- **Maintainability:** Harder to adjust if Gmail API limits change
- **Not Configurable:** Cannot be changed without code modification
- **Documentation:** No comment explaining the choice

## Proposed Solution

Define as a named constant at the module level with documentation:

```python
# Gmail API allows up to 500 messages per page
# Using maximum to minimize API calls
MAX_MESSAGES_PER_PAGE = 500

def list_messages(service, query: str = " ", page_token: str | None = None):
    """Yield all message metadata matching the query, handling pagination automatically."""
    while True:
        response = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=MAX_MESSAGES_PER_PAGE, pageToken=page_token)
            .execute()
        )
        # ... rest of code
```

Or make it configurable:

```python
DEFAULT_PAGE_SIZE = 500

def list_messages(
    service, 
    query: str = " ", 
    page_token: str | None = None,
    page_size: int = DEFAULT_PAGE_SIZE
):
    """
    Yield all message metadata matching the query, handling pagination automatically.
    
    Args:
        service: Authenticated Gmail API service
        query: Gmail search query
        page_token: Pagination token for continuing previous search
        page_size: Number of messages per page (default: 500, max: 500)
    """
    if page_size > 500:
        logger.warning("Gmail API maximum is 500 messages per page, using 500")
        page_size = 500
        
    # ... rest of code with maxResults=page_size
```

## Acceptance Criteria

- [ ] Define `MAX_MESSAGES_PER_PAGE` constant at module level
- [ ] Add comment explaining the value (Gmail API limit)
- [ ] Replace magic number with named constant
- [ ] Consider making it a parameter for testing flexibility
- [ ] Update any related documentation

## Additional Notes

According to [Gmail API documentation](https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list), the maximum value for `maxResults` is 500, so this is already using the optimal value. The issue is purely about code clarity and maintainability.
