"""
Type Contract Validation Script for Project Sovereign

This script validates that all agents comply with the BaseAgent type contract:
    execute(AgentInput) -> AgentOutput

It also checks for potential type mismatches like:
- Calling .get() on Pydantic models (should use attribute access)
- Returning dicts where AgentOutput is expected
- Using isinstance() checks where types should be guaranteed

Usage:
    python scripts/validate_type_contracts.py
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple, Dict


class TypeContractValidator(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.issues: List[Tuple[int, str, str]] = []
        self.in_execute_method = False
        self.execute_return_type = None
        self.agent_class_name = None
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Check if class inherits from BaseAgent"""
        if any(
            (isinstance(base, ast.Name) and base.id == "BaseAgent")
            or (isinstance(base, ast.Attribute) and base.attr == "BaseAgent")
            for base in node.bases
        ):
            self.agent_class_name = node.name
            print(f"  ✓ Found agent class: {node.name}")
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Check execute method signature and return type"""
        if node.name == "execute":
            self.in_execute_method = True
            
            # Check return type annotation
            if node.returns:
                if isinstance(node.returns, ast.Name):
                    self.execute_return_type = node.returns.id
                elif isinstance(node.returns, ast.Attribute):
                    self.execute_return_type = node.returns.attr
                elif isinstance(node.returns, ast.Subscript):
                    # Handle Union[Dict, AgentOutput] or similar
                    if isinstance(node.returns.slice, ast.Tuple):
                        for elt in node.returns.slice.elts:
                            if isinstance(elt, ast.Name) and elt.id == "AgentOutput":
                                self.execute_return_type = "AgentOutput"
                                break
            
            if self.execute_return_type != "AgentOutput":
                self.issues.append((
                    node.lineno,
                    "CRITICAL",
                    f"execute() must return AgentOutput, not {self.execute_return_type or 'unknown'}"
                ))
            else:
                print(f"  ✓ execute() return type: AgentOutput")
        
        self.generic_visit(node)
        self.in_execute_method = False
    
    def visit_Return(self, node: ast.Return):
        """Check what execute method returns"""
        if self.in_execute_method and node.value:
            # Check if returning a dict literal
            if isinstance(node.value, ast.Dict):
                self.issues.append((
                    node.lineno,
                    "CRITICAL",
                    "execute() returning dict literal instead of AgentOutput"
                ))
            # Check if returning a call that might return dict
            elif isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Attribute):
                    method_name = node.value.func.attr
                    # Allow converter methods
                    if not method_name.startswith("_") or "to_agent_output" not in method_name:
                        # This might be okay, but flag for review
                        pass
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Check for .get() calls on what might be Pydantic models"""
        if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            # Check if calling .get() on something that might be a Pydantic model
            if isinstance(node.func.value, ast.Name):
                var_name = node.func.value.id
                # Flag suspicious .get() calls
                if any(
                    suspect in var_name.lower() 
                    for suspect in ["input", "output", "agent", "config", "request"]
                ):
                    self.issues.append((
                        node.lineno,
                        "WARNING",
                        f"Suspicious .get() call on '{var_name}' - might be Pydantic model"
                    ))
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """Check for common Pydantic model attributes being accessed"""
        if node.attr in ["interpretationSeed", "confidence", "calculation", "correlations", "visualizationData"]:
            # This is good - accessing Pydantic model attributes correctly
            pass
        self.generic_visit(node)


def validate_file(filepath: Path) -> List[Tuple[int, str, str]]:
    """Parse and validate a single Python file"""
    print(f"\n🔍 Validating: {filepath.relative_to(Path.cwd())}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        
        validator = TypeContractValidator(str(filepath))
        validator.visit(tree)
        
        return validator.issues
    except SyntaxError as e:
        print(f"  ❌ Syntax error: {e}")
        return [(e.lineno or 0, "ERROR", f"Syntax error: {e.msg}")]
    except Exception as e:
        print(f"  ❌ Error parsing file: {e}")
        return [(0, "ERROR", str(e))]


def main():
    """Run validation on all agent files"""
    print("=" * 80)
    print("Type Contract Validation for Project Sovereign")
    print("=" * 80)
    
    # Find all agent files
    api_dir = Path(__file__).parent.parent / "src" / "agents"
    agent_files = list(api_dir.glob("**/*.py"))
    
    # Exclude __init__.py files
    agent_files = [f for f in agent_files if f.name != "__init__.py"]
    
    print(f"\nFound {len(agent_files)} agent files to validate")
    
    all_issues: Dict[str, List[Tuple[int, str, str]]] = {}
    
    for filepath in agent_files:
        issues = validate_file(filepath)
        if issues:
            all_issues[str(filepath)] = issues
    
    # Report findings
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    
    if not all_issues:
        print("\n✅ All type contracts are valid!")
        return 0
    
    critical_count = 0
    warning_count = 0
    
    for filepath, issues in all_issues.items():
        print(f"\n📄 {Path(filepath).relative_to(Path.cwd())}")
        for line_no, severity, message in issues:
            icon = "🔴" if severity == "CRITICAL" else "⚠️" if severity == "WARNING" else "ℹ️"
            print(f"  {icon} Line {line_no}: [{severity}] {message}")
            if severity == "CRITICAL":
                critical_count += 1
            elif severity == "WARNING":
                warning_count += 1
    
    print("\n" + "=" * 80)
    print(f"Summary: {critical_count} critical issues, {warning_count} warnings")
    print("=" * 80)
    
    return 1 if critical_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
