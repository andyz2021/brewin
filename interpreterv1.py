from intbase import InterpreterBase, ErrorType
from brewparse import parse_program

# use InterpreterBase.output() and InterpreterBase.input() for print/input

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp) 



    def run(self, program):
        # program: list of strings we want to parse through
        parsed = parse_program(program)
        self.variables = dict()
        # turn into AST

        for node in parsed:
            if(node.elem_type == "program"):
                #parseProgramNode...
                funcs = node.dict['functions'] # for now, this is just the main func
                break

        foundMain = False
        for func in funcs:
            if func.dict['name'] == 'main':
                foundMain = True
            self.run_func(func)
        super().error(
        ErrorType.NAME_ERROR,
        "No main() function was found",
    )

    def run_func(self, func):
        funcName = func.dict['name']
        statements = func.dict['statements']

        for statement in statements:
            self.run_statement(self, statement)


    
    def run_statement(self, statement):
        if statement.elem_type == '=':
            # assignment
            self.do_assignment(self, statement)
        elif statement.elem_type == 'fcall':
            # function
            self.evaluate_function(self, statement)

    def do_assignment(self, statement):
        varName = statement.dict['name']
        expression = statement.dict['expression']
        self.variables[varName] = self.get_value(self, expression)

        # if(expression.elem_type == "int" or expression.elem_type == "string"): # value node
        #     self.variables[varName] = expression.dict['val']

        # elif(expression.elem_type == "var"): # variable node
        #     self.variables[varName] = self.variables[expression.dict['name']]

        # else: # expression node
        #     self.variables[varName] = self.evaluateExpression(self, expression)

    
    def evaluate_function(self, func):
        funcName = func['name']
        if funcName == "print":
            str = ""
            for s in func['args']:
                str += 
        
        if funcName == "inputi":
            if len(func['args']) > 1:
                super().error(
                ErrorType.NAME_ERROR,
                f"No inputi() function found that takes > 1 parameter",
            )
        


    def get_value(self, node): # This function will get the value from a value/variable/expression node
        if(node.elem_type == "int" or node.elem_type == "string"): # value node
            return node.dict['val']

        elif(node.elem_type == "var"): # variable node
            if node.dict['name'] in self.variables:
                return self.variables[node.dict['name']]
            else:
                super().error(
                ErrorType.NAME_ERROR,
                f"Variable {node.dict['name']} has not been defined",
            )

        else: # expression node
            type = node.elem_type

            if type == '+': #binary operation
                op1 = node.dict['op1']
                op2 = node.dict['op2']
                try:
                    return self.getValue(self, op1) + self.getValue(self, op2)
                except:
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for arithmetic operation",
                )
            elif type == '-':
                op1 = node.dict['op1']
                op2 = node.dict['op2']
                try:
                    return self.getValue(self, op1) - self.getValue(self, op2)
                except:
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for arithmetic operation",
                )
            
            else:
                return self.evaluate_function(self, node)

           
               


    

        
        

        