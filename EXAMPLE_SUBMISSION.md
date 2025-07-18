# Example: Adding a Model Submission

This guide shows you exactly how to add a model's solutions to the benchmark.

## Step 1: Create Model Directory

```bash
# Copy the template
cp -r submissions/template submissions/claude_opus_4

# Navigate to the new directory
cd submissions/claude_opus_4
```

## Step 2: Add Solutions

### For Prompt 1 (prompt_1_solution.py)

Replace the template content with the AI's refactored code:

```python
#!/usr/bin/env python3
"""
process_records.py: A script for processing user records from various sources
Author: A. Novice Developer (Refactored)
"""

import json
import yaml
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# ... (rest of the refactored code from the AI)
```

### For Prompt 2 (prompt_2_config_fixed.yaml)

Replace with the AI's corrected YAML:

```yaml
# Configuration file for the data processor script
# Contains paths, rules, and feature flags.

use_legacy_paths: true

paths:
  data_source: /srv/data/production/users.json
  legacy_data_source: ./user_data.json
  log_file: /var/log/processor.log

# ... (rest of the corrected YAML)
```

### For Prompt 2 (prompt_2_config.json)

Replace with the AI's JSON conversion:

```json
{
  "use_legacy_paths": true,
  "paths": {
    "data_source": "/srv/data/production/users.json",
    "legacy_data_source": "./user_data.json",
    "log_file": "/var/log/processor.log"
  },
  // ... (rest of the JSON)
}
```

### For Prompt 3 (prompt_3_transform.py)

Replace with the AI's transformation function:

```python
#!/usr/bin/env python3
"""
User data transformation and enrichment module.
"""

import json
import logging
from typing import Dict, List, Any, Optional

def transform_and_enrich_users(user_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform and enrich user records."""
    # ... (AI's implementation)
    
# Optional: main block for testing
if __name__ == "__main__":
    # Test code
    pass
```

### For Prompt 4 (prompt_4_api_sync.py)

Replace with the AI's API sync function:

```python
#!/usr/bin/env python3
"""
CRM Synchronization Module
"""

import json
import requests
from typing import List, Dict, Any, Optional

def sync_users_to_crm(user_data: List[Dict[str, Any]], api_token: str) -> Optional[str]:
    """Synchronize user data with external CRM system."""
    # ... (AI's implementation)
    
# Optional: main block for testing
if __name__ == "__main__":
    # Test code
    pass
```

## Step 3: Run the Benchmark

```bash
# Go back to project root
cd ../..

# Run benchmark for this specific model
python run_benchmark.py --model claude_opus_4
```

## Expected Output

```
🚀 Testing model: claude_opus_4
==================================================

📝 Testing Refactoring & Analysis...
   ✅ PASSED - Score: 23/25
   ✅ Valid Python syntax
   ✅ Good code structure (5/5 best practices)
   ✅ Script runs without errors
   ✅ High code quality

📝 Testing YAML/JSON Correction...
   ✅ PASSED - Score: 25/25
   ✅ Valid YAML syntax
   ✅ All sections preserved
   ✅ Valid JSON syntax
   ✅ All data types corrected

📝 Testing Data Transformation...
   ✅ PASSED - Score: 25/25
   ✅ Transform function found
   ✅ Function runs without crashing
   ✅ All IDs converted to integers
   ✅ Email providers extracted correctly
   ✅ Account tiers calculated correctly

📝 Testing API Simulation...
   ✅ PASSED - Score: 20/25
   ✅ Function signature correct
   ✅ Uses requests library
   ✅ Comprehensive error handling
   ⚠️  API structure issues

🎯 Final Score: 93/100 (93.0%)

💾 Results saved to: results/latest_results.json
💾 Timestamped copy: results/results_20250118_143025.json
📄 Summary report: results/summary_report_20250118_143025.txt
```

## Tips for Best Results

1. **Copy Exactly**: Copy the AI's code exactly as provided (including imports and structure)
2. **Check Indentation**: Ensure proper Python indentation (4 spaces)
3. **Include All Functions**: Don't forget helper functions if the AI provided them
4. **Test First**: You can test individual files before running the full benchmark

## Testing Individual Files

```python
# Test if a Python file has syntax errors
python -m py_compile submissions/claude_opus_4/prompt_1_solution.py

# Test if YAML is valid
python -c "import yaml; yaml.safe_load(open('submissions/claude_opus_4/prompt_2_config_fixed.yaml'))"

# Test if JSON is valid
python -c "import json; json.load(open('submissions/claude_opus_4/prompt_2_config.json'))"
```

## Common Issues and Fixes

### "Function not found" Error

- Make sure the function name matches exactly (e.g., `transform_and_enrich_users`)
- Check that the function is at the module level (not inside a class)

### Low Scores Despite Correct Code

- Ensure all required functionality is implemented
- Check error handling is comprehensive
- Verify data types are correct (not strings where numbers expected)

### YAML/JSON Errors

- Use a YAML validator online to check syntax
- Ensure proper indentation (2 spaces for YAML)
- Check that data types are correct in JSON (true not "true")
