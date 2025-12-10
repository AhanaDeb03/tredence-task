"""
Pre-built workflow examples that you can use right away!

Think of these as ready-made recipes - you don't have to build them from scratch.
Just pick one, give it your data, and watch it work its magic!
"""
from typing import Dict, Any
from app.tools import tool_registry


def create_code_review_workflow() -> Dict[str, Any]:
    """
    Code Review Mini-Agent - Your helpful code quality assistant! 🔍
    
    This workflow analyzes your code and helps improve its quality. Here's what it does:
    
    1. Extract functions - "What functions do you have in this code?"
    2. Check complexity - "How complex is this code? Can it be simpler?"
    3. Detect issues - "Are there any code smells or problems I can spot?"
    4. Suggest improvements - "Here's how you could make this better!"
    5. Loop until quality is good - "Keep improving until it meets your standards!"
    
    The workflow will keep looping and improving until your code reaches
    the quality threshold you set (or until max iterations).
    """
    
    def extract_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 1: Extract all the functions from the code.
        
        Like creating a table of contents - we need to know what we're working with!
        """
        code = state.get("code", "")
        result = tool_registry.call("extract_functions", code)
        return {
            "extracted_functions": result["functions"],
            "function_count": result["function_count"],
            "message": f"Found {result['function_count']} function(s) in your code!"
        }
    
    def check_complexity_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: Measure how complex the code is.
        
        Complexity matters! Simple code is easier to understand, debug, and maintain.
        We calculate metrics and give it a quality score (0-100).
        """
        code = state.get("code", "")
        result = tool_registry.call("check_complexity", code)
        
        quality_score = result["quality_score"]
        complexity = result["complexity"]
        
        # Give a friendly status message
        if quality_score >= 80:
            status_msg = "🌟 Excellent! Your code is clean and simple!"
        elif quality_score >= 60:
            status_msg = "👍 Good job! Your code is pretty readable."
        elif quality_score >= 40:
            status_msg = "⚠️  Your code could use some simplification."
        else:
            status_msg = "💡 This code is quite complex - let's work on making it simpler!"
        
        return {
            "complexity": complexity,
            "lines_of_code": result["lines_of_code"],
            "quality_score": quality_score,
            "message": f"Complexity: {complexity}, Quality Score: {quality_score}/100. {status_msg}"
        }
    
    def detect_issues_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3: Look for code smells and potential issues.
        
        Code smells are signs that something might be wrong - like a warning light
        on your car's dashboard. They don't mean your code is broken, but they
        suggest it could be better!
        """
        code = state.get("code", "")
        result = tool_registry.call("detect_smells", code)
        
        issue_count = result["issue_count"]
        if issue_count == 0:
            message = "✨ No issues detected! Your code looks clean!"
        elif issue_count == 1:
            message = f"🔍 Found {issue_count} potential issue - nothing major!"
        else:
            message = f"🔍 Found {issue_count} potential issues - let's address them!"
        
        return {
            "issues": result["issues"],
            "issue_count": issue_count,
            "message": message
        }
    
    def suggest_improvements_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 4: Suggest concrete ways to improve the code.
        
        Not just "this is bad" - but "here's how to make it better!"
        We give actionable advice with priorities (high/medium/low).
        """
        issues = state.get("issues", [])
        complexity = state.get("complexity", 0)
        quality_score = state.get("quality_score", 0)
        
        result = tool_registry.call("suggest_improvements", issues, complexity, quality_score)
        
        suggestion_count = result["suggestion_count"]
        if suggestion_count == 0:
            message = "🎉 No suggestions needed - your code is already great!"
        else:
            message = f"💡 Here are {suggestion_count} suggestion(s) to improve your code!"
        
        return {
            "suggestions": result["suggestions"],
            "suggestion_count": suggestion_count,
            "message": message
        }
    
    def check_loop_condition_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5: Decide if we should keep improving or if we're done!
        
        This is the "quality gate" - we keep looping until the code meets
        your quality standards (quality_score >= threshold).
        
        In a real scenario, this node would apply the suggestions we made,
        then re-check the quality. For this demo, we simulate improvement.
        """
        quality_score = state.get("quality_score", 0)
        threshold = state.get("quality_threshold", 70)
        iteration = state.get("_iteration", 0)
        max_iterations = state.get("max_loop_iterations", 3)
        
        # Should we keep looping?
        # Only if quality is below threshold AND we haven't exceeded max iterations
        should_loop = quality_score < threshold and iteration < max_iterations
        
        # Simulate improvement (in a real system, you'd actually apply fixes here)
        if should_loop and iteration > 0:
            # Each iteration, we improve the quality score a bit
            # (simulating that we applied the suggestions)
            improvement = min(10, threshold - quality_score)
            quality_score += improvement
            state["quality_score"] = quality_score
        
        if should_loop:
            # Not there yet - let's try again!
            return {
                "_next_node": "check_complexity",  # Go back and re-check
                "_loop": True,  # Mark that we're in a loop
                "quality_score": quality_score,
                "message": (
                    f"Quality score is {quality_score}, but we need {threshold}. "
                    f"Let's keep improving! (iteration {iteration}/{max_iterations})"
                )
            }
        else:
            # We're done! Either we met the threshold or hit max iterations
            if quality_score >= threshold:
                message = (
                    f"🎉 Success! Quality score is {quality_score}, "
                    f"which meets your threshold of {threshold}!"
                )
            else:
                message = (
                    f"Quality check complete. Final score: {quality_score} "
                    f"(target was {threshold}). "
                    f"We reached the maximum number of iterations ({max_iterations})."
                )
            
            return {
                "_loop": False,  # Exit the loop
                "message": message
            }
    
    # Return the workflow definition - all the nodes and how they connect
    return {
        "name": "Code Review Mini-Agent",
        "description": "Analyzes code quality and suggests improvements until standards are met",
        "nodes": {
            "extract": {
                "func": extract_node,
                "description": "Extract functions from code"
            },
            "check_complexity": {
                "func": check_complexity_node,
                "description": "Measure code complexity and calculate quality score"
            },
            "detect_issues": {
                "func": detect_issues_node,
                "description": "Detect code smells and potential issues"
            },
            "suggest_improvements": {
                "func": suggest_improvements_node,
                "description": "Generate improvement suggestions"
            },
            "check_loop": {
                "func": check_loop_condition_node,
                "description": "Check if quality threshold is met, loop if needed"
            }
        },
        "edges": [
            ("extract", "check_complexity"),           # First, extract then check complexity
            ("check_complexity", "detect_issues"),     # Then detect issues
            ("detect_issues", "suggest_improvements"), # Then suggest fixes
            ("suggest_improvements", "check_loop"),    # Then check if we're done
            ("check_loop", "check_complexity")         # Loop back if needed
        ],
        "entry_node": "extract",  # Start here
        "exit_nodes": ["check_loop"]  # Can finish here
    }
