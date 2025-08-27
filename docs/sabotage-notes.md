# Sabotage Notes: Deliberate Issues Added to AIBugBench

## Overview

This document catalogs the realistic edge cases and coding pitfalls intentionally introduced to enhance AIBugBench difficulty while maintaining solvability. Each modification reflects real-world QA scenarios and tests AI models' ability to handle inconsistent, legacy, or problematic input data.

**Design Principles**:

- Every hazard has a realistic origin story from production systems
- All issues remain solvable through defensive programming practices
- Success paths are preserved to ensure benchmark remains achievable
- Edge cases increase difficulty without changing core requirements

## File-by-File Hazard Catalog

### test_data/process_records.py

**Hazards Introduced**:

1. **Builtin Shadowing** (`list = []`)
   - **What**: Shadows Python's built-in `list` type but never uses the variable
   - **Real-world Context**: Legacy code accumulates unused variables that shadow builtins
   - **Impact**: Can confuse code analysis, potential runtime issues if variable used
   - **Solution**: Remove unused variable or rename to non-conflicting name

2. **Mixed Import Patterns** (`from datetime import datetime as dt` + `import datetime`)
   - **What**: Both `dt` and `datetime` available, creating potential confusion
   - **Real-world Context**: Multiple developers adding imports over time
   - **Impact**: Code readability issues, potential for using wrong reference
   - **Solution**: Standardize on single import pattern throughout module

3. **Exception Masking with NameError Risk**
   - **What**: Broad `except Exception: pass` creates undefined variable scenarios
   - **Real-world Context**: Quick fixes that hide real problems
   - **Impact**: Silent failures, potential NameError when accessing undefined variables
   - **Solution**: Specific exception handling with proper error recovery

4. **Unsafe YAML Loading** (`yaml.load()` without Loader)
   - **What**: Uses deprecated unsafe YAML loading method
   - **Real-world Context**: Legacy code before security best practices
   - **Impact**: Security vulnerability, deprecation warnings
   - **Solution**: Use `yaml.safe_load()` or specify `Loader=yaml.SafeLoader`

5. **Mixed Date Format Support with Naive Datetime**
   - **What**: Supports multiple date formats but uses naive datetime operations
   - **Real-world Context**: Systems integrating data from multiple sources
   - **Impact**: Timezone issues, format parsing failures
   - **Solution**: Timezone-aware datetime handling, robust format validation

6. **Misleading Parameter Names**
   - **What**: Hardcoded values passed to parameters with names suggesting flexibility
   - **Real-world Context**: Technical debt where interfaces evolved but implementations didn't
   - **Impact**: Maintenance confusion, false expectations about configurability
   - **Solution**: Either make parameters truly configurable or rename to reflect reality

### test_data/user_data.json

**Hazards Introduced**:

1. **JSON Syntax Violations**
   - **Trailing Commas**: After final array/object elements
   - **JavaScript Comments**: `//` and `/* */` style comments
   - **Duplicate Keys**: Same key appears multiple times (last value wins)
   - **Real-world Context**: JSON exports from systems with relaxed parsing
   - **Impact**: Parsing errors in strict JSON parsers
   - **Solution**: JSON preprocessing to remove comments and trailing commas

2. **Data Type Inconsistencies**
   - **String NaN**: Age field as `"NaN"` string instead of null
   - **Leading Zeros**: Numbers as strings with leading zeros (`"0004"`)
   - **Mixed Number Types**: Ages as strings, integers, and floats
   - **Real-world Context**: Data exports from different database systems
   - **Impact**: Type coercion issues, invalid calculations
   - **Solution**: Robust type normalization and validation

3. **Unicode Edge Cases**
   - **Zero-Width Spaces**: Invisible characters in names (U+200B)
   - **Combining Diacritics**: Characters composed of multiple Unicode code points
   - **BOM Characters**: Byte Order Mark at file start
   - **Real-world Context**: Data from international systems, copy-paste errors
   - **Impact**: Display issues, string comparison failures, encoding problems
   - **Solution**: Unicode normalization, BOM stripping, proper encoding handling

4. **Structure Variations**
   - **Contact Field Types**: String vs object vs array across users
   - **Missing Required Fields**: Some users lack expected properties
   - **Nested Object Depth**: Inconsistent nesting levels
   - **Real-world Context**: API evolution, optional field handling
   - **Impact**: Field access errors, type assumption failures
   - **Solution**: Defensive field access, type checking, schema validation

**Success Path Preservation**:
Users 101, 105, and one additional clean record maintain perfect structure for successful processing:

- Consistent data types
- All required fields present  
- Standard JSON formatting
- No Unicode complications

