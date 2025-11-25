"""
Python AST Parser for Graphical Code Editor

Extracts code structure at three levels:
1. Architecture: modules, classes, imports, relationships
2. Signatures: function/method signatures
3. Code: full source code
"""

import ast
import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set
from pathlib import Path


@dataclass
class FunctionInfo:
    name: str
    signature: str
    docstring: Optional[str]
    code: str
    lineno: int
    end_lineno: int
    decorators: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)  # Functions this function calls


@dataclass
class ClassInfo:
    name: str
    docstring: Optional[str]
    bases: List[str]  # Parent classes
    methods: List[FunctionInfo] = field(default_factory=list)
    lineno: int = 0
    end_lineno: int = 0


@dataclass
class ModuleInfo:
    name: str
    path: str
    docstring: Optional[str]
    imports: List[str] = field(default_factory=list)  # What this module imports
    import_from: Dict[str, List[str]] = field(default_factory=dict)  # from X import Y
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    code: str = ""


class CallVisitor(ast.NodeVisitor):
    """Extract function calls from a function body"""

    def __init__(self):
        self.calls: Set[str] = set()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Handle method calls like obj.method()
            self.calls.add(node.func.attr)
        self.generic_visit(node)


class CodeParser:
    """Parse Python code and extract structure at multiple levels"""

    def __init__(self, source_code: str, filename: str = "module.py"):
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.filename = filename
        self.tree = ast.parse(source_code, filename)

    def get_source_segment(self, node) -> str:
        """Extract source code for a node"""
        try:
            return ast.get_source_segment(self.source_code, node) or ""
        except:
            # Fallback to line-based extraction
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                lines = self.source_lines[node.lineno - 1:node.end_lineno]
                return '\n'.join(lines)
            return ""

    def get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature"""
        args = []

        # Positional-only args (Python 3.8+)
        for arg in node.args.posonlyargs:
            args.append(self._format_arg(arg))
        if node.args.posonlyargs:
            args.append('/')

        # Regular args
        defaults_offset = len(node.args.args) - len(node.args.defaults)
        for i, arg in enumerate(node.args.args):
            default_idx = i - defaults_offset
            if default_idx >= 0:
                default = ast.unparse(node.args.defaults[default_idx])
                args.append(f"{self._format_arg(arg)}={default}")
            else:
                args.append(self._format_arg(arg))

        # *args
        if node.args.vararg:
            args.append(f"*{self._format_arg(node.args.vararg)}")
        elif node.args.kwonlyargs:
            args.append('*')

        # Keyword-only args
        kw_defaults_dict = {i: d for i, d in enumerate(node.args.kw_defaults) if d is not None}
        for i, arg in enumerate(node.args.kwonlyargs):
            if i in kw_defaults_dict:
                default = ast.unparse(kw_defaults_dict[i])
                args.append(f"{self._format_arg(arg)}={default}")
            else:
                args.append(self._format_arg(arg))

        # **kwargs
        if node.args.kwarg:
            args.append(f"**{self._format_arg(node.args.kwarg)}")

        # Return annotation
        returns = ""
        if node.returns:
            returns = f" -> {ast.unparse(node.returns)}"

        return f"def {node.name}({', '.join(args)}){returns}:"

    def _format_arg(self, arg: ast.arg) -> str:
        """Format a function argument"""
        if arg.annotation:
            return f"{arg.arg}: {ast.unparse(arg.annotation)}"
        return arg.arg

    def parse_function(self, node: ast.FunctionDef) -> FunctionInfo:
        """Parse a function definition"""
        # Get decorators
        decorators = []
        for dec in node.decorator_list:
            decorators.append(ast.unparse(dec))

        # Get docstring
        docstring = ast.get_docstring(node)

        # Get function calls
        call_visitor = CallVisitor()
        call_visitor.visit(node)

        return FunctionInfo(
            name=node.name,
            signature=self.get_function_signature(node),
            docstring=docstring,
            code=self.get_source_segment(node),
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno,
            decorators=decorators,
            calls=list(call_visitor.calls)
        )

    def parse_class(self, node: ast.ClassDef) -> ClassInfo:
        """Parse a class definition"""
        # Get base classes
        bases = []
        for base in node.bases:
            bases.append(ast.unparse(base))

        # Get docstring
        docstring = ast.get_docstring(node)

        # Get methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self.parse_function(item))

        return ClassInfo(
            name=node.name,
            docstring=docstring,
            bases=bases,
            methods=methods,
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno
        )

    def parse_module(self) -> ModuleInfo:
        """Parse the entire module"""
        imports = []
        import_from = {}
        classes = []
        functions = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module not in import_from:
                    import_from[module] = []
                for alias in node.names:
                    import_from[module].append(alias.name)

        # Only get top-level classes and functions
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append(self.parse_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self.parse_function(node))

        return ModuleInfo(
            name=Path(self.filename).stem,
            path=self.filename,
            docstring=ast.get_docstring(self.tree),
            imports=imports,
            import_from=import_from,
            classes=classes,
            functions=functions,
            code=self.source_code
        )


def parse_directory(directory: str) -> List[ModuleInfo]:
    """Parse all Python files in a directory"""
    modules = []

    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        source = f.read()
                    parser = CodeParser(source, filepath)
                    modules.append(parser.parse_module())
                except (SyntaxError, UnicodeDecodeError) as e:
                    print(f"Error parsing {filepath}: {e}")

    return modules


def module_to_dict(module: ModuleInfo) -> dict:
    """Convert ModuleInfo to dictionary for JSON serialization"""
    return {
        'name': module.name,
        'path': module.path,
        'docstring': module.docstring,
        'imports': module.imports,
        'import_from': module.import_from,
        'classes': [
            {
                'name': c.name,
                'docstring': c.docstring,
                'bases': c.bases,
                'lineno': c.lineno,
                'end_lineno': c.end_lineno,
                'methods': [
                    {
                        'name': m.name,
                        'signature': m.signature,
                        'docstring': m.docstring,
                        'code': m.code,
                        'lineno': m.lineno,
                        'end_lineno': m.end_lineno,
                        'decorators': m.decorators,
                        'calls': m.calls
                    }
                    for m in c.methods
                ]
            }
            for c in module.classes
        ],
        'functions': [
            {
                'name': f.name,
                'signature': f.signature,
                'docstring': f.docstring,
                'code': f.code,
                'lineno': f.lineno,
                'end_lineno': f.end_lineno,
                'decorators': f.decorators,
                'calls': f.calls
            }
            for f in module.functions
        ],
        'code': module.code
    }


if __name__ == '__main__':
    # Test with this file itself
    with open(__file__, 'r') as f:
        source = f.read()

    parser = CodeParser(source, __file__)
    module = parser.parse_module()

    print(json.dumps(module_to_dict(module), indent=2))
