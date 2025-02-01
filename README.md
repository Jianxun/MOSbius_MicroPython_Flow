# About
This project is the MicroPython workflow of the MOSbius chip (https://mosbius.org). 
Any MCU platform that is capable of running MicroPython can be used to program the MOSbius but Raspberry Pi Pico is recommended.

# Raspberry Pi Pico
Follow the official tutorials and install MicroPython firmware onto the Raspberry Pi Pico.
https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico

# Python IDE
You can use Thonny (https://thonny.org/), which is recommended by the official tutorial. This is beginner friendly IDE. You can easily move files between you computer and the RPi Pico.

If you are a more experienced Python user, and want a nicer IDE with code completion, you can use the VSCode + MicroPico plugin.
 
# Upload Files
`MOSbius.py`, `main.py`, and `connections.json` are essential files that need to be uploaded to the RPi Pico.

If you are using Thonny, right click them in the files window and select `Upload to /`
![](./screenshots/upload_files_to_rpi_pico.png)

If you are using VSCode + MicroPico, you can right click on the files and select `Upload file to Pico`, or `Upload project to Pico`.
![](./screenshots/upload_files_to_rpi_pico_vscode.png)

# Program MOSbius with the Raspberry Pi Pico
- Connect GPIO `10`, `11`, and `12` pins on the RPi Pico to the `EN`, `CLK` and `DATA` pins on the MOSBIUS PCB (top pins) and short the corresponding jumpers to the left. Feel free to use other GPIO pins by modifying the definitions in `main.py`.
- Connect the `LDO` and `GND` pins on the MOSbius PCB to the Raspberry Pi GND and 3.3V power pin.
- Below is an example setup with breadboards.
![](./screenshots/RPi_Pico_connections.png)

- Open `connections.json` from the device, edit and save the connections as needed. The default `connection.json` is a three-stage ring oscillator.
- Double click to open `main.py` from the device, click `Run current script`.
- The console will print out the connections and the bitstream, check them against your `connections.json` file.
![](./screenshots/programming_MOSbius.png)


# Running the flow on non-MicroPython hosts
The `main.py` script can detect if it is running on a MicroPython implementation. If not it will create the MOSbius object without valid GPIO pin configurations. You should be able to create a bitstream from a .json file and export it to `bitstream.csv`, which can be loaded into Scopy to program the MOSbius chip with an ADALM2000 if you don't have a RPI pico available.