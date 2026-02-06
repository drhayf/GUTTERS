# 🎯 PROMPT FOR NEXT AGENT: E501 Line Length Fixes

## Mission Brief
You are tasked with fixing the remaining **490 E501 (line-too-long)** linting errors in the GUTTERS codebase. These are lines exceeding 120 characters, which is a style guideline that improves readability and maintainability.

---

## 🔍 Current State

**Remaining Errors:** 577 total
- **490 E501** (line-too-long) - **YOUR PRIMARY TARGET**
- **87 UP035** (deprecated typing imports) - Lower priority, cosmetic

**Context:** The codebase has already been cleaned of all functional errors:
- ✅ All syntax errors fixed
- ✅ All undefined names fixed
- ✅ All unused variables removed
- ✅ All boolean comparisons corrected
- ✅ All bare excepts fixed
- ✅ All lambda assignments converted

**Your job:** Fix line length violations systematically with surgical precision.

---

## 🎯 Objectives

### Primary Goal
Fix all 490 E501 errors by wrapping long lines to comply with the 120-character limit while:
1. **Preserving exact functionality**
2. **Maintaining code readability**
3. **Following Python style conventions**
4. **Ensuring proper indentation**

### Success Criteria
- ✅ Zero E501 errors remaining
- ✅ All code still executes correctly
- ✅ Improved readability through proper line breaks
- ✅ Consistent formatting throughout

---

## 📋 Strategic Approach

### Step 1: Categorize Errors by Type
Run this to understand distribution:
```powershell
ruff check . --output-format=json | ConvertFrom-Json | Where-Object { $_.code -eq 'E501' } | Group-Object { Split-Path $_.filename -Leaf } | Sort-Object Count -Descending | Select-Object -First 20
```

