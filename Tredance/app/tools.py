"""
A toolbox full of useful functions that workflow nodes can use!

Think of this as your Swiss Army knife - each tool does one specific job well.
Nodes can grab tools from here to do things like:
- Analyzing code
- Detecting problems
- Calculating metrics
- Making suggestions

Want to add your own tool? Just write a function and register it!
"""
from typing import Dict, Any, Callable
import re


class ToolRegistry:
    """
    A central registry where we keep all our tools organized.
    
    Think of it like a tool shed - you can:
    - Add new tools (register)
    - Find tools by name (get)
    - Use a tool (call)
    - See what tools are available (list_tools)
    """
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
    
    def register(self, name: str, func: Callable):
        """Add a new tool to the registry - give it a name so others can find it!"""
        self.tools[name] = func
    
    def get(self, name: str) -> Callable:
        """Find a tool by name - throws a helpful error if it doesn't exist."""
        if name not in self.tools:
            available = ", ".join(self.tools.keys()) or "none"
            raise ValueError(
                f"Tool '{name}' not found! "
                f"Available tools: {available}. "
                f"Did you forget to register it?"
            )
        return self.tools[name]
    
    def call(self, name: str, *args, **kwargs) -> Any:
        """Use a tool by name - just pass in the tool name and its arguments."""
        tool = self.get(name)
        return tool(*args, **kwargs)
    
    def list_tools(self) -> Dict[str, str]:
        """
        Get a list of all available tools with their descriptions.
        
        Perfect for showing users what they can use in their workflows!
        """
        return {
            name: func.__doc__ or "No description available"
            for name, func in self.tools.items()
        }


# Create a global tool registry that everyone can use
tool_registry = ToolRegistry()


# ============================================================================
# Code Analysis Tools
# ============================================================================

def detect_smells(code: str) -> Dict[str, Any]:
    """
    Sniff out code smells - those telltale signs that code could be better!
    
    This is like having a code reviewer who looks for:
    - Functions that are way too long (hard to understand)
    - Deeply nested code (hard to follow)
    - Magic numbers (what does 42 mean?!)
    - TODO comments (unfinished business)
    
    Args:
        code: The source code to analyze (as a string)
        
    Returns:
        A dictionary with:
        - issues: List of detected problems with details
        - issue_count: How many issues we found
    """
    issues = []
    
    # Check for functions that are too long (harder to read and maintain)
    lines = code.split('\n')
    if len(lines) > 50:
        issues.append({
            "type": "long_function",
            "severity": "medium",
            "message": f"This function is {len(lines)} lines long. "
                      f"Consider splitting it into smaller, focused functions. "
                      f"Your future self will thank you!"
        })
    
    # Check for code that's nested too deeply (hard to follow the logic)
    max_nesting = 0
    current_nesting = 0
    for line in lines:
        # Count control flow statements that add nesting
        current_nesting += line.count('if ') + line.count('for ') + line.count('while ')
        current_nesting -= line.count('elif ') - 1  # elif doesn't add new nesting level
        max_nesting = max(max_nesting, current_nesting)
    
    if max_nesting > 4:
        issues.append({
            "type": "high_nesting",
            "severity": "high",
            "message": f"This code has {max_nesting} levels of nesting. "
                      f"That's like trying to read a book inside a book inside a book! "
                      f"Consider extracting functions or using early returns to flatten it."
        })
    
    # Check for "magic numbers" - hardcoded numbers that don't explain themselves
    magic_numbers = re.findall(r'\b\d{3,}\b', code)  # Find numbers with 3+ digits
    if len(magic_numbers) > 5:
        issues.append({
            "type": "magic_numbers",
            "severity": "low",
            "message": f"Found {len(magic_numbers)} potential magic numbers. "
                      f"Consider replacing them with named constants so the code explains itself. "
                      f"For example: MAX_RETRIES = 3 instead of just 3"
        })
    
    # Check for TODO/FIXME comments (technical debt markers)
    todo_count = len(re.findall(r'(TODO|FIXME|XXX|HACK)', code, re.IGNORECASE))
    if todo_count > 0:
        issues.append({
            "type": "todo_comments",
            "severity": "low",
            "message": f"Found {todo_count} TODO/FIXME comments. "
                      f"These are like little notes saying 'I'll fix this later' - "
                      f"make sure they don't pile up!"
        })
    
    return {
        "issues": issues,
        "issue_count": len(issues)
    }


def check_complexity(code: str) -> Dict[str, Any]:
    """
    Measure how complex your code is - like a readability score!
    
    Complexity matters because:
    - Simple code = easy to understand = fewer bugs
    - Complex code = hard to understand = more bugs
    
    We calculate a simple complexity score and convert it to a quality score (0-100).
    
    Args:
        code: The source code to analyze
        
    Returns:
        Dictionary with:
        - complexity: How many decision points (if/for/while/etc.) the code has
        - lines_of_code: Number of non-empty lines
        - total_lines: Total lines including empty ones
        - quality_score: A score from 0-100 (higher is better!)
    """
    lines = code.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    
    # Simple cyclomatic complexity: count decision points
    # Each if/for/while/etc. makes the code harder to follow
    complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'except', 'and', 'or']
    complexity = 1  # Start with base complexity of 1
    for line in lines:
        complexity += sum(1 for keyword in complexity_keywords if keyword in line)
    
    # Convert complexity to a quality score (0-100)
    # More complexity = lower quality score
    # This is a simple formula - in real life, you'd use more sophisticated metrics
    quality_score = max(0, min(100, 100 - (complexity * 2)))
    
    return {
        "complexity": complexity,
        "lines_of_code": len(non_empty_lines),
        "total_lines": len(lines),
        "quality_score": quality_score
    }


def extract_functions(code: str) -> Dict[str, Any]:
    """
    Find all the functions in your code - like a table of contents!
    
    This helps you understand the structure of your code at a glance.
    
    Args:
        code: The source code to analyze
        
    Returns:
        Dictionary with:
        - functions: List of function info (name, code, line count)
        - function_count: How many functions we found
    """
    functions = []
    # Look for function definitions: "def function_name(...):"
    function_pattern = re.compile(r'def\s+(\w+)\s*\([^)]*\):')
    
    for match in function_pattern.finditer(code):
        func_name = match.group(1)  # Extract the function name
        start_pos = match.start()
        
        # Find where this function ends (simplified - looks for next function or end of string)
        end_match = function_pattern.search(code, start_pos + 1)
        if end_match:
            func_code = code[start_pos:end_match.start()]
        else:
            func_code = code[start_pos:]
        
        functions.append({
            "name": func_name,
            "code": func_code.strip(),
            "line_count": len(func_code.split('\n'))
        })
    
    return {
        "functions": functions,
        "function_count": len(functions)
    }


def suggest_improvements(issues: list, complexity: int, quality_score: float) -> Dict[str, Any]:
    """
    Give friendly, actionable advice on how to improve your code!
    
    This looks at all the issues and metrics we've found, and suggests
    specific things you can do to make your code better.
    
    Args:
        issues: List of detected issues (from detect_smells)
        complexity: Complexity score (from check_complexity)
        quality_score: Quality score 0-100 (from check_complexity)
        
    Returns:
        Dictionary with:
        - suggestions: List of improvement suggestions with priorities
        - suggestion_count: How many suggestions we have
    """
    suggestions = []
    
    # Give suggestions based on the issues we found
    for issue in issues:
        if issue["type"] == "long_function":
            suggestions.append({
                "type": "refactor",
                "priority": "medium",
                "suggestion": "This function is doing too much! "
                             "Try splitting it into smaller functions, each doing one thing well. "
                             "Think: 'Can I explain what this function does in one sentence?'"
            })
        elif issue["type"] == "high_nesting":
            suggestions.append({
                "type": "refactor",
                "priority": "high",
                "suggestion": "Those nested if statements are hard to follow! "
                             "Consider: extracting helper functions, using early returns, "
                             "or restructuring with guard clauses. "
                             "Your brain will thank you when debugging later!"
            })
        elif issue["type"] == "magic_numbers":
            suggestions.append({
                "type": "refactor",
                "priority": "low",
                "suggestion": "Replace those mysterious numbers with named constants! "
                             "Instead of `if count > 42:`, use `MAX_ITEMS = 42` then `if count > MAX_ITEMS:`. "
                             "Your code will explain itself better."
            })
    
    # Give suggestions based on overall complexity
    if complexity > 20:
        suggestions.append({
            "type": "refactor",
            "priority": "high",
            "suggestion": f"Your code has a complexity score of {complexity}, which is quite high! "
                         "Consider breaking it down into smaller, simpler pieces. "
                         "Remember: simple code is easy to understand, test, and fix."
        })
    
    # Give general feedback based on quality score
    if quality_score < 50:
        suggestions.append({
            "type": "general",
            "priority": "high",
            "suggestion": "Your code quality score is on the lower side. "
                         "Don't worry - every expert was once a beginner! "
                         "Try focusing on: simplifying logic, reducing nesting, "
                         "and breaking large functions into smaller ones. "
                         "You've got this! 💪"
        })
    
    return {
        "suggestions": suggestions,
        "suggestion_count": len(suggestions)
    }


# ============================================================================
# Register all our tools so they're available to workflows
# ============================================================================

tool_registry.register("detect_smells", detect_smells)
tool_registry.register("check_complexity", check_complexity)
tool_registry.register("extract_functions", extract_functions)
tool_registry.register("suggest_improvements", suggest_improvements)
