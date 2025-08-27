# Prompt 2: Error Explanation and Multi-Format Conversion ↔️

## Fairness note

• Expect non-strict inputs (minor format deviations, mixed encodings, platform-specific paths).
• Normalize types and handle missing/variant fields gracefully.  
• Avoid network access; keep solutions deterministic and testable.

The original process_records.py script will fail when trying to load config.yaml.

    Explain the Errors: Pinpoint the exact lines and reasons why the yaml.load() call will raise errors based on the content of config.yaml. Be specific about indentation and structural issues.

    Correct the YAML: Provide a fully corrected version of config.yaml that resolves all parsing issues while preserving the intended data structure. Use safe loading practices.

    Convert to JSON: Convert the corrected YAML content into a properly formatted JSON object. Ensure all data types (booleans, numbers, strings) are represented correctly in the JSON output.