### Step 2: Prioritize Files
Fix in this order:
1. **User-facing APIs** (src/app/api/v1/*.py)
2. **Core modules** (src/app/modules/intelligence/*.py)
3. **Data constants** (brain/constants.py files)
4. **Test files** (tests/*.py)
5. **Scripts** (scripts/*.py)
6. **Work directory** (work/* - optional, may be temp files)

### Step 3: Apply Fixes Systematically

---

## 🔧 Fixing Techniques

### Technique 1: String Literals
**BEFORE:**
```python
error_message = "This is a very long error message that exceeds the 120 character limit and needs to be broken up into multiple lines"
```

**AFTER:**
```python
error_message = (
    "This is a very long error message that exceeds the 120 character limit "
    "and needs to be broken up into multiple lines"
)
```

---

### Technique 2: Function Calls with Many Arguments
**BEFORE:**
```python
result = some_function(arg1="value1", arg2="value2", arg3="very_long_value", arg4="another_value", arg5="final_value")
```

**AFTER:**
```python
result = some_function(
    arg1="value1",
    arg2="value2",
    arg3="very_long_value",
    arg4="another_value",
    arg5="final_value"
)
```

---

### Technique 3: List/Dict Literals
**BEFORE:**
```python
candidates = dict.fromkeys(["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"], 1 / 12)
```

**AFTER:**
```python
candidates = dict.fromkeys(
    [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ],
    1 / 12
)
```

---

### Technique 4: Long Comprehensions
**BEFORE:**
```python
result = [process_item(x) for x in very_long_collection if x.property == "value" and x.another_property > threshold]
```

**AFTER:**
```python
result = [
    process_item(x)
    for x in very_long_collection
    if x.property == "value" and x.another_property > threshold
]
```

---

### Technique 5: Chained Method Calls
**BEFORE:**
```python
result = data.filter(condition1).map(transform).filter(condition2).sort(key=lambda x: x.value).collect()
```

**AFTER:**
```python
result = (
    data
    .filter(condition1)
    .map(transform)
    .filter(condition2)
    .sort(key=lambda x: x.value)
    .collect()
)
```

---

### Technique 6: Import Statements
**BEFORE:**
```python
from some.very.long.module.path.that.exceeds.limit import FirstClass, SecondClass, ThirdClass, FourthClass
```

**AFTER:**
```python
from some.very.long.module.path.that.exceeds.limit import (
    FirstClass,
    SecondClass,
    ThirdClass,
    FourthClass,
)
```

---

### Technique 7: Logical Expressions
**BEFORE:**
```python
if user.is_authenticated and user.has_permission("admin") and user.profile.is_complete and not user.is_banned:
```

**AFTER:**
```python
if (
    user.is_authenticated
    and user.has_permission("admin")
    and user.profile.is_complete
    and not user.is_banned
):
```

---

### Technique 8: F-Strings and Format Strings
**BEFORE:**
```python
message = f"User {user.name} with ID {user.id} attempted to access resource {resource.name} at {timestamp.isoformat()}"
```

**AFTER:**
```python
message = (
    f"User {user.name} with ID {user.id} attempted to access "
    f"resource {resource.name} at {timestamp.isoformat()}"
)
```

---

## ⚠️ Critical Rules

### DO:
✅ Break at natural semantic boundaries
✅ Keep related parameters together
✅ Align continuation lines consistently
✅ Use parentheses for implicit line continuation (preferred)
✅ Test code after each batch of changes
✅ Preserve all comments and docstrings
✅ Maintain consistent indentation (4 spaces)

### DON'T:
❌ Break mid-word or mid-string unnaturally
❌ Create lines that are too short (aim for 80-120 chars)
❌ Change any logic or functionality
❌ Remove or modify comments
❌ Introduce syntax errors
❌ Mix tabs and spaces
❌ Break URLs or paths unnecessarily

---

## 🚨 High-Risk Areas (Handle with Care)

### 1. Data Constants Files
- **Location:** `src/app/modules/calculation/human_design/brain/constants.py`
- **Issue:** Many lines of dict literals (313-332)
- **Approach:** Group related keys, break at dict boundaries
- **Example:**
```python
# BEFORE:
{"gate": 1, "name": "Very long name here", "RAC": "Right Angle Cross of Something Very Long", "JXP": "Juxtaposition", "LAC": "Left Angle Cross"},

# AFTER:
{
    "gate": 1,
    "name": "Very long name here",
    "RAC": "Right Angle Cross of Something Very Long",
    "JXP": "Juxtaposition",
    "LAC": "Left Angle Cross"
},
```

### 2. Test Assertion Messages
- **Risk:** Breaking test assertion strings can make failures less clear
- **Approach:** Use implicit string concatenation
```python
# AFTER:
assert result == expected, (
    f"Expected {expected} but got {result}. "
    f"Additional context: {debug_info}"
)
```

### 3. Logging Statements
- **Risk:** Log formatting strings are often long
- **Approach:** Break after format markers
```python
# AFTER:
logger.info(
    f"Processing item {item.id} with status {item.status} "
    f"and priority {item.priority}"
)
```

---

## 🔍 Verification Process

After each batch of fixes (recommend 20-30 files at a time):

### 1. Check Error Count
```powershell
ruff check . --statistics | Select-String "E501"
```

### 2. Verify No New Errors
```powershell
ruff check . --statistics | Select-Object -First 5
```

### 3. Spot Check Syntax
```powershell
python -m py_compile path/to/modified/file.py
```

### 4. Run Quick Smoke Test (if available)
```powershell
pytest tests/ -k "test_smoke" --tb=short
```

---

## 📊 Progress Tracking

Use this template to track your work:

```markdown
## E501 Fix Progress

### Batch 1: API Files (20 files)
- [ ] src/app/api/v1/birth_data.py (2 errors)
- [ ] src/app/api/v1/observer.py (4 errors)
- [ ] ...

**Status:** In Progress
**Errors Fixed:** 0/490
**Files Fixed:** 0/XX

### Batch 2: Intelligence Modules
...
```

---

## 🎯 Efficiency Tips

### Use Multi-Replace When Possible
For independent fixes in different files, use:
```python
multi_replace_string_in_file(
    explanation="Fix E501 errors in API files",
    replacements=[
        {fix1}, {fix2}, {fix3}...
    ]
)
```

### Pattern Recognition
- Many errors in same file? Likely similar patterns
- Group fixes by pattern type (strings, imports, function calls)
- Create templates for common patterns

### Avoid Over-Engineering
- If a line is 125 chars, simple fixes are fine
- Don't over-optimize 121-char lines into 5 lines
- Balance readability with line length

---

## 📝 Example Workflow

```python
# 1. Identify errors in file
ruff check src/app/api/v1/birth_data.py

# 2. Read the problematic lines
read_file(file, startLine=125, endLine=135)

# 3. Apply fix
replace_string_in_file(
    oldString="...",  # Include context!
    newString="..."   # Fixed version
)

# 4. Verify
ruff check src/app/api/v1/birth_data.py
```

---

## 🚀 Starting Point

Begin with these known high-concentration files:

1. **src/app/modules/calculation/human_design/brain/constants.py** (~20 errors)
   - Dict literals with long strings
   - Pattern: Break at dict boundaries

2. **src/app/api/v1/observer.py** (~4 errors)
   - Function calls and logging

3. **src/app/core/state/chronos.py** (~3 errors)
   - Complex logic chains

4. **Work through remaining files alphabetically within each category**

---

## ⏱️ Time Estimates

- **API files (50 errors):** ~30-45 minutes
- **Intelligence modules (200 errors):** ~2-3 hours
- **Constants files (150 errors):** ~1-2 hours
- **Test files (50 errors):** ~30-45 minutes
- **Scripts & misc (40 errors):** ~30 minutes

**Total Estimated Time:** 5-7 hours of focused work

---

## 🎓 Quality Standards

### Good Fix Example:
```python
# BEFORE (135 chars):
result = calculate_something(parameter1, parameter2, parameter3, very_long_parameter4="value", another_parameter="another_value")

# AFTER:
result = calculate_something(
    parameter1,
    parameter2,
    parameter3,
    very_long_parameter4="value",
    another_parameter="another_value"
)
```

### Poor Fix Example (Don't Do This):
```python
# AVOID - Too fragmented:
result = calculate_something(
    parameter1, parameter2,
    parameter3,
    very_long_parameter4="value",
    another_parameter=
    "another_value"  # ❌ Unnatural break
)
```

---

## 🔐 Final Checklist Before Completion

- [ ] All 490 E501 errors resolved
- [ ] No new errors introduced
- [ ] Code still runs (test at least one module)
- [ ] Formatting is consistent
- [ ] Git diff is reviewable (logical chunks)
- [ ] All syntax valid (no stray commas, parens)

---

## 📞 Support Resources

- **PEP 8 Style Guide:** https://pep8.org/#maximum-line-length
- **Black Formatter:** (for inspiration on breaking styles)
- **Ruff Docs:** https://docs.astral.sh/ruff/rules/line-too-long/

---

## 🎯 Success Definition

**You will know you're done when:**
```powershell
ruff check . --statistics
```

Returns:
```
87     UP035   deprecated-import
Found 87 errors.
```

And **ZERO E501 errors**.

---

**Agent Instructions:**
1. Work systematically through files
2. Use multi_replace when possible
3. Test periodically
4. Document any challenges
5. Focus on readability, not just compliance
6. **Be surgical - preserve all functionality**

**Good luck! You've got this! 🚀**

---

**Prepared by:** Previous Agent (Surgical Error Fixer)
**For:** Next Agent (Line Length Specialist)
**Date:** February 6, 2026
**Confidence:** All foundational work is solid - this is pure style cleanup
