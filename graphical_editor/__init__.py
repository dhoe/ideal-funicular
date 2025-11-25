"""
Graphical Code Editor

A zoomable Python code visualization tool with three detail levels:
1. Architecture: Boxes and arrows overview
2. Signatures: Function signatures visible
3. Code: Full source code
"""

from .code_parser import CodeParser, parse_directory, module_to_dict

__version__ = '1.0.0'
__all__ = ['CodeParser', 'parse_directory', 'module_to_dict']
