
from IPython.core.debugger import set_trace


def state_from_program(program):
    return [int(e) for e in program.split(',')]

def get_intlist(integer):
    return [int(i) for i in list(str(integer))]

class machine:
    def __init__(self, program=None, inputs = None, return_output = False, verbose = True):
        self.state = []
        self.head = 0
        self.__return_output = return_output
        self.__verbose = verbose
        
        if program is not None:
            self.state = state_from_program(program)

        if inputs is not None:
            self.__inputs = inputs
        else:
            self.__inputs = None

        if return_output:
            self.outputs = []

        self.__paused = False
        self.is_terminated = False


      
    def run(self):
        if self.is_terminated:
            print('Program has halted and cannot resume.')
        while not (self.__paused or self.is_terminated):
            self._opcode()
            
            if self.state[self.head] == 99:
                if self.__verbose:
                    print('Termination criterion received. Halting.')
                self.is_terminated = True
    
        if self.__return_output:
            return self.outputs

    def input(self, inp):
        self.__inputs.append(inp)
        self.__paused = False
                
    def _opcode(self):
        # make a list of integers that defines the opcode, namely where
        # the instruction pointer (head) points in the state
        code_seq = get_intlist(self.state[self.head])
        
        # The actual opcode is the last digit
        code = code_seq[-1]
        
        # the various opcodes have different number of parameters, so the code str
        # will vary in length. We figure this out in order to be able to add a leading
        # zero if it is missing
        code_str_lengths = {1: 5,
                            2: 5, 
                            3: 1,
                            4: 1,
                            5: 4,
                            6: 4,
                            7: 5,
                            8: 5,
                        }
        # If we expect a longer code string than we get, we add leading zeros
        while (len(code_seq) < code_str_lengths[code]):
            code_seq = [0] + code_seq
        
        # part of the code signifies if the parameter type is position or immediate
        parameter_map = {0: 'pos', 1: 'imm'}
        
        # we figure out which parameters should be interpreted as what
        par_types = [parameter_map[o] for o in reversed(code_seq[:-2])]
        
        # A mapping between op-codes and the functions we want to perform
        code_functions = {1: self._code_one, 
                 2: self._code_two,
                 3: self._code_three, 
                 4: self._code_four,
                 5: self._code_five,
                 6: self._code_six, 
                 7: self._code_seven,
                 8: self._code_eight,
                }
        
        # Some of the opcodes will require additional arguments, we can put them here.
        # This seems more future-proof than a boolean
        function_args = {1: {'par_types': par_types},
                         2: {'par_types': par_types},
                         3: {},
                         4: {},
                         5: {'par_types': par_types},
                         6: {'par_types': par_types},
                         7: {'par_types': par_types},
                         8: {'par_types': par_types},
                        }
        
        # We determine which function to apply, from the code received
        code_func = code_functions[code]
        # What are the arguments we should provide?
        args = function_args[code]
        
        # Apply the function. The functions themselves are responsible for altering the state
        # of the machine and moving the instruction pointer (head) appropriately
        code_func(**args)
    
    def _interpret_parameters(self, par_types, give_address=False):
        # Opcodes have parameters sometimes, and this function gives values for those
        # depending on if they are positional or immediate (this information is stored
        # in the input par_types)
        state = self.state
        head = self.head
        
        # If we have immediate parameter type, we select the value in the state at the 
        # parameter position. Otherwise, we have positional parameter type and we select
        # the value in the state at the address given by the parameter 
        val1 = (state[head+1] if par_types[0] is 'imm' else state[state[head+1]])
        val2 = (state[head+2] if par_types[1] is 'imm' else state[state[head+2]])
        
        # If we have a third parameter, it has so far been an address to put the result
        # If we want this, we return it
        if give_address:
            address = state[head+3]
            return val1, val2, address
        else:
            return val1, val2
    
    
    def _code_one(self, par_types):
        # Add parameter 1 and 2 and store it at parameter 3
        # set_trace()
        val1, val2, address = self._interpret_parameters(par_types, give_address=True)
        try:
            self.state[address] = val1 + val2
        except TypeError as e:
            set_trace()
            print(e)
        self.head += 4
        
    def _code_two(self, par_types):
        # Multiply parameter 1 and 2 and store it at parameter 3
        val1, val2, address = self._interpret_parameters(par_types, give_address=True)
        self.state[address] = val1 * val2
        self.head += 4
        
    def _code_three(self):    
        # Take an input number and store it at the address given by
        # parameter 1
        if self.__inputs == []:
            self.__paused = True
        else:
            if self.__inputs is None:
                while True:
                    try:
                        val = int(input("Enter an integer: "))
                    except ValueError:
                        print('Give a number!')
                        continue
                    break
            else:
                val = self.__inputs.pop(0)

            address = self.state[self.head+1]
            self.state[address] = val
            self.head += 2
        
    def _code_four(self):
        # Only output the value stored positionally at the code's 
        # parameter
        address = self.state[self.head+1]
        output = self.state[address]
        if self.__return_output:
            self.outputs.append(output)      
        if self.__verbose:
            print('Output: {}'.format(output))
        self.head += 2
    
    def _code_five(self, par_types):     
        # If parameter 1 is non-zero, set head at parameter 2
        val1, val2 = self._interpret_parameters(par_types, give_address=False)
        if val1 != 0:
            self.head = val2
        else:
            self.head += 3
            
    def _code_six(self, par_types):     
        # If parameter 1 is zero, set head at parameter 2
        val1, val2 = self._interpret_parameters(par_types, give_address=False)
        if val1 == 0:
            self.head = val2
        else:
            self.head += 3
    
    def _code_seven(self, par_types):
        # If parameter 1 is less than parameter 2, set 1 at parameter 3 else 0 
        val1, val2, address = self._interpret_parameters(par_types, give_address=True)
        self.state[address] = 1 if val1 < val2 else 0
        self.head += 4
    
    def _code_eight(self, par_types):
        # If parameter 1 equals parameter 2, set 1 at parameter 3 else 0 
        val1, val2, address = self._interpret_parameters(par_types, give_address=True)
        self.state[address] = 1 if val1 == val2 else 0
        self.head += 4
    
    def __repr__(self):
        return '{}'.format(self.state)
        