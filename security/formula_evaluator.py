# security/formula_evaluator.py - Safe formula evaluation
import ast
import math
import operator
from decimal import Decimal
from typing import Dict, Any, Union
from simpleeval import simple_eval

class SafeFormulaEvaluator:
    """
    Secure formula evaluator that replaces dangerous eval() usage.
    Only allows safe mathematical operations and pre-defined variables.
    """
    
    def __init__(self):
        # Define safe operators using AST node types (as required by simpleeval)
        self.safe_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
            ast.FloorDiv: operator.floordiv,
            # Comparison operators for conditional expressions
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            # Unary operators
            ast.UAdd: operator.pos,
            ast.USub: operator.neg,
        }
        
        # Define safe functions (mathematical only)
        self.safe_functions = {
            'abs': abs,
            'round': round,
            'int': int,
            'float': float,
            'min': min,
            'max': max,
            # Math module functions
            'ceil': math.ceil,
            'floor': math.floor,
            'sqrt': math.sqrt,
            'pow': pow,
            # Add more safe functions as needed
        }
        
        # Define safe names (built-in constants)
        self.safe_names = {
            'pi': math.pi,
            'e': math.e,
        }
    
    def evaluate_formula(self, formula: str, variables: Dict[str, Union[float, int, Decimal]]) -> Decimal:
        """
        Safely evaluate a mathematical formula with given variables.
        
        Args:
            formula: Mathematical expression string (e.g., "width_m * 2", "math.ceil(area_m2 / 2)")
            variables: Dictionary with variable values
            
        Returns:
            Decimal: Result of the formula evaluation
            
        Raises:
            ValueError: If formula is invalid or contains unsafe operations
            NameError: If formula references undefined variables
        """
        if not formula or not isinstance(formula, str):
            raise ValueError("Formula must be a non-empty string")
        
        # Prepare variables for evaluation (convert Decimals to float for math operations)
        eval_vars = {}
        for key, value in variables.items():
            if isinstance(value, Decimal):
                eval_vars[key] = float(value)
            else:
                eval_vars[key] = value
        
        # Add math module as a safe namespace
        eval_vars['math'] = type('math', (), {
            'ceil': math.ceil,
            'floor': math.floor,
            'sqrt': math.sqrt,
            'pi': math.pi,
            'e': math.e,
        })
        
        try:
            # Use simpleeval for safe evaluation
            result = simple_eval(
                formula,
                operators=self.safe_operators,
                functions=self.safe_functions,
                names={**self.safe_names, **eval_vars}
            )
            
            # Convert result back to Decimal for precision
            if isinstance(result, (int, float)):
                return Decimal(str(result))
            else:
                return Decimal(str(float(result)))
                
        except Exception as e:
            raise ValueError(f"Error evaluating formula '{formula}': {str(e)}")
    
    def validate_formula(self, formula: str, expected_variables: list = None) -> bool:
        """
        Validate if a formula is syntactically correct and uses only expected variables.
        
        Args:
            formula: Formula string to validate
            expected_variables: List of allowed variable names
            
        Returns:
            bool: True if formula is valid
        """
        if not formula or not isinstance(formula, str):
            return False
        
        try:
            # Try parsing with dummy values
            test_vars = {}
            if expected_variables:
                for var in expected_variables:
                    test_vars[var] = 1.0
            else:
                # Default test variables for window calculations
                test_vars = {
                    'width_m': 1.0,
                    'height_m': 1.0,
                    'area_m2': 1.0,
                    'perimeter_m': 4.0,
                    'quantity': 1,
                }
            
            self.evaluate_formula(formula, test_vars)
            return True
            
        except:
            return False

# Global instance for use throughout the application
formula_evaluator = SafeFormulaEvaluator()