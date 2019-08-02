import serial
import time

def read(s):
    data = ""
    while s.inWaiting():
        data += s.read_all()
    return data
s = serial.Serial("/dev/ttyS0", 115200)
s.write(b'AT\r\n')
s.flush()
time.sleep(1)
print(read(s))

