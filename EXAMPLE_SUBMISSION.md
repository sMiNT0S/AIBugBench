# Example: Adding a Model Submission

This guide shows you exactly how to add an AI model's code responses to the benchmark.

## Step 1: Create Model Directory

**Windows (CMD):**
```cmd
xcopy /E /I submissions\template submissions\claude_opus_4
cd submissions\claude_opus_4
```

**Windows (PowerShell):**
```powershell
Copy-Item -Recurse submissions\template submissions\claude_opus_4
cd submissions\claude_opus_4
```

**macOS/Linux (Bash):**
```bash
cp -r submissions/template submissions/claude_opus_4
cd submissions/claude_opus_4
```

## Step 2: Add Solutions

### For Prompt 1 (prompt_1_solution.py)

Replace the template content with the AI's refactored Python code:

```python
#!/usr/bin/env python3
"""
process_records.py: A script for processing user records from various sources
Refactored by: [Your AI Model Name Here] 🤖
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

**All Platforms:**
```bash
# Go back to project root
cd ../..

# Run benchmark for this specific model
python run_benchmark.py --model claude_opus_4
```

## Expected output

```
Testing model: claude_opus_4
==================================================

Testing Refactoring & Analysis...
   PASSED - Score: 23.00/25 (92.0%)
     └─ Syntax: 5.0/5, Structure: 3.0/3, Execution: 6.0/6
     └─ Quality: 3.0/3, Security: 4.0/4, Performance: 1.5/2, Maintainability: 0.5/2

Testing YAML/JSON Correction...
   PASSED - Score: 25.00/25 (100.0%)
     └─ Syntax: 4.0/4, Structure: 6.0/6, Execution: 8.0/8
     └─ Quality: 6.0/6, Security: 1.0/1, Performance: 0.0/0, Maintainability: 0.0/0

Testing Data Transformation...
   PASSED - Score: 25.00/25 (100.0%)
     └─ Syntax: 3.0/3, Structure: 3.0/3, Execution: 12.0/12
     └─ Quality: 3.0/3, Security: 1.0/1, Performance: 1.0/1, Maintainability: 2.0/2

Testing API Simulation...
   PASSED - Score: 20.50/25 (82.0%)
     └─ Syntax: 2.0/2, Structure: 3.0/3, Execution: 6.0/7
     └─ Quality: 2.5/3, Security: 7.0/7, Performance: 0.0/2, Maintainability: 0.0/1

Final Score: 93.50/100 (93.5%) - Grade: A

Results saved to: results/latest_results.json
Timestamped copy: results/results_20250118_143025.json
Summary report: results/summary_report_20250118_143025.txt
```

**Enhanced feedback features:**
- **Detailed category breakdown**: See exactly where each model excels or struggles
- **7-category analysis**: Security, performance, and maintainability insights
- **Prompt-specific emphasis**: Each prompt shows its unique scoring distribution
- **Actionable feedback**: Specific rationale for each scoring decision

## Tips for Best Results

1. **Copy Exactly**: Copy the AI's code exactly as provided (including imports and structure)
2. **Check Indentation**: Ensure proper Python indentation (4 spaces)
3. **Include All Functions**: Don't forget helper functions if the AI provided them
4. **Test First**: You can test individual files before running the full benchmark

## Testing Individual Files

**All Platforms:**
```bash
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
