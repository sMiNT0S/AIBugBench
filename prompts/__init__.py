"""
Prompt definitions for AI Code Benchmark
Contains the standardized prompts used for testing AI models.
"""

# Prompt metadata
PROMPT_METADATA = {
    "prompt_1": {
        "title": "Code Refactoring & Analysis",
        "difficulty": "Medium",
        "focus": ["Code Quality", "Error Handling", "Best Practices"],
        "time_estimate": "15-30 minutes",
    },
    "prompt_2": {
        "title": "YAML/JSON Correction",
        "difficulty": "Easy-Medium",
        "focus": ["Debugging", "Data Formats", "Type Conversion"],
        "time_estimate": "10-20 minutes",
    },
    "prompt_3": {
        "title": "Data Transformation",
        "difficulty": "Medium-Hard",
        "focus": ["Logic Implementation", "Error Handling", "Data Processing"],
        "time_estimate": "20-40 minutes",
    },
    "prompt_4": {
        "title": "API Integration",
        "difficulty": "Medium-Hard",
        "focus": ["API Design", "Error Handling", "Production Code"],
        "time_estimate": "15-30 minutes",
    },
}


def get_prompt_info(prompt_id: str) -> dict:
    """Get metadata for a specific prompt."""
    return PROMPT_METADATA.get(prompt_id, {})


def list_all_prompts() -> list:
    """Get list of all available prompts."""
    return list(PROMPT_METADATA.keys())
