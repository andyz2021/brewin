from intbase import InterpreterBase, ErrorType
from brewparse import parse_program

# use InterpreterBase.output() and InterpreterBase.input() for print/input

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp) 
        self.op = { #idea from stack overflow: https://stackoverflow.com/questions/1740726/turn-string-into-operator
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x // y,
            '==': lambda x, y: x == y,
            '<': lambda x, y: x < y,
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            '!=': lambda x, y: x != y,
        }



    def run(self, program):
        # program: list of strings we want to parse through
        parsed = parse_program(program)
        # program node

        # set up variables
        self.variables = dict() # we should have a map from the function name we're currently in, to the variables defined in that function
        # When we enter a new function, we enter in all the variables from the caller function into the callee dictionary 
        self.functions = dict() # map function name to function node
        self.curr_func = 'main' # set our current function we're running

        # turn into AST

        funcs = parsed.dict['functions'] # get funcs

        foundMain = False
        for func in funcs:
            if func.dict['name'] == 'main':
                foundMain = True
                mainFunc = func
                # self.run_func(func) # run the functions
            else:
                self.functions[[func.dict['name'], len(func.dict['args'])]] = func # map function name and number of arguments to the function node 
            # in the future, we only run main and set up the other functions, so we can run when needed
        
        if not foundMain:
            super().error(
            ErrorType.NAME_ERROR,
            "No main() function was found",
        )
            
        self.run_func(mainFunc)# run mainFunc

    def run_func(self, func):
        funcName = func.dict['name']
        args = func.dict['args']
        arg_names = []
        for arg in args:
            var = arg.dict['name']
            arg_names.append(var)
        statements = func.dict['statements']

        for statement in statements:
            self.run_statement(statement)



    
    def run_statement(self, statement):
        if statement.elem_type == '=':
            # assignment
            self.do_assignment(statement)
        elif statement.elem_type == 'fcall':
            # function
            self.curr_func = statement.dict['name']
            self.evaluate_function(statement)

        elif statement.elem_type == 'if':
            self.evaluate_condition(statement)

        elif statement.elem_type == 'while':
            self.evaluate_loop(statement)
        
        elif statement.elem_type == 'return':
            # somehow return value?

    def do_assignment(self, statement):
        varName = statement.dict['name']
        expression = statement.dict['expression']
        self.variables[varName] = self.evaluate_node(expression)

        # if(expression.elem_type == "int" or expression.elem_type == "string"): # value node
        #     self.variables[varName] = expression.dict['val']

        # elif(expression.elem_type == "var"): # variable node
        #     self.variables[varName] = self.variables[expression.dict['name']]

        # else: # expression node
        #     self.variables[varName] = self.evaluateExpression(self, expression)

    
    def evaluate_function(self, func):
        funcName = func.dict['name']
        numArgs = func.dict['args']
        if funcName == "print":
            output_str = ""
            for s in func.dict['args']:
                temp_str = self.evaluate_node(s)
                try:
                    output_str += str(temp_str)
                except:
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for arithmetic operation",
                )
            super().output(output_str)

        
        elif funcName == "inputi":
            if len(func.dict['args']) > 1:
                super().error(
                ErrorType.NAME_ERROR,
                f"No inputi() function found that takes > 1 parameter",
            )
            if len(func.dict['args']) == 1:
                output_str = self.evaluate_node(func.dict['args'][0])
                super().output(output_str)

            inputInt = super().get_input()
            inputInt = int(inputInt)

            return inputInt
        
        elif [funcName, numArgs] in self.functions:
            self.run_func(self.functions[[funcName, numArgs]])
        else:
                super().error(
                ErrorType.NAME_ERROR,
                "Undefined function",
            )
            
        


    def evaluate_node(self, node): # This function will get the value from a value/variable/expression node
        if(node.elem_type == "int" or node.elem_type == "string" or node.elem_type == "bool"): # value node
            return node.dict['val']
        
        if(node.elem_type == 'nil'):
            return None

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

            if type in self.op:
                op1 = self.evaluate_node(node.dict['op1'])
                op2 = self.evaluate_node(node.dict['op2']) 
                try:
                    return self.op[type](op1,op2)
                except:
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types",
                )
            
            # if type == '+': #binary operation
            #     op1 = self.evaluate_node(node.dict['op1'])
            #     op2 = self.evaluate_node(node.dict['op2'])
            #     try:
            #         return op1 + op2
            #     except:
            #         super().error(
            #         ErrorType.TYPE_ERROR,
            #         "Incompatible types for arithmetic operation",
            #     )
            # elif type == '-':
            #     op1 = self.evaluate_node(node.dict['op1'])
            #     op2 = self.evaluate_node(node.dict['op2'])
            #     try:
            #         return op1 - op2
            #     except:
            #         super().error(
            #         ErrorType.TYPE_ERROR,
            #         "Incompatible types for arithmetic operation",
            #     )
            
            elif type == '!':
                op1 = self.evaluate_node(node.dict['op1'])

                try:
                    return not op1
                except:
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for boolean not",
                )

            elif type == 'neg':
                op1 = self.evaluate_node(node.dict['op1'])

                try:
                    return -op1
                except:
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for negation",
                )
            
            else:
                self.curr_func = node.dict['name']
                retval =  self.evaluate_function(node) # should be result of inputi
                self.curr_func = 

           
               


    
def main():
    interpreter = Interpreter()
    program1 = """func main() {
    x = 6;
    y = 3;
    print(4+inputi(2));
}
"""

    interpreter.run(program1)


if __name__ == '__main__':
    main()
        
        

        