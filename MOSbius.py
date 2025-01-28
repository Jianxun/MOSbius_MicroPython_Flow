import time

class mosbius_mk1:
    NO_BUSES = 10
    NO_REGISTERS = 65
    
    T_CLK_HALF_CYCLE_US = 10
    

    VALID_PIN_ENUM = [1] + list(range(5,NO_REGISTERS+4))
    #pin 2,3,4 are used for programming, not connected to the matrix
    
    
    def __init__(self, pin_en=None, pin_clk=None, pin_data=None):

        self.bitstream = [0] * self.NO_BUSES * self.NO_REGISTERS 
        self.pin_en = pin_en
        self.pin_clk = pin_clk
        self.pin_data = pin_data
 
    
    def convert_pcb_pin_to_register(self,pin):
        if pin == 1:
            register = 1
        else:
            register = pin-3 #skip EN, CLK, and DATA pins
        return register

    def convert_register_to_pcb_pin(self,register):
        if register == 1:
            pin = 1
        else:
            pin = register + 3 #skip EN, CLK, and DATA pins
        return pin

    def create_bitstream(self, dict_connections):
        
        #print('Creating bitstream:')
        self.bitstream = [0] * self.NO_BUSES * self.NO_REGISTERS
        
        for bus in range(1,self.NO_BUSES+1):
            if f'{bus}' in dict_connections:
                pin_list = dict_connections[f'{bus}']
                #print(f'    BUS{bus}: {pin_list}')
            else:
                raise ValueError(f'JSON file error: missing bus entry {bus}.')
                
            for pin in pin_list:
                if  pin in self.VALID_PIN_ENUM:
                    register = self.convert_pcb_pin_to_register(pin)
                    bit_addr = (bus-1) * self.NO_REGISTERS + (register-1)
                    #print(bit_addr)
                    self.bitstream[bit_addr] = 1
                else:
                    raise ValueError(f'JSON file error: invalid MOSbius Pin Number {pin}.')

    def program_bitstream(self):
        print('Programming bitstream')
        
        if self.pin_en == None:
            print('Warning: GPIO pins not initialized. Abort programming.')
            return

        self.pin_data.value(0)
        self.pin_clk.value(0)
        self.pin_en.value(0)

        t_sleep_us = 100000

        
        for k in reversed(range(0,len(self.bitstream))):
            bit = self.bitstream[k]

            self.pin_data.value(bit)
                
            self.pin_clk.value(1)
            time.sleep_us(self.T_CLK_HALF_CYCLE_US)
            self.pin_clk.value(0)
            time.sleep_us(self.T_CLK_HALF_CYCLE_US)

        self.pin_en.value(1)
        print('Programming completed')
        
    def export_bitstream_to_csv(self):
        print('Exporting bitstream')

        with open("bitstream.csv", "w") as file:
            
            file.write('0,0,0\n')
        
            for k in reversed(range(0,len(self.bitstream))):
                bit = self.bitstream[k]

                file.write(f'0,1,{bit}\n')
                file.write(f'0,0,{bit}\n')

                
            file.write('1,0,0\n')
            
        print('Export completed')
        
    def display_connections(self):
        print('Connections:')
        print('    BUS    ', end='')
        for bus in range(1, self.NO_BUSES + 1):
            print(f'{bus} ', end='')
        print('')
        for register in range(1, self.NO_REGISTERS + 1):
            pin = self.convert_register_to_pcb_pin(register)
            print(f'    PIN {pin:02} ', end='')
            for bus in range(1, self.NO_BUSES + 1):
                bit_addr = (bus - 1) * self.NO_REGISTERS + (register - 1)
                #print(bitstream[bit_addr], end='')
                if self.bitstream[bit_addr]:
                    print('X ', end='')
                else:
                    print('| ', end='')
            print('')

    def print_connections(self):
        print('Connections:')
        for bus in range(1, self.NO_BUSES + 1):
            print(f'    BUS{bus}: [ ', end='')
            for register in range(1, self.NO_REGISTERS + 1):
                bit_addr = (bus - 1) * self.NO_REGISTERS + (register - 1)
                if self.bitstream[bit_addr]:
                    pin = self.convert_register_to_pcb_pin(register)
                    print(f'{pin:02} ', end='')
            print(']')            
