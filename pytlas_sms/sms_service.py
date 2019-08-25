import sys
import time
import threading
import re
import RPi.GPIO as GPIO
import serial
import re
import blinker


class SMSService(threading.Thread):
    def __init__(self, power=False, pin="", sms_server="", serial_address = "/dev/ttyS0", speed = 115200, encoding="latin-1"):
        super(SMSService,self).__init__()
        self.power = power
        self.pin = pin
        self.sms_server = sms_server
        self.encoding = encoding
        self.serial_address = serial_address
        self.speed = speed
        self.serial = serial.Serial(serial_address, speed)
        self.is_running = True
        self.incoming_re = re.compile(r'^\+CMGL:\ +(\d+),\"([^\"]*)\",\"([^\"]*)\"(,\"([^\"]*)\")?(,\"([^\"]+)\")?(,(\d+),(\d+))?\r?\n([^\r\n]+)\r?\n', re.MULTILINE)
        self.new_message = False
        self.on_new_sms = blinker.Signal()
    
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

    def do_send(self):
        phone_number = self.phone_number
        message = self.message
        self.new_message = False
        phone_number_command = 'AT+CMGS="{0}"'.format(phone_number)
        response = self.send_serial(phone_number_command, r">") 
        if re.search(">", response) == None:
            raise Exception("Phone number not accepted")
        
        text_command = "{0}\x1a".format(message)
        response = self.send_serial(text_command,r"(OK|ERROR)")
        if re.search("OK", response) == None:
            raise Exception("Unable to send sms")
    
    def check_receive(self):
        response = self.send_serial('AT+CMGL="ALL"', r"(OK|ERROR)")
        match = self.incoming_re.search(response, 0)
        ids = []
        while match != None:
            (__start, end) = match.span(0)
            id = match.group(1)
            ids.append(id)
            sender=match.group(2)
            date=match.group(3)
            message=match.group(11)
            self.on_new_sms.send(self, sender=sender, date=date, message=message)
            match = self.incoming_re.search(response, end+1)
        for id in ids:
            response = self.send_serial('AT+CMGD={0}'.format(id),"(OK|ERROR)")
            #if re.search("OK",response) == None:
            #    print("failed to delete : {0}".format(id))
        time.sleep(0.1)

    def run(self):
        while self.is_running:
            self.check_receive()
            if (self.new_message):
                self.do_send()
            time.sleep(0.1)

    def stop(self):
        self.is_running = False

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
        self.phone_number = phone_number
        self.message = message
        self.new_message = True      
