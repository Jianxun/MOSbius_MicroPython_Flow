import json
import sys
import MOSbius

PIN_EN = 18
PIN_CLK = 17
PIN_DATA = 16

def main():

    if sys.implementation.name == 'micropython':
        from machine import Pin
        pin_en = Pin(PIN_EN,Pin.OUT)
        pin_clk = Pin(PIN_CLK,Pin.OUT)
        pin_data = Pin(PIN_DATA,Pin.OUT)

        chip = MOSbius.mosbius_mk1(pin_en, pin_clk, pin_data)  
    else:
        # Not running on MCU, program_bitstream will not work.
        chip = MOSbius.mosbius_mk1()



    # Select connections file
    #filename_connections = 'connections.json'
    filename_connections = 'ring_oscillator.json'
    
    with open(filename_connections,'r') as file:
        dict_connections = json.load(file)
        
    chip.create_bitstream(dict_connections)
    chip.export_bitstream_to_csv()
    
    #optional visualizations
    chip.print_connections()
    chip.display_connections()
    
    chip.program_bitstream()

if __name__ == "__main__":
    main()