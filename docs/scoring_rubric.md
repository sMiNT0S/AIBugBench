# Scoring Rubric - AI Code Benchmark

## Overview

Each prompt is worth 25 points, for a total of 100 points. The passing threshold is 60% (15/25 points per prompt).

## Prompt 1: Code Refactoring & Analysis (25 points)

### Code Quality Improvements (10 points)

- **Error Handling (2 points)**: Added try-except blocks, proper exception handling
- **Context Managers (2 points)**: Using `with` statements for file operations
- **Type Hints (2 points)**: Added function and variable type annotations
- **String Formatting (2 points)**: Modern f-strings or .format() usage
- **Import Organization (2 points)**: Clean, organized imports at top of file

### Execution Success (10 points)

- **Runs Without Errors (10 points)**: Script executes completely without crashing
- **Partial Credit (5 points)**: Script runs with minor issues or warnings

### Output Correctness (5 points)

- **Correct Output Format (5 points)**: Produces expected JSON output with USA users
- **Partial Credit (2-3 points)**: Output mostly correct but with minor formatting issues

## Prompt 2: YAML/JSON Correction (25 points)

### YAML Parsing (10 points)

- **Valid Syntax (10 points)**: YAML file loads without any parsing errors
- **Partial Credit (5 points)**: YAML loads but has structural issues

### YAML Structure (5 points)

- **All Sections Present (5 points)**: All original config sections preserved and correctly formatted
- **Partial Credit (2-3 points)**: Most sections correct, minor issues

### JSON Parsing (5 points)

- **Valid JSON (5 points)**: JSON file is syntactically correct
- **Partial Credit (2-3 points)**: Minor JSON formatting issues

### Data Type Conversion (5 points)

- **Correct Types (5 points)**: Booleans are boolean, numbers are numeric, strings remain strings
- **Partial Credit (2-3 points)**: Most types converted correctly

## Prompt 3: Data Transformation (25 points)

### Function Execution (5 points)

- **No Crashes (5 points)**: Function executes without throwing exceptions
- **Handles Edge Cases (bonus)**: Gracefully handles null/missing data

### ID Standardization (5 points)

- **All IDs Integers (5 points)**: All user IDs converted to int type
- **Partial Credit (2-3 points)**: Most IDs converted correctly

### Email Provider Extraction (5 points)

- **Correct Extraction (5 points)**: Email domain extracted and added as email_provider
- **Error Handling (bonus)**: Properly handles null emails without crashing

### Account Tier Logic (5 points)

- **Correct Logic (5 points)**: Gold/Silver/Bronze assigned according to exact rules
- **Partial Credit (2-4 points)**: Logic mostly correct but minor errors

### Age Type Correction (5 points)

- **All Ages Integers (5 points)**: String ages converted to int type
- **Partial Credit (2-3 points)**: Most ages converted correctly

## Prompt 4: API Simulation (25 points)

### Function Structure (5 points)

- **Correct Function Name (5 points)**: Function named exactly `sync_users_to_crm`
- **Correct Parameters (bonus)**: Takes user_data and api_token parameters

### Library Usage (3 points)

- **Imports Requests (3 points)**: Uses requests library for HTTP calls

### API Configuration (4 points)

- **Correct Endpoint (2 points)**: Uses exact API URL provided
- **POST Method (2 points)**: Uses POST HTTP method

### Headers (4 points)

- **Content-Type (2 points)**: Sets application/json content type
- **Authorization (2 points)**: Sets Bearer token authorization header

### Error Handling (9 points)

- **Connection Errors (3 points)**: Handles requests.exceptions.ConnectionError
- **HTTP Status Codes (3 points)**: Handles 401, 400, 503 status codes specifically
- **Generic Error Handling (3 points)**: Has try-except blocks for unexpected errors

## Grade Scale

| Percentage | Letter Grade | Description |
|------------|--------------|-------------|
| 90-100%    | A           | Excellent - Production ready code |
| 80-89%     | B           | Good - Minor improvements needed |
| 70-79%     | C           | Satisfactory - Some issues to address |
| 60-69%     | D           | Minimal - Significant improvements needed |
| 0-59%      | F           | Fail - Major issues or non-functional |

## Bonus Points

Models can earn bonus points for:

- Exceptional error handling
- Clean, documented code
- Performance optimizations
- Security considerations
- Advanced Python features used appropriately
