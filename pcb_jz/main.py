from machine import Pin, I2C
import mcp23017

import json
import sys
import MOSbius


from ssd1306 import SSD1306_I2C
import framebuf



PIN_EN = 18
PIN_CLK = 17
PIN_DATA = 16

def display():

    WIDTH  = 128                                            # oled display width
    HEIGHT = 32                                             # oled display height

    i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq=200000)       # Init I2C using pins GP8 & GP9 (default I2C0 pins)
    print("I2C Address      : "+hex(i2c.scan()[0]).upper()) # Display device address
    print("I2C Configuration: "+str(i2c))                   # Display I2C config


    oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)                  # Init oled display

    # Raspberry Pi logo as 32x32 bytearray
    buffer = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00|?\x00\x01\x86@\x80\x01\x01\x80\x80\x01\x11\x88\x80\x01\x05\xa0\x80\x00\x83\xc1\x00\x00C\xe3\x00\x00~\xfc\x00\x00L'\x00\x00\x9c\x11\x00\x00\xbf\xfd\x00\x00\xe1\x87\x00\x01\xc1\x83\x80\x02A\x82@\x02A\x82@\x02\xc1\xc2@\x02\xf6>\xc0\x01\xfc=\x80\x01\x18\x18\x80\x01\x88\x10\x80\x00\x8c!\x00\x00\x87\xf1\x00\x00\x7f\xf6\x00\x008\x1c\x00\x00\x0c \x00\x00\x03\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")

    # Load the raspberry pi logo into the framebuffer (the image is 32x32)
    fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB)

    # Clear the oled display in case it has junk on it.
    oled.fill(0)

    # Blit the image from the framebuffer to the oled display
    #oled.blit(fb, 96, 0)

    # Add some text
    oled.text("MOSbius",5,5)
    oled.text("",5,15)

    # Finally update the oled display so the image & text is displayed
    oled.show()

def main():

    if sys.implementation.name == 'micropython':
        from machine import Pin
        
        i2c_0 = I2C(0,scl=Pin(13), sda=Pin(12))
        mcp = mcp23017.MCP23017(i2c_0, 0x21)

        mcp.pin(8, mode=0)
        mcp.pin(9, mode=0)
        mcp.pin(10, mode=0)
        
        pin_en = mcp[8]
        pin_clk = mcp[9]
        pin_data = mcp[10]
        

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
    #chip.export_bitstream_to_csv()
    
    #optional debugging information
    chip.print_connections()
    chip.display_connections()
    
    chip.program_bitstream()

    display()


if __name__ == "__main__":
    main()