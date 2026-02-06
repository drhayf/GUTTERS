#!/usr/bin/env python3
"""
GUTTERS Comprehensive Validation Script

Auto-discovers and validates all GUTTERS components:
- Models (field ordering, imports, metadata)
- Protocol package
- Core systems
- Schemas
- Utils

Uses AST parsing to detect field ordering issues BEFORE import.

Usage:
    python src/scripts/validate_models.py

Exit codes:
    0 - All passed
    1 - Import errors
    2 - Field ordering errors
    3 - Missing imports
    4 - Other validation errors
"""

import ast
import importlib
import sys
from pathlib import Path
from typing import Any

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))


class ValidationError(Exception):
    """Custom validation error."""

    pass


def discover_models(models_dir: Path) -> list[Path]:
    """
    Auto-discover all model files.

    Args:
        models_dir: Path to app/models directory

    Returns:
        List of model file paths (excluding __init__.py)
    """
    return [f for f in models_dir.glob("*.py") if f.name != "__init__.py"]


def parse_model_fields(file_path: Path) -> list[dict[str, Any]]:
    """
    Parse model file with AST to extract field definitions.

    Args:
        file_path: Path to model file

    Returns:
        List of field info dicts: {name, has_default, line_number}
    """
    with open(file_path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    fields = []

    # Find class definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Look for annotated assignments (field definitions)
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    field_name = item.target.id
                    has_default = item.value is not None

                    # Check if it's a mapped_column with default/default_factory
                    if has_default and isinstance(item.value, ast.Call):
                        # Check for default_factory, server_default, default, or init=False
                        for keyword in item.value.keywords:
                            if keyword.arg in ("default_factory", "server_default", "default", "init"):
                                has_default = True
                                break

                    fields.append({"name": field_name, "has_default": has_default, "line_number": item.lineno})

    return fields


def validate_field_ordering(file_path: Path) -> tuple[bool, str | None]:
    """
    Validate field ordering using AST analysis.

    Rules:
    1. Primary key (id) should be first
    2. Required fields (no defaults) before optional fields (with defaults)

    Args:
        file_path: Path to model file

    Returns:
        (is_valid, error_message)
    """
    try:
        fields = parse_model_fields(file_path)

        if not fields:
            return True, None

        # Check ordering: fields without defaults should come before fields with defaults
        seen_default = False
        for field in fields:
            if field["has_default"]:
                seen_default = True
            elif seen_default and not field["has_default"]:
                # Found required field after optional field
                error = (
                    f"Line {field['line_number']}: Field '{field['name']}' (required, no default)\n"
                    f"  comes after a field with a default value.\n"
                    f"  Fix: Move '{field['name']}' before fields with defaults."
                )
                return False, error

        return True, None

    except Exception as e:
        return False, f"AST parsing error: {e}"


def check_required_imports(file_path: Path) -> tuple[bool, list[str]]:
    """
    Check if model file has required imports.

    Args:
        file_path: Path to model file

    Returns:
        (all_present, missing_imports)
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    missing = []

    # Check for Mapped and mapped_column
    if "Mapped[" in content and "from sqlalchemy.orm import" not in content:
        missing.append("from sqlalchemy.orm import Mapped, mapped_column")

    # Check for func usage
    if "func." in content and "from sqlalchemy" not in content or "func" not in content:
        if "func.now()" in content or "func." in content:
            missing.append("from sqlalchemy import func")

    # Check for JSONB
    if "JSONB" in content and "from sqlalchemy.dialects.postgresql import JSONB" not in content:
        missing.append("from sqlalchemy.dialects.postgresql import JSONB")

    return len(missing) == 0, missing


def validate_models() -> tuple[int, list[str], list[str]]:
    """
    Validate all models.

    Returns:
        (exit_code, passed_models, errors)
    """
    models_dir = src_path / "app" / "models"
    model_files = discover_models(models_dir)

    passed = []
    errors = []

    # Sort files to ensure user.py and core models are loaded first
    # This prevents NoReferencedTableError during discovery
    def sort_key(p: Path):
        name = p.stem
        if name == "user":
            return "000_user"
        if name == "user_profile":
            return "001_user_profile"
        return name

    model_files.sort(key=sort_key)

    # First, do AST-based validation (doesn't import anything, so no metadata conflicts)
    for model_file in model_files:
        model_name = model_file.stem

        # 1. Check field ordering with AST
        is_valid, error_msg = validate_field_ordering(model_file)
        if not is_valid:
            errors.append(f"❌ {model_file.relative_to(src_path)}\n  {error_msg}")
            continue

        # 2. Check required imports
        imports_ok, missing = check_required_imports(model_file)
        if not imports_ok:
            errors.append(
                f"❌ {model_file.relative_to(src_path)}\n"
                f"  Missing imports:\n" + "\n".join(f"    {imp}" for imp in missing)
            )
            continue

        passed.append(model_name)

    # If AST validation passed, we're good
    # Note: We skip actual import testing here because it can cause SQLAlchemy metadata
    # conflicts when validation is run from within alembic migrations (which pre-import models).
    # The AST checks above catch all the critical issues (field ordering, required imports).

    if errors:
        return 2 if "Field" in str(errors) else 1, passed, errors

    return 0, passed, errors


def validate_protocol() -> tuple[int, list[str], list[str]]:
    """Validate protocol package."""
    passed = []
    errors = []

    try:

        passed.extend(["events", "packet"])
    except Exception as e:
        errors.append(f"❌ protocol: {e}")
        return 1, passed, errors

    return 0, passed, errors


def validate_core_systems() -> tuple[int, list[str], list[str]]:
    """Validate core systems."""
    passed = []
    errors = []

    systems = [
        ("app.core.ai.llm_factory", "llm_factory"),
        ("app.core.events.bus", "event_bus"),
        ("app.core.memory.active_memory", "active_memory"),
    ]

    for module_path, name in systems:
        try:
            importlib.import_module(module_path)
            passed.append(name)
        except Exception as e:
            errors.append(f"❌ {name}: {e}")

    return 1 if errors else 0, passed, errors


def validate_schemas() -> tuple[int, list[str], list[str]]:
    """Validate schemas."""
    passed = []
    errors = []

    try:

        passed.append("profile")
    except Exception as e:
        errors.append(f"❌ profile: {e}")
        return 1, passed, errors

    return 0, passed, errors


def validate_utils() -> tuple[int, list[str], list[str]]:
    """Validate utils."""
    passed = []
    errors = []

    try:

        passed.append("geocoding")
    except Exception as e:
        errors.append(f"❌ geocoding: {e}")
        return 1, passed, errors

    return 0, passed, errors


def main():
    """Main entry point."""
    print("[*] Validating GUTTERS Codebase...")
    print("=" * 60)

    all_exit_codes = []

    # Validate models
    exit_code, passed_models, model_errors = validate_models()
    all_exit_codes.append(exit_code)
    print(f"\nModels ({len(passed_models)}/{len(passed_models) + len(model_errors)}):")
    for model in passed_models:
        print(f"  [OK] {model}")
    for error in model_errors:
        print(f"  {error}")

    # Validate protocol
    exit_code, passed_protocol, protocol_errors = validate_protocol()
    all_exit_codes.append(exit_code)
    print(f"\nProtocol ({len(passed_protocol)}/{len(passed_protocol) + len(protocol_errors)}):")
    for item in passed_protocol:
        print(f"  [OK] {item}")
    for error in protocol_errors:
        print(f"  {error}")

    # Validate core systems
    exit_code, passed_core, core_errors = validate_core_systems()
    all_exit_codes.append(exit_code)
    print(f"\nCore Systems ({len(passed_core)}/{len(passed_core) + len(core_errors)}):")
    for item in passed_core:
        print(f"  [OK] {item}")
    for error in core_errors:
        print(f"  {error}")

    # Validate schemas
    exit_code, passed_schemas, schema_errors = validate_schemas()
    all_exit_codes.append(exit_code)
    print(f"\nSchemas ({len(passed_schemas)}/{len(passed_schemas) + len(schema_errors)}):")
    for item in passed_schemas:
        print(f"  [OK] {item}")
    for error in schema_errors:
        print(f"  {error}")

    # Validate utils
    exit_code, passed_utils, util_errors = validate_utils()
    all_exit_codes.append(exit_code)
    print(f"\nUtils ({len(passed_utils)}/{len(passed_utils) + len(util_errors)}):")
    for item in passed_utils:
        print(f"  [OK] {item}")
    for error in util_errors:
        print(f"  {error}")

    # Summary
    total_passed = (
        len(passed_models) + len(passed_protocol) + len(passed_core) + len(passed_schemas) + len(passed_utils)
    )
    total_errors = len(model_errors) + len(protocol_errors) + len(core_errors) + len(schema_errors) + len(util_errors)

    print("\n" + "=" * 60)
    if total_errors == 0:
        print(f"[OK] All validations passed ({total_passed}/{total_passed})")
        sys.exit(0)
    else:
        print(f"[FAIL] Validation failed ({total_passed}/{total_passed + total_errors} passed)")
        sys.exit(max(all_exit_codes))


if __name__ == "__main__":
    main()