### test_data/config.yaml

**Hazards Introduced**:

1. **Multi-Document YAML Structure**
   - **What**: Two YAML documents with conflicting values
   - **Real-world Context**: Configuration file evolution, different environment configs
   - **Impact**: Parser confusion, value precedence issues
   - **Solution**: Multi-document aware parsing with merge strategies

2. **Mixed Boolean Representations**
   - **Document 1**: Native YAML booleans (`yes`, `true`, `false`)
   - **Document 2**: String booleans (`"true"`, `"false"`, `"1"`, `"off"`)
   - **Real-world Context**: Different systems writing to same config file
   - **Impact**: Boolean evaluation inconsistencies
   - **Solution**: Normalize boolean values during parsing

3. **Type System Chaos**
   - **Numbers as Strings**: `"021"`, `"05"`, `"60.00"`
   - **Leading Zeros**: String numbers with leading zeros
   - **Decimal Strings**: Integers represented as decimal strings
   - **Real-world Context**: Form inputs, environment variable substitution
   - **Impact**: Numeric comparison failures, type conversion issues
   - **Solution**: Type coercion with validation

4. **Path Format Mixing**
   - **Environment Variables**: `$HOME/data`, `~/logs`
   - **Platform Mixing**: Windows (`C:\`) and Unix (`/tmp`) paths
   - **Relative vs Absolute**: Mixed path resolution strategies
   - **Real-world Context**: Cross-platform deployment, different developers
   - **Impact**: Path resolution failures, file not found errors
   - **Solution**: Platform-aware path handling, environment variable expansion

5. **Indentation Chaos**
   - **Mixed Tabs/Spaces**: Within single document
   - **Inconsistent Levels**: Varying indentation amounts
   - **Real-world Context**: Different editors, copy-paste operations
   - **Impact**: YAML parsing errors, structure misinterpretation
   - **Solution**: Indentation normalization, YAML validation

6. **YAML Advanced Features**
   - **Anchors and Aliases**: `&default_paths` and `*default_paths`
   - **Multi-line Strings**: Various YAML string representations
   - **Real-world Context**: DRY principle application, complex configurations
   - **Impact**: Reference resolution issues, parser compatibility
   - **Solution**: YAML feature-aware parsing

**Success Path Preservation**:
Document 2 contains working path: `"./user_data.json"` pointing to actual file
Essential configuration values remain accessible through proper multi-document parsing

## Solution Pattern Library (Comments added to explain 'expected' behavior)

### Pattern 1: Safe File Reading with Encoding Handling

```python
def safe_json_load(file_path):
    with open(file_path, encoding='utf-8-sig') as f:
        content = f.read()
        # Strip BOM if present
        content = content.strip('\ufeff')
        # Remove JavaScript-style comments (simple approach)
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # Remove trailing commas (simplified)
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        return json.loads(content)
```

### Pattern 2: Type Normalization

```python
def normalize_age(age_value):
    if age_value is None:
        return 0
    if isinstance(age_value, (int, float)):
        return int(age_value)
    if isinstance(age_value, str):
        if age_value.lower() in ('nan', 'null', ''):
            return 0
        # Handle leading zeros
        try:
            return int(float(age_value))  # Handle "21.0" -> 21
        except ValueError:
            return 0
    return 0
```

### Pattern 3: Multi-Document YAML Handling

```python
def load_config_safe(config_path):
    with open(config_path) as f:
        documents = list(yaml.safe_load_all(f))
    
    # Merge documents with precedence (last wins)
    config = {}
    for doc in documents:
        if doc:  # Skip None documents
            config.update(doc)
    
    return config
```

### Pattern 4: Unicode Normalization

```python
import unicodedata

def normalize_text(text):
    if not isinstance(text, str):
        return text
    
    # Remove zero-width characters
    text = ''.join(char for char in text if unicodedata.category(char) != 'Cf')
    
    # Normalize Unicode (NFC form)
    text = unicodedata.normalize('NFC', text)
    
    return text.strip()
```

### Pattern 5: Defensive Field Access

```python
def safe_get_nested(data, path, default=None):
    """Safely get nested dictionary values with dot notation"""
    keys = path.split('.')
    current = data
    
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    
    return current

# Usage: email = safe_get_nested(user, 'contact.email', '')
```

## Testing and Validation

### Manual Verification Steps

1. **File Parsing Tests**:

   ```python
   # Test JSON with comments and trailing commas
   import json
   with open('user_data.json', encoding='utf-8-sig') as f:
       raw = f.read()
       # Should fail with standard json.loads()
       # Should succeed with preprocessing
   
   # Test multi-document YAML
   import yaml
   with open('config.yaml') as f:
       docs = list(yaml.safe_load_all(f))
       assert len(docs) == 2
   ```

2. **Unicode Handling Tests**:

   ```python
   # Test zero-width space detection
   name = "Jane​Doe"  # Contains U+200B
   assert len(name) > len("JaneDoe")  # Should detect extra character
   
   # Test combining diacritics  
   muller1 = "Müller"        # Precomposed
   muller2 = "Mu\u0308ller" # Combining diacritic
   assert muller1 != muller2  # Different representations
   ```

3. **Type Coercion Tests**:

   ```python
   # Test string number handling
   assert int("0004") == 4      # Leading zeros
   assert float("21.00") == 21.0 # Decimal strings
   
   # Test NaN handling
   try:
       int("NaN")  # Should raise ValueError
   except ValueError:
       pass  # Expected
   ```

### Automated Testing Framework

```python
def test_enhanced_benchmark():
    """Test that enhanced files maintain solvability"""
    
    # Test 1: JSON parsing with preprocessing succeeds
    users = load_users_safe('test_data/user_data.json')
    assert len(users) >= 3  # At least 3 clean users
    
    # Test 2: YAML multi-document parsing succeeds  
    config = load_config_safe('test_data/config.yaml')
    assert 'validation_rules' in config
    
    # Test 3: Core business logic executable
    processor = SafeProcessor(config)
    results = processor.process_all_records()
    assert len(results) > 0  # Some records processed successfully
    
    # Test 4: Score achievability
    score = validate_solution_quality(results)
    assert score >= 18  # Minimum achievable with good solution
```

## Troubleshooting Guide

### Common Issues and Solutions

**Issue**: JSON parsing fails with syntax error
**Cause**: JavaScript comments or trailing commas
**Solution**: Preprocess JSON to remove comments and trailing commas

**Issue**: YAML parsing returns unexpected values  
**Cause**: Multi-document structure, only first document loaded
**Solution**: Use `yaml.safe_load_all()` and merge documents appropriately

**Issue**: Unicode characters display incorrectly
**Cause**: Zero-width spaces, combining diacritics, encoding issues
**Solution**: Unicode normalization and BOM stripping

**Issue**: Type conversion errors on numeric strings
**Cause**: Leading zeros, decimal representations, "NaN" values
**Solution**: Robust type coercion with fallback values

**Issue**: File path resolution failures
**Cause**: Environment variables, platform-specific paths
**Solution**: Path expansion and platform-aware handling

### Performance Considerations

**Impact**: Enhanced files may require additional processing
**Mitigation**:

- Cache preprocessing results
- Use efficient regex patterns
- Minimize file I/O operations
- Consider lazy loading for large datasets

**Benchmarking**: Enhanced benchmark ~10-15% slower due to:

- JSON preprocessing overhead
- Multi-document YAML parsing
- Unicode normalization
- Type coercion operations

## Real-World Context and Educational Value

### Why These Issues Exist

**Legacy System Integration**: Different systems export data in incompatible formats
**Multi-Developer Codebases**: Inconsistent coding standards accumulate over time  
**Copy-Paste Programming**: Code fragments copied without understanding context
**Evolving Requirements**: Systems modified without updating related components
**Platform Differences**: Windows/Unix path handling, encoding variations
**Internationalization**: Unicode complexity, character encoding issues

### Educational Outcomes

**Defensive Programming**: Students learn to validate and sanitize inputs
**Error Handling**: Proper exception handling becomes critical for success
**Type Safety**: Dynamic typing pitfalls become apparent
**Configuration Management**: Complex config handling strategies required  
**Unicode Awareness**: International character set considerations
**Security Consciousness**: Unsafe YAML loading demonstrates security implications

### Professional Relevance  

These enhancements mirror real-world scenarios QA engineers encounter:

- Data migration projects with inconsistent source formats
- Legacy code maintenance with accumulated technical debt
- Integration testing across different systems and platforms
- International deployment with Unicode complexity
- Security auditing of configuration and data loading practices

## Conclusion

The AIBugBench difficulty enhancement introduces realistic complexity that mirrors production QA scenarios while maintaining clear solution paths for thorough implementations. Each hazard serves educational purposes and tests practical skills essential for professional software quality assurance.

Success requires:

- Careful input validation and sanitization
- Robust error handling and recovery
- Type safety awareness and normalization
- Unicode and encoding best practices  
- Configuration complexity management
- Security-conscious programming practices

These skills directly transfer to real-world QA engineering challenges, making the enhanced benchmark a more valuable assessment tool for AI model capabilities in practical software quality scenarios.
