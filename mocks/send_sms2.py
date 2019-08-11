import sys
import time
import re
import argparse
import RPi.GPIO as GPIO
import serial


class SMSService:
    def __init__(self, power=False, pin="", sms_server="", serial_address = "/dev/ttyS0", speed = 115200, encoding="latin-1"):
        self.power = power
        self.pin = pin
        self.sms_server = sms_server
        self.encoding = encoding
        self.serial_address = serial_address
        self.speed = speed
        self.serial = serial.Serial(serial_address, speed)
        self.is_running = True
    
    def send_serial(self, command, completed_response = "", timeout = 5.0 ):
        self.serial.write("{0}\r".format(command).encode())
        self.serial.flush()
        response = ""
        #time.sleep(0.1)
        t0 = time.perf_counter()
        while re.search(completed_response, response) == None:
            while self.serial.inWaiting():
                response = "{0}{1}".format(response,self.serial.read_all().decode(self.encoding))
                time.sleep(0.1)
                if time.perf_counter() - t0 > timeout:
                    raise Exception("Timeout")
            time.sleep(0.1)
            if time.perf_counter() - t0 > timeout:
                raise Exception("Timeout")
        return response    

    def initialisation(self):
        self.serial = serial.Serial(self.serial_address, self.speed)            
        try:
            #print("Check serial")
            response = self.send_serial("AT", r"(OK|ERROR)") #< check hat state
        except Exception:
            if self.power: #power it if requiered
                #print("power")
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(7, GPIO.OUT)
                while True:
                    GPIO.output(7, GPIO.LOW)
                    time.sleep(4)
                    GPIO.output(7, GPIO.HIGH)
                    break
                GPIO.cleanup()
                time.sleep(1)
                response = self.send_serial("AT", r"(OK|ERROR)") #< check hat state
            else:
                raise Exception("Hat error (perhaps not powered)")
    
        if re.search(r"ERROR", response): 
            raise Exception("Hat error")
        
        #print("remove echo")
        response = self.send_serial("ATE0", r"(OK|ERROR)") #< remove command echo
        if re.search(r"ERROR", response):
            raise Exception("Unable to set echo off")
        
        response = self.send_serial("AT+CPIN?", r"(READY|SIM PIN|SIM PUK|PH_SIM PIN|PH_SIM PUK|SIM PIN2|ERROR|SIM PUK2)") #< check pin
        if  re.search("SIM PIN",response): #< pin requiered 
            #print("pin requiered")
            if self.pin != "": #< pin entered
                #print("pin entered")
                response = self.send_serial("AT+CPIN={0}".format(self.pin),r"(SMS Ready|ERROR)")
                if re.search("SMS Ready",response) == None:
                    raise Exception("Pin error")
            else:
                raise Exception("Pin requiered")
        elif re.search(r"READY", response) == None:
            raise Exception("Pin error {0}".format(response))
    
        if self.sms_server != "": #< set sms server setting
            #print("sms server setting")
            server_number_command = 'AT+CSCA="{0}'.format(self.sms_server)
            response = self.send_serial(server_number_command, r"(OK|ERROR)")
            if re.search("ERROR", response):
                raise Exception("SMS Server setting error")
    
        #print("disable sms notification")
        response = self.send_serial("AT+CNMI=2,0,0,0,0", r"(OK|ERROR)") #disable sms notification 
        if re.search("ERROR", response):
            raise Exception("unable to remove TA notification")
                     
        #print("set text format")
        response = self.send_serial("AT+CMGF=1",r"(OK|ERROR)") #< set format to text
        if re.search("ERROR", response):
            raise Exception("Text format not accepted")
    
    def send(self, phone_number, message):
        phone_number_command = 'AT+CMGS="{0}"'.format(phone_number)
        response = self.send_serial(phone_number_command, r">") 
        if re.search(">", response) == None:
            raise Exception("Phone number not accepted")
        
        text_command = "{0}\x1a".format(message)
        response = self.send_serial(text_command,r"(OK|ERROR)")
        if re.search("OK", response) == None:
            raise Exception("Unable to send sms")
     

def main():
    parser = argparse.ArgumentParser(prog=__name__,description='Simple SMS send_serialer')
    parser.add_argument('--server', action="store", default="", dest="server_number")
    parser.add_argument('--pin', action="store", default="", dest="pin")
    parser.add_argument('--power', action="store_true", default=False, dest="power")
    parser.add_argument('destination_number', action="store")
    parser.add_argument('text', action="store")

    parsed_args = parser.parse_args()

    sms_service = SMSService(parsed_args.power, parsed_args.pin, parsed_args.server_number)
    print("initialisation (please wait) ... ")
    sms_service.initialisation()
    print(" ... done")

    sms_service.send(parsed_args.destination_number, parsed_args.text)
    
if __name__ == "__main__":
    result = 0
    try:
        result = 1
        main()
    except Exception as e:
        print('Error: %s' % e, file=sys.stderr)
    sys.exit(result)