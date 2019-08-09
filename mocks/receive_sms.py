import sys
import time
import re
import argparse
import RPi.GPIO as GPIO
import serial

def send(command,s):
    s.write("{0}\r".format(command).encode())
    s.flush()
    response = ""
    time.sleep(1)
    while s.inWaiting():
        response = "{0}{1}".format(response,s.read_all().decode('latin-1'))
        time.sleep(1)
    #print(response)
    return response
    

def main():
    parser = argparse.ArgumentParser(prog=__name__,description='Simple SMS sender')
    parser.add_argument('--server', action="store", default="", dest="server_number")
    parser.add_argument('--pin', action="store", default="", dest="pin")
    parser.add_argument('--power', action="store_true", default=False, dest="power")

    incoming_re = re.compile(r'^\+CMGL:\ +(\d+),\"([^\"]*)\",\"([^\"]*)\"(,\"([^\"]*)\")?(,\"([^\"]+)\")?(,(\d+),(\d+))?\r?\n([^\r\n]+)\r?\n', re.MULTILINE)

    parsed_args = parser.parse_args()
    s = serial.Serial("/dev/ttyS0", 115200)
    print("Starting (please wait) ...")
    response = send("AT", s) #< check hat state
    if re.search("OK", response) == None: 
        if parsed_args.power: #power it if requiered
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(7, GPIO.OUT)
            while True:
                GPIO.output(7, GPIO.LOW)
                time.sleep(4)
                GPIO.output(7, GPIO.HIGH)
                break
            GPIO.cleanup()
            time.sleep(1)
        else:
            print("Hat error (perhapse not started)")
            return

    response = send("AT", s) #< check state again
    if re.search("OK", response) == None: 
        print("Hat error")
        return
    
    response = send("ATE0", s) #< remove command echo
    if re.search("OK", response) == None:
        print("Unable to set echo off")
        return
        
    response = send("AT+CPIN?",s) #< check pin
    if  re.search("SIM PIN",response): 
        if parsed_args.pin != "": #enter pin if requiered
            response = send("AT+CPIN={0}".format(parsed_args.pin),s)
            if re.search("SMS Ready",response) == None:
                print("Pin not accepted")
                return
        else:
            print("Pin requiered")
            return

    if parsed_args.server_number != "": #< check sms server setting
        server_number_command = 'AT+CSCA="{0}'.format(parsed_args.server_number)
        response = send(server_number_command, s)
        if re.search("OK", response) == None:
            print ("Server number setting failed")
            return

    response = send("AT+CNMI=2,0,0,0,0", s) #disable sms notification 
    if re.search("OK", response) == None:
        print("unable to remove TA notification")
        return
        
     
    response = send("AT+CMGF=1",s) #< set format to text
    if re.search("OK", response) == None:
        print("Text format not accepted")
        return
    
    print(" ... [done]\n")
    while True:
        response = send('AT+CMGL="ALL"', s)
        match = incoming_re.search(response, 0)
        ids = []
        while match != None:
            (__start, end) = match.span(0)
            id = match.group(1)
            ids.append(id)
            print("SMS Received : {0}".format(match.group(11)))
            match = incoming_re.search(response, end+1)
        for id in ids:
            response = send('AT+CMGD={0}'.format(id),s)
            if re.search("OK",response) == None:
                print("failed to delete : {0}".format(id))
        time.sleep(1)


if __name__ == "__main__":
    result = 0
    try:
        result = 1
        main()
    except Exception as e:
        print('Error: %s' % e, file=sys.stderr)
    sys.exit(result)