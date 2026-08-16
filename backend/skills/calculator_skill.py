""" 
============================================================ 
AVORA Calculator Skill 
============================================================ 

Handles mathematical calculations for AI Friend. 

Features: 
    â€�¢ Safe mathematical expression evaluation 
    â€�¢ Supports basic arithmetic (+, -, *, /, %, **) 
    â€�¢ Supports parentheses and order of operations 
    â€�¢ Rejects unsafe expressions (no imports, function calls, etc.) 

""" 

from __future__ import annotations 

import ast 
import logging 
from typing import Dict, Any, Optional 

from skills.skill_base import BaseSkill, register_skill 

logger = logging.getLogger("CalculatorSkill") 


class CalculatorSkill(BaseSkill): 
    """Skill for performing mathematical calculations.""" 
    
    def __init__(self): 
        super().__init__( 
            name="calculator_skill", 
            description="Performs mathematical calculations" 
        ) 
    
    def can_handle(self, intent: str, params: Dict[str, Any]) -> bool: 
        """Can handle calculate intents.""" 
        from core.intelligence_engine import IntentType 
        return intent == IntentType.CALCULATE 
    
    def plan(self, intent: str, params: Dict[str, Any], 
             context: Dict[str, Any]) -> Optional[Dict[str, Any]]: 
        """Create a plan to calculate the expression.""" 
        target = params.get("target", "") 
        if not target: 
            return None 
        
        return { 
            "skill": "calculator_skill", 
            "action": "calculate", 
            "target": target, 
            "context": context, 
        } 
    
    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]: 
        """Execute the calculation plan.""" 
        target = plan.get("target", "") 
        if not target: 
            return { 
                "success": False, 
                "message": "No expression provided", 
            } 
        
        try: 
            result = self._safe_eval(target) 
            # Format the result: remove trailing .0 if integer 
            if isinstance(result, float) and result.is_integer(): 
                result = int(result) 
            expression = target.strip() 
            return { 
                "success": True, 
                "message": f"{expression} = {result}", 
                "result": result, 
            } 
        except Exception as e: 
            logger.error(f"Calculation error: {e}") 
            return { 
                "success": False, 
                "message": f"Could not calculate '{target}': {str(e)}", 
            } 
    
def _safe_eval(self, expr: str): 
        """Safely evaluate a mathematical expression."""
        # Parse the expression into an AST
        try:
            tree = ast.parse(expr, mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Invalid syntax: {e}")
        
        # Define allowed node types - only pure math, no names or calls
        allowed_nodes = {
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.Pow,
            ast.Mod,
            ast.UAdd,
            ast.USub,
        }
        
        def check_node(node):
            node_type = type(node)
            if node_type not in allowed_nodes:
                raise ValueError(f"Disallowed node type: {node_type.__name__}")
            for child in ast.iter_child_nodes(node):
                check_node(child)
        
        try:
            check_node(tree)
        except ValueError as e:
            raise ValueError(f"Unsafe expression: {e}")
        
        # Compile and evaluate in a restricted namespace with no builtins
        code = compile(tree, '<string>', 'eval')
        return eval(code, {"__builtins__": {}})


skill = CalculatorSkill() 
register_skill("calculator_skill", skill) 

__all__ = ["CalculatorSkill", "skill"] 
