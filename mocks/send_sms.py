import serial
import time

s = serial.Serial("/dev/ttyS0", 115200)
s.write(b'AT\r\n')
s.flush()
time.sleep(1)
if s.inWaiting():
    print(s.read_all().decode('utf_8'))
s.write(b'AT+CMGS="+33649122408"\r\ntext\x1a\r\n')
time.sleep(1)
if s.inWaiting():
    print(s.read_all().decode('utf_8'))
