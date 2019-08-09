import sys
import time
import re
import argparse
import RPi.GPIO as GPIO
import serial

def send(command,s):
    s.write("{0}\r\n".format(command).encode())
    s.flush()
    response = ""
    time.sleep(1)
    while s.inWaiting():
        response = "{0}{1}".format(response,s.read_all().decode('utf_8'))
        time.sleep(1)
    print(response)
    return response

def main():
    parser = argparse.ArgumentParser(prog=__name__,description='Simple SMS sender')
    parser.add_argument('--server', action="store", default="", dest="server_number")
    parser.add_argument('--pin', action="store", default="", dest="pin")
    parser.add_argument('--power', action="store_true", default=False, dest="power")
    parser.add_argument('destination_number', action="store")
    parser.add_argument('text', action="store")


    parsed_args = parser.parse_args()
    s = serial.Serial("/dev/ttyS0", 115200)

    response = send("AT", s)
    if re.search("OK", response) == None: 
        if parsed_args.power:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(7, GPIO.OUT)
            while True:
                GPIO.output(7, GPIO.LOW)
                time.sleep(4)
                GPIO.output(7, GPIO.HIGH)
                break
            GPIO.cleanup()
            time.sleep(1)
            response = send("AT", s)
            if re.search("OK", response) == None: 
                print("Hat error")
                return
        else:
            print("Hat error (perhapse not started)")
            return


    response = send("AT+CPIN?",s)
    if  re.search("SIM PIN",response): 
        if parsed_args.pin != "":
            response = send("AT+CPIN={0}".format(parsed_args.pin),s)
            if re.search("OK",response) == None:
                print("Pin not accepted")
                return
        else:
            print("Pin requiered")
            return

    if parsed_args.server_number != "":
        server_number_command = 'AT+CSCA="{0}'.format(parsed_args.server_number)
        response = send(server_number_command, s)
        if re.search("OK", response) == None:
            print ("Server number setting failed")
            return

    #set format to text
    response = send("AT+CMGF=1",s)
    if re.search("OK", response) == None:
        print("Text format not accepted")
        return
    
    phone_number_command = 'AT+CMGS="{0}"'.format(parsed_args.destination_number)
    response = send(phone_number_command, s) 
    if re.search(">", response) == None:
        print("Phone number not accepted")
        return
    
    text_command = "{0}\x1a".format(parsed_args.text)
    response = send(text_command,s)


if __name__ == "__main__":
    result = 0
    try:
        result = 1
        main()
    except Exception as e:
        print('Error: %s' % e, file=sys.stderr)
    sys.exit(result)
