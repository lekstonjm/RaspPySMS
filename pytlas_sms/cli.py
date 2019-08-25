import cmd
import argparse
import shlex
from sms_service import SMSService

class Cli(cmd.Cmd):

    def __init__(self, sms_service):
        super(Cli,self).__init__()
        self.sms_service = sms_service
        def handle_new_sms(emiter, **kw):
            self.on_new_sms(emiter, **kw)
        self.handle_new_sms = handle_new_sms
        self.sms_service.on_new_sms.connect(handle_new_sms)
    
    def on_new_sms(self, emiter, sender, date, message):
        print("New message at {0} from {1}: {2}")

    def do_exit(self, args):
        self.sms_service.stop()
        self.sms_service.join()
        return True
    def do_send(self, args):
        parser = argparse.ArgumentParser(prog="send",description='Simple SMS sender')
        parser.add_argument('destination_number', action="store")
        parser.add_argument('text', action="store") 
        try:               
            parsed_args = parser.parse_args(shlex.split(args))
            self.sms_service.send(parsed_args.destination_number, parsed_args.text)
        except SystemExit:
            return


def main():
    parser = argparse.ArgumentParser(prog=__name__,description='Simple SMS send_serialer')
    parser.add_argument('--server', action="store", default="", dest="server_number")
    parser.add_argument('--pin', action="store", default="", dest="pin")
    parser.add_argument('--power', action="store_true", default=False, dest="power")
    parsed_args = parser.parse_args()
    sms_service = SMSService(parsed_args.power, parsed_args.pin, parsed_args.server_number)
    print("initialisation (please wait) ... ")
    sms_service.initialisation()
    print(" ... done")
    sms_service.start()
    cli = Cli(sms_service)
    cli.cmdloop()

if __name__ == "__main__":
    main()