// static/js/safe-formula-evaluator.js - Safe frontend formula evaluation
class SafeFormulaEvaluator {
    constructor() {
        // Define allowed mathematical operations and functions
        this.safeOperators = ['+', '-', '*', '/', '(', ')', 'Math.ceil', 'Math.floor', 'Math.round', 'Math.sqrt'];
        this.allowedVariables = ['width_m', 'height_m', 'area_m2', 'perimeter_m', 'quantity', 'num_hojas'];
    }

    /**
     * Safely evaluate a mathematical formula with given variables
     * @param {string} formula - Mathematical expression string
     * @param {Object} variables - Object with variable values
     * @returns {number} Result of the formula evaluation
     */
    evaluateFormula(formula, variables) {
        if (!formula || typeof formula !== 'string') {
            throw new Error('Formula must be a non-empty string');
        }

        // Validate formula contains only safe characters and operations
        if (!this.isFormulaValid(formula)) {
            throw new Error('Formula contains unsafe operations or characters');
        }

        // Replace variables with their values
        let processedFormula = formula;
        for (const [varName, value] of Object.entries(variables)) {
            if (this.allowedVariables.includes(varName)) {
                // Use word boundaries to avoid partial replacements
                const regex = new RegExp(`\\b${varName}\\b`, 'g');
                processedFormula = processedFormula.replace(regex, value.toString());
            }
        }

        // Validate that all variables have been replaced (no remaining variable names)
        for (const varName of this.allowedVariables) {
            const regex = new RegExp(`\\b${varName}\\b`);
            if (regex.test(processedFormula)) {
                throw new Error(`Undefined variable: ${varName}`);
            }
        }

        try {
            // Use Function constructor for safer evaluation than eval()
            const result = new Function('Math', `"use strict"; return (${processedFormula})`)(Math);
            
            if (typeof result !== 'number' || !isFinite(result)) {
                throw new Error('Formula must evaluate to a finite number');
            }
            
            return result;
        } catch (error) {
            throw new Error(`Error evaluating formula '${formula}': ${error.message}`);
        }
    }

    /**
     * Validate if a formula contains only safe characters and operations
     * @param {string} formula - Formula to validate
     * @returns {boolean} True if formula is safe
     */
    isFormulaValid(formula) {
        // Allow only numbers, operators, parentheses, dots, variable names, and Math functions
        const safePattern = /^[0-9+\-*/().\s]*(width_m|height_m|area_m2|perimeter_m|quantity|num_hojas|Math\.(ceil|floor|round|sqrt))*[0-9+\-*/().\s]*$/;
        
        // Check for dangerous patterns
        const dangerousPatterns = [
            /eval\s*\(/,
            /Function\s*\(/,
            /constructor/,
            /prototype/,
            /__/,
            /document/,
            /window/,
            /global/,
            /process/,
            /require/,
            /import/,
            /export/,
            /[<>]/,
            /[;&|]/,
            /alert/,
            /console/,
            /fetch/,
            /XMLHttpRequest/
        ];

        // Check for dangerous patterns
        for (const pattern of dangerousPatterns) {
            if (pattern.test(formula)) {
                return false;
            }
        }

        return safePattern.test(formula);
    }

    /**
     * Validate formula syntax with test variables
     * @param {string} formula - Formula to validate
     * @returns {boolean} True if formula is syntactically valid
     */
    validateFormula(formula) {
        try {
            const testVars = {
                width_m: 1.0,
                height_m: 1.0,
                area_m2: 1.0,
                perimeter_m: 4.0,
                quantity: 1,
                num_hojas: 2
            };
            
            this.evaluateFormula(formula, testVars);
            return true;
        } catch {
            return false;
        }
    }
}

// Global instance for use throughout the application
const safeFormulaEvaluator = new SafeFormulaEvaluator();