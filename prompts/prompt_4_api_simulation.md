# Prompt 4: API Interaction & Robustness Testing

## Fairness note

• Expect non-strict inputs (minor format deviations, mixed encodings, platform-specific paths).
• Normalize types and handle missing/variant fields gracefully.  
• Avoid network access; keep solutions deterministic and testable.

The business wants to synchronize processed user data with an external CRM system via REST API.

## Task: Create API Sync Function

Write a complete, standalone Python function `sync_users_to_crm(user_data, api_token)` that simulates this integration process with comprehensive error handling.

### Requirements

**Target Endpoint**: `https://api.crm-system.com/v2/users/sync`

**HTTP Method**: POST

**Headers**:

- `Content-Type: application/json`
- `Authorization: Bearer <api_token>`

**Payload**: JSON object with single key `users` containing the user records list

### Error Handling Requirements

Use the `requests` library with comprehensive handling for:

- **Network problems** (`requests.exceptions.ConnectionError`)
- **HTTP status codes**:
  - `401 Unauthorized` (invalid token)
  - `400 Bad Request` (bad data)  
  - `503 Service Unavailable`
  - Generic handling for other 4xx/5xx errors
- **Print informative error messages** for each case

### Success Case

If successful (status 200/202), parse JSON response and return the `job_id` value.

### Function Requirements

- Function must be named exactly `sync_users_to_crm`
- Should handle both valid and invalid scenarios gracefully
- Must follow secure coding practices (no hardcoded credentials)
- Include proper imports and type hints if possible

Your solution should be production-ready with robust error handling that could be used in a real application.
