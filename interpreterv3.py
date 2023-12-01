from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
import copy

# use InterpreterBase.output() and InterpreterBase.input() for print/input
nil = None
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
            '||': lambda x, y: x or y,
            '&&': lambda x, y: x and y,
        
        }

        self.intOps = ['+', '-', '*', '/', '<', '>', '<=', '>=', '==', '!=']
        self.stringOps = ['+', '==', '!=']
        self.boolOps = ['||', '&&', '==', '!=']
        self.otherComps = ['>', '<', '>=', '<=']
        self.arithOps = ['-', '+', '/', '*']



    def run(self, program):
        # program: list of strings we want to parse through
        parsed = parse_program(program)
        # program node

        # set up variables
        self.variables = [] # we should have a map from the function name we're currently in, to the variables defined in that function
        # When we enter a new function, we enter in all the variables from the caller function into the callee dictionary 
        self.functions = dict() # map function name to function node
        # self.funcNames = dict() # function name to their number of overloaded functions
        self.curr_func = [['main', 0]] # set our current function we're running
        self.variables.append(dict()) # current function variables defined 
        self.funcToNumArgs = dict()
        self.closures = dict() # mapping from variable name to closure(scope) at the moment it's defined 

        # turn into AST

        funcs = parsed.dict['functions'] # get funcs

        foundMain = False
        for func in funcs:
            if func.dict['name'] == 'main':
                foundMain = True
                mainFunc = func
                # self.run_func(func) # run the functions
            self.functions[(func.dict['name'], len(func.dict['args']))] = func # map function name and number of arguments to the function node 
            if func.dict['name'] in self.funcToNumArgs:
                self.funcToNumArgs[func.dict['name']].append(len(func.dict['args'])) # maps function name to number of args, (list of number of args because of overloading)
            else:
                self.funcToNumArgs[func.dict['name']] = [(len(func.dict['args']))]
                # self.funcNames[func.dict['name']] += 1
            # in the future, we only run main and set up the other functions, so we can run when needed
        
        if not foundMain:
            super().error(
            ErrorType.NAME_ERROR,
            "No main() function was found",
        )
            
        self.run_func(mainFunc)# run mainFunc

    def run_func(self, func):
        args = func.dict['args']
        arg_names = []
        for arg in args:
            var = arg.dict['name']
            arg_names.append(var)
        statements = func.dict['statements']

        for statement in statements:
            if statement.elem_type == 'return':
                return self.evaluate_node(statement.dict['expression'])
            else:
                res = self.run_statement(statement)
                if(res is not None):
                    return res
            # print(self.variables[-1])

        return nil



    
    def run_statement(self, statement):
        if statement.elem_type == '=':
            # assignment
            self.do_assignment(statement)
        elif statement.elem_type == 'fcall':
            # add currently defined variables to the next function
            # self.variables.append(self.variables[-1]) 
            # curr_func = self.functions[(statement.dict['name'], len(statement.dict['args']))]
            # arg_names = curr_func.dict['args']
            # arg_vals = statement.dict['args']
            # for i in range(len(arg_vals)): # get value and variable of each parameter, and pass it in
            #     arg_val = self.evaluate_node(arg_vals[i])
            #     arg_name = arg_names[i].dict['name']
            #     self.variables[-1][arg_name] = arg_val

            return self.evaluate_function(statement.dict['name'], statement.dict['args'])
            # self.variables.pop() # pop off stack

        elif statement.elem_type == 'if':
            new_vars = self.variables[-1].copy()
            self.variables.append(new_vars)
            retVal = self.evaluate_control(statement)
            curr_vars = self.variables[-1]
            self.variables.pop() # pop off stack
            for var in curr_vars:
                if var in self.variables[-1]: # if it was already defined then we update it
                    self.variables[-1][var] = curr_vars[var]
            return retVal

        elif statement.elem_type == 'while':
            new_vars = self.variables[-1].copy()
            self.variables.append(new_vars)
            retVal = self.evaluate_loop(statement)
            curr_vars = self.variables[-1]
            self.variables.pop() # pop off stack
            for var in curr_vars:
                if var in self.variables[-1]: # if it was already defined, then we update it
                    self.variables[-1][var] = curr_vars[var]
            return retVal
        
        # don't need to care about the return type here, because we return in the runFunc 

        return nil
            

        
    
    def evaluate_control(self, statement):
        isTrue = self.evaluate_node(statement.dict['condition'])
        if isinstance(isTrue, int):
            if(isTrue != 0):
                isTrue = True
            else:
                isTrue = False
        if not isinstance(isTrue, bool):
            super().error(
                    ErrorType.TYPE_ERROR,
                    "Expression was not a boolean",
                )
            
        if isTrue == True:
            # we go to if statement
            for s in statement.dict['statements']:
                if s.elem_type == 'return':
                    return self.evaluate_node(s.dict['expression'])
                else:
                    res = self.run_statement(s)# need to differentiate just in case we want to return nil on purpose
                    if(res is not None):
                        return res
        else:
            if statement.dict['else_statements'] is not None:
                for s in statement.dict['else_statements']:
                    if s.elem_type == 'return':
                        return self.evaluate_node(s.dict['expression'])
                    else:
                        res = self.run_statement(s)
                        if res is not None:
                            return res
                        
        return nil


    def evaluate_loop(self, statement):
        isTrue = self.evaluate_node(statement.dict['condition'])
        if isinstance(isTrue, int):
            if(isTrue != 0):
                isTrue = True
            else:
                isTrue = False
        if not isinstance(isTrue, bool):
            super().error(
                    ErrorType.TYPE_ERROR,
                    "Expression was not a boolean",
                )
        
        if isTrue == True:
            # we go to if statement
            for s in statement.dict['statements']:
                if s.elem_type == 'return':
                    return self.evaluate_node(s.dict['expression'])
                else:
                    res = self.run_statement(s)
                    if res is not None:
                        return res
            return self.evaluate_loop(statement) #re evaluate the statement to see if it's still true 
        
        return nil
            


        

    def do_assignment(self, statement):
        varName = statement.dict['name']
        expression = statement.dict['expression']
        # print(varName)
        # print(expression)
        evaluated = self.evaluate_node(expression)
        # print(evaluated)
        # if expression.elem_type == 'lambda':
        #     self.variables[-1][varName] = expression # lambda
        #     self.closures[varName] = self.variables[-1] # captures our current scope 


        self.variables[-1][varName] = evaluated #expression

        try: # see if we returned a lambda from another expression
            if evaluated.elem_type == 'lambda': # If it returns a lambda, then we can assign the new closure 
                # print("CHECK")
                # print(self.variables)
                self.variables[-1][varName] = (evaluated, self.variables[-1].copy())
                # print(self.variables[-1][varName])
                # self.closures[varName] = self.variables[-1].copy()
        except:
            pass
        
        try: # see if we returned a lambda from another expression
            if evaluated[0].elem_type == 'lambda': # If it returns a lambda, then we can assign the new closure 
                self.variables[-1][varName] = (evaluated[0], evaluated[1].copy())
                # self.closures[varName] = self.variables[-1].copy()
        except:
            pass

        if expression.elem_type == 'var' and isinstance(evaluated, tuple):
            # self.closures[varName] = self.closures[expression.dict['name']]
            self.variables[-1][varName] = evaluated
        if expression.elem_type == 'lambda': # for a lambda, we store a tuple with the closure and the associated lambda
            # self.closures[varName] = self.variables[-1].copy()

            self.variables[-1][varName] = (evaluated, self.variables[-1].copy())
        # print(self.variables)




        # elif expression.elem_type == 'var' and expression.dict['name'] in self.funcToNumArgs:


    
    def evaluate_function(self, name, args):
        # name is original name of the variable?
        funcName = name

        if funcName in self.variables[-1]: # if we assigned a variable to the function(and not lambda), we get that function
            funcName = self.variables[-1][funcName]

            try: # check if this is a function node or a function ,if we can successfully run this line, it's a function node, so we get the function name
                funcName = funcName.dict['name']
            except:
                pass
            # print(isinstance(funcName, tuple))

            # try:
            #     if funcName.elem_type == "lambda": # We pass in a lambda as a argument
            #         isLambda = True
            #     else:
            #         isLambda = False
            # except:
            #     isLambda = False
            if not isinstance(funcName, tuple) and funcName not in self.funcToNumArgs: # not a lambda or a function
                    
                super().error(
                ErrorType.TYPE_ERROR,
                "Not a function",
                )
        numArgs = len(args)
        # print(funcName)
        if funcName == "print":
            output_str = ""
            for s in args:
                temp_str = self.evaluate_node(s)
                if not (isinstance(temp_str, bool) or isinstance(temp_str, str) or isinstance(temp_str, int)):
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for print",
                )
                try:
                    if isinstance(temp_str, bool) and temp_str == True:
                        temp_str = "true"
                    elif isinstance(temp_str, bool) and temp_str == False:
                        temp_str = "false"
                    output_str += str(temp_str)
                except:
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for print",
                )
            super().output(output_str)

            return nil

        
        elif funcName == "inputi":
            if numArgs > 1:
                super().error(
                ErrorType.NAME_ERROR,
                f"No inputi() function found that takes > 1 parameter",
            )
            if numArgs == 1:
                output_str = self.evaluate_node(args[0])
                super().output(output_str)

            inputInt = super().get_input()
            inputInt = int(inputInt)

            return inputInt
        
        elif funcName == "inputs":
            if numArgs > 1:
                super().error(
                ErrorType.NAME_ERROR,
                f"No inputs() function found that takes > 1 parameter",
            )
            if numArgs == 1: # the input string
                output_str = self.evaluate_node(args[0])
                super().output(output_str)

            inputStr = super().get_input()

            return inputStr
        
        elif not isinstance(funcName, tuple) and (funcName, numArgs) in self.functions:
            # return value of the function
            new_vars = copy.deepcopy(self.variables[-1])
            curr_func = self.functions[(funcName, numArgs)]
            arg_names = curr_func.dict['args']
            check_arg_names = []
            arg_to_var = dict() # mapping from argName to original variable
            is_refArg = dict()
            arg_vals = args
            if len(arg_names) != len(arg_vals):
                super().error(
                ErrorType.TYPE_ERROR,
                "Wrong number of arguments",
            )
            for i in range(len(arg_vals)): # get value and variable of each parameter, and pass it in
                arg_val = self.evaluate_node(arg_vals[i])
                arg_name = arg_names[i].dict['name']
                if arg_vals[i].elem_type == 'var':
                    arg_to_var[arg_name] = arg_vals[i].dict['name']
                check_arg_names.append(arg_name)
                if arg_names[i].elem_type == 'refarg':
                    is_refArg[arg_name] = True
                else:
                    is_refArg[arg_name] = False
                new_vars[arg_name] = arg_val
                try:
                    if arg_val.elem_type == 'lambda': # We pass in a newly defined lambda NOT associated with a variable
                        new_vars[arg_name] = (arg_val, self.variables[-1].copy())
                except:
                    pass

            self.variables.append(new_vars)
 
  
            retVal = self.run_func(self.functions[(funcName, numArgs)])
            curr_vars = self.variables[-1]
            self.variables.pop() # pop off stack
            for var in curr_vars:
                if var in self.variables[-1] and (var not in check_arg_names): # if it was already defined and not a parameter, or a ref parameter, then we update it
                    self.variables[-1][var] = curr_vars[var]

                if var in is_refArg and is_refArg[var] == True and arg_to_var[var] in self.variables[-1]: # update the variable we passed into reference parameter
                    self.variables[-1][arg_to_var[var]] = curr_vars[var]

                    
            return retVal

        elif isinstance(funcName, tuple) and funcName[0].elem_type == 'lambda': # lambda function

            func = funcName[0]

            # new_vars = self.closures[name].copy()
            new_vars = funcName[1].copy()
            arg_names = func.dict['args'] 
            check_arg_names = []
            is_refArg = dict()
            arg_vals = args
            if len(arg_names) != len(arg_vals):
                super().error(
                ErrorType.TYPE_ERROR,
                "Wrong number of arguments",
            )
            arg_to_var = dict() # mapping from argName to original variable
            for i in range(len(arg_vals)): # get value and variable of each parameter, and pass it in
                arg_val = self.evaluate_node(arg_vals[i])
                arg_name = arg_names[i].dict['name']
                if arg_vals[i].elem_type == 'var':
                    arg_to_var[arg_name] = arg_vals[i].dict['name']
                check_arg_names.append(arg_name)
                if arg_names[i].elem_type == 'refarg':
                    is_refArg[arg_name] = True
                else:
                    is_refArg[arg_name] = False
                new_vars[arg_name] = arg_val
                try:
                    if arg_val.elem_type == 'lambda': # We pass in a newly defined lambda NOT associated with a variable
                        new_vars[arg_name] = (arg_val, self.variables[-1].copy())
                except:
                    pass

            self.variables.append(new_vars)
            retVal = self.run_func(func)
            curr_vars = self.variables[-1]
            self.variables.pop() # pop off stack
            # print(funcName[1])

            for var in curr_vars:
                if var in is_refArg and is_refArg[var] == True and arg_to_var[var] in  self.variables[-1]: # update the variable we passed into reference parameter
                    self.variables[-1][arg_to_var[var]] = curr_vars[var]
                    # print("check")
                # print(funcName[1][name])
                # we only want to update lambda scope if it was a ref argument
                self.variables[-1][name][1][var] = curr_vars[var]
                    # if(curr_vars[var])
            # print(self.closures[name] is self.variables[-1])
            # print(funcName)
            # update lambda closure
            # self.closures[name] = curr_vars
            return retVal

        # elif isLambda:
            # Lambda function that was passed in, but not previously defined 
        
        elif numArgs not in self.funcToNumArgs[funcName]:
            super().error(
                ErrorType.TYPE_ERROR,
                "Wrong number of arguments",
            )
        else:
            super().error(
                ErrorType.NAME_ERROR,
                "Undefined function",
            )
            
        



    def evaluate_node(self, node): # This function will get the value from a value/variable/expression node
        if node == None:
            return nil
        
        if node.elem_type == "lambda":
            return node
        
        if node.elem_type == 'var' and node.dict['name'] in self.funcToNumArgs:
            if len(self.funcToNumArgs[node.dict['name']]) > 1:
                super().error(
                ErrorType.NAME_ERROR,
                "Multiple functions with the same name",
            )
            funcName = node.dict['name']
            numArgs = self.funcToNumArgs[node.dict['name']][0]
            return self.functions[(funcName, numArgs)]
        
        if(node.elem_type == "int" or node.elem_type == "string" or node.elem_type == "bool"): # value node
            return node.dict['val']
        
        if(node.elem_type == 'nil'):
            return nil

        elif(node.elem_type == "var"): # variable node
            if node.dict['name'] in self.variables[-1]:
                return self.variables[-1][node.dict['name']]
            else:
                super().error(
                ErrorType.NAME_ERROR,
                f"Variable {node.dict['name']} has not been defined",
            )

        else: # expression node
            elem_type = node.elem_type

            # Add support for when we expect a boolean value(if/while statements, maybe add new function for them)

            if elem_type in self.op:
                op1 = self.evaluate_node(node.dict['op1'])
                op2 = self.evaluate_node(node.dict['op2'])
                # print(op1)
                # print(elem_type)
                # print(op2)
                if elem_type == "&&" or elem_type == "||":
                    if isinstance(op1, int):
                        if(op1!=0):
                            op1 = True
                        else:
                            op1 = False

                    if isinstance(op2, int):
                        if(op2!=0):
                            op2 = True
                        else:
                            op2 = False

                if (elem_type == '==' or elem_type == '!='):
                    if (isinstance(op1, int) and isinstance(op2, bool)):
                        if(op1!=0):
                            op1 = True
                        else:
                            op1 = False

                        return self.op[elem_type](op1,op2)
                    elif (isinstance(op1, bool) and isinstance(op2, int)):
                        if op2!=0:
                            op2 = True
                        else:
                            op2 = False

                        return self.op[elem_type](op1,op2)

                    

                    elif elem_type == '==' and type(op1) != type(op2): # if they're different types
                        return False
                    elif elem_type == '!=' and type(op1) != type(op2): # if they're different types
                        return True
                
                if elem_type in self.arithOps:
                    if (isinstance(op1, bool)):
                        if(op1):
                            op1 = 1
                        else:
                            op1 = 0
                        

                    elif (isinstance(op2, bool)):
                        if op2:
                            op2 = 1
                        else:
                            op2 = 0

                    try:    
                        return self.op[elem_type](op1,op2)
                    except:
                        super().error(
                        ErrorType.TYPE_ERROR,
                        "Incompatible types",
                        )

                if type(op1) != type(op2):
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types",
                    )
                
                # if type(op1) != type(op2):

                if elem_type == '+' and (isinstance(op1, str) and isinstance(op2, str)): # make sure don't throw an error on string addition
                    pass
                elif elem_type in self.arithOps and (not (isinstance(op1, int) and isinstance(op2, int))): # no non arithmetic operations
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types",
                    )

                if isinstance(op1, str) and isinstance(op2, str):
                    if elem_type not in self.stringOps:
                        super().error(
                        ErrorType.TYPE_ERROR,
                        "Incompatible types for strings",
                        )

                elif isinstance(op1, bool) and isinstance(op2, bool):
                    if elem_type not in self.boolOps:
                        super().error(
                        ErrorType.TYPE_ERROR,
                        "Incompatible types for bools",
                        )

                elif isinstance(op1, int) and isinstance(op2, int):
                    if elem_type not in self.intOps:
                        super().error(
                        ErrorType.TYPE_ERROR,
                        "Incompatible types for ints",
                        )

                # elif 

                try:
                    return self.op[elem_type](op1,op2)
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
            
            elif elem_type == '!':
                op1 = self.evaluate_node(node.dict['op1'])
                if isinstance(op1, int):
                    if op1 != 0:
                        op1 = True
                    else:
                        op1 = False
                elif not isinstance(op1, bool):
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for boolean not",
                    )

                try:
                    return not op1
                except:
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for boolean not",
                )

            elif elem_type == 'neg':
                op1 = self.evaluate_node(node.dict['op1'])
                if not isinstance(op1, int):
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for negation",
                    )

                try:
                    return -op1
                except:
                    super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible types for negation",
                )
            
            else:
                # parentFunc = self.curr_func[-1]
                # self.curr_func.append([node.dict['name'], len(node.dict['args'])])
                # add currently defined variables to the next function
                retval =  self.evaluate_function(node.dict['name'], node.dict['args'])
                # self.variables.pop()
                return retval
            
        

           
               


    
def main():
    interpreter = Interpreter()
    program1 = """
func main() {
  b = 5;
  f = lambda(a) { print(a*b); }; /* captures b = 5 by making a copy */
  b = 7;                         /* has no impact on captured b */

  f(3);     /* prints 15 */
}


"""

    interpreter.run(program1)


if __name__ == '__main__':
    main()
        
        

        
# FIX THIS TEST CASE
#         func foo(f1, ref f2) {
#   f1();  /* prints 1 */
#   f2();  /* prints 1 */
# }

# func main() {
#   x = 0;
#   lam1 = lambda() { x = x + 1; print(x); };
#   lam2 = lambda() { x = x + 1; print(x); };
#   foo(lam1, lam2);
#   lam1();  /* prints 1 */
#   lam2();  /* prints 2 */
# }