from IPython.core.debugger import set_trace

def state_from_program(program):
    return [int(e) for e in program.split(',')]

def get_intlist(integer):
    return [int(i) for i in list(str(integer))]

class machine:
    def __init__(self, program=None, inputs=None, 
                 return_output=False, verbose=True, reset_outputs = False):
        self.state = []
        self.head = 0
        self.__return_output = return_output
        self.__verbose = verbose
        self.__relative_base = 0
        self.__reset_outputs = reset_outputs
        
        if program is not None:
            self.state = state_from_program(program)

        self.__inputs = inputs

        if return_output:
            self.outputs = []

        self.__paused = False
        self.is_terminated = False

      
    def run(self):
        if self.is_terminated:
            print('Program has halted due to previous code 99 and cannot resume.')
        while not (self.__paused or self.is_terminated):
            self._opcode()
            
            # if self.state[self.head] == 99:
            if self._read_memory(self.head) == 99:
                if self.__verbose:
                    print('Code 99 received. Halting.')
                self.is_terminated = True
    
        if self.__return_output:
            if self.__reset_outputs:
                temp = self.outputs
                self.outputs = []
                return temp
            else:
                return self.outputs


    def input(self, inp):
        self.__inputs.append(inp)
        self.__paused = False

    def _read_memory(self, address, how = 'immediate'):
        
        if how == 'immediate':
            add = address
        elif how == 'positional':
            add = self._read_memory(address, how = 'immediate')
        elif how == 'relative':
            add = self._read_memory(address, how = 'immediate') + self.__relative_base
        else:
            raise ValueError('Unknown parameter mode for reading: {}'.format(how))

        try:
            return self.state[add]
        except IndexError:
            self._extend_memory(add)
            return self.state[add]

    def _write_memory(self, address, value, how = 'positional'):

        if how == 'immediate':
            raise ValueError('Cannot write in immediate mode!')
        elif how == 'positional':
            add = address
        elif how == 'relative':
            add = address + self.__relative_base
        else:
            raise ValueError('Unknown parameter mode for writing: {}'.format(how))

        try:
            self.state[add] = value
        except IndexError:
            self._extend_memory(add)
            self.state[add] = value

    def _extend_memory(self, address):
        if address < 0:
            raise IndexError('Cannot access negative memory address.')

        additional_memory = address - len(self.state) + 1
        self.state += [0] * additional_memory

    def _opcode(self):
        # make a list of integers that defines the opcode, namely where
        # the instruction pointer (head) points in the state
        code_seq = get_intlist(self._read_memory(self.head))
        # set_trace()

        # The actual opcode is the last digit
        code = code_seq[-1]
        
        # the various opcodes have different number of parameters, so the code str
        # will vary in length. We figure this out in order to be able to add a leading
        # zero if it is missing
        code_str_lengths = {1: 5,
                            2: 5, 
                            3: 3,
                            4: 3,
                            5: 4,
                            6: 4,
                            7: 5,
                            8: 5,
                            9: 3,
                        }
        # If we expect a longer code string than we get, we add leading zeros
        while (len(code_seq) < code_str_lengths[code]):
            code_seq = [0] + code_seq
        
        # part of the code signifies if the parameter type is positional, immediate
        # or relative
        parameter_map = {0: 'positional', 1: 'immediate', 2: 'relative'}
        
        
        # we figure out which parameters should be interpreted as what
        parameter_modes = [parameter_map[o] for o in reversed(code_seq[:-2])]
        
        # A mapping between op-codes and the functions we want to perform
        code_functions = {1: self._code_one, 
                 2: self._code_two,
                 3: self._code_three, 
                 4: self._code_four,
                 5: self._code_five,
                 6: self._code_six, 
                 7: self._code_seven,
                 8: self._code_eight,
                 9: self._code_nine,
                }
        
        
        # We determine which function to apply, from the code received
        code_func = code_functions[code]
        
        # Apply the function. The functions themselves are responsible for altering the state
        # of the machine and moving the instruction pointer (head) appropriately
        code_func(parameter_modes)
      
    def _code_one(self, parameter_modes):
        # Add parameter 1 and 2 and store it at parameter 3
        val1 = self._read_memory(self.head + 1, how=parameter_modes[0])
        val2 = self._read_memory(self.head + 2, how=parameter_modes[1])
        
        write_address = self._read_memory(self.head + 3)
        self._write_memory(write_address, val1 + val2, how=parameter_modes[2])

        self.head += 4
        
    def _code_two(self, parameter_modes):
        # # Multiply parameter 1 and 2 and store it at parameter 3
        val1 = self._read_memory(self.head + 1, how=parameter_modes[0])
        val2 = self._read_memory(self.head + 2, how=parameter_modes[1])
        
        write_address = self._read_memory(self.head + 3)
        self._write_memory(write_address, val1 * val2, how = parameter_modes[2])
        self.head += 4
        
    def _code_three(self, parameter_modes):    
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
            write_address = self._read_memory(self.head + 1)
            self._write_memory(write_address, val, how = parameter_modes[0])
            self.head += 2
        
    def _code_four(self, parameter_modes):
        # Only output the value given by the code's parameter
        output = self._read_memory(self.head+1, how=parameter_modes[0])

        if self.__return_output:
            self.outputs.append(output)      
        if self.__verbose:
            print('Output: {}'.format(output))
        self.head += 2
    
    def _code_five(self, parameter_modes):     
        # If parameter 1 is non-zero, set head at parameter 2
        val1 = self._read_memory(self.head + 1, how=parameter_modes[0])
        val2 = self._read_memory(self.head + 2, how=parameter_modes[1])

        if val1 != 0:
            self.head = val2
        else:
            self.head += 3
            
    def _code_six(self, parameter_modes):     
        # If parameter 1 is zero, set head at parameter 2
        val1 = self._read_memory(self.head + 1, how=parameter_modes[0])
        val2 = self._read_memory(self.head + 2, how=parameter_modes[1])
        
        if val1 == 0:
            self.head = val2
        else:
            self.head += 3
    
    def _code_seven(self, parameter_modes):
        # If parameter 1 is less than parameter 2, set 1 at parameter 3 else 0 
        val1 = self._read_memory(self.head + 1, how=parameter_modes[0])
        val2 = self._read_memory(self.head + 2, how=parameter_modes[1])

        write_address = self._read_memory(self.head + 3)
        self._write_memory(write_address, 1 if val1 < val2 else 0, how = parameter_modes[2])
        self.head += 4
    
    def _code_eight(self, parameter_modes):
        # If parameter 1 equals parameter 2, set 1 at parameter 3 else 0 
        val1 = self._read_memory(self.head + 1, how=parameter_modes[0])
        val2 = self._read_memory(self.head + 2, how=parameter_modes[1])

        write_address = self._read_memory(self.head + 3)
        self._write_memory(write_address, 1 if val1 == val2 else 0, how=parameter_modes[2])
        self.head += 4
    
    def _code_nine(self, parameter_modes):
        # increase/decrease the relative base by the code's parameter
        val = self._read_memory(self.head + 1, how=parameter_modes[0])
        self.__relative_base += val
        self.head += 2

    def __repr__(self):
        return '{}'.format(self.state)
