import serial
import datetime
import threading
import time

ser = serial.Serial('/dev/cu.usbserial-A9ADVKYL', baudrate=9600, timeout=1, parity=serial.PARITY_NONE, bytesize=8, stopbits=serial.STOPBITS_ONE, xonxoff=False)

def Read_from_port(ser,rommon_event ,image_event, prompt_event, switch_break_event):
    line_buffer = ""
    while ser.is_open == True:
        if ser.in_waiting > 0:
            chunk = ser.read(ser.in_waiting).decode("utf-8",errors = "ignore")
            line_buffer += chunk
            lines = line_buffer.split("\n")
            for line in lines[:-1]:

                if "rommon" in line:
                    rommon_event.set()

                if "Rom image verified correctly" in line:
                    image_event.set()

                if "Send break" in line:
                    switch_break_event.set()

                if "Press RETURN to get started!" in line:
                    prompt_event.set()

                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"{timestamp} {line}")
            line_buffer = lines[-1]

switch_break_reached = threading.Event()
prompt_reached = threading.Event()
image_reached = threading.Event()
rommon_reached = threading.Event()
threading.Thread(target=Read_from_port, args=(ser, rommon_reached, image_reached, prompt_reached, switch_break_reached), daemon=True).start()

while not switch_break_reached.is_set() or not image_reached.is_set():
    if switch_break_reached.is_set():
        ser.send_break()
        break
    elif image_reached.is_set():
        ser.send_break()
        if rommon_reached.is_set():
            break

if switch_break_reached.is_set():
    time.sleep(3)
    ser.write(bytes(str(f"delete flash:config.text"), 'ISO-8859-1\r\n'))
    time.sleep(1)
    ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
    time.sleep(1)
    ser.write(bytes(str(f"y\r"), 'ISO-8859-1'))
    time.sleep(1)
    ser.write(bytes(str(f"delete flash:vlan.dat\r"), 'ISO-8859-1'))
    time.sleep(1)
    ser.write(bytes(str(f"y\r"), 'ISO-8859-1'))
    time.sleep(1)
    ser.write(bytes(str(f"boot\r"), 'ISO-8859-1'))

else:
    ser.write(bytes(str(f"confreg 0x2142\r"), 'ISO-8859-1'))
    ser.write(bytes(str(f"reset\r"), 'ISO-8859-1'))

while True:
    if prompt_reached.is_set() and not switch_break_reached.is_set():
        ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"en\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"erase startup-config\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"conf t\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"config-register 0x2102\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"do wr\r"), 'ISO-8859-1'))
        break
    elif prompt_reached.is_set() and switch_break_reached.is_set():
        ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"no\r"), 'ISO-8859-1'))
        ser.write(bytes(str(f"\r"), 'ISO-8859-1'))
        break

while True:
    ser.write(bytes(str(f"{input()}\r"), "ISO-8859-1"))
