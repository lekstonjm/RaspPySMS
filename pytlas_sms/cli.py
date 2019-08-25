import cmd
import argparse
import shlex
from sms_service import SMSService
from pytlas import Agent, __version__
from pytlas.importers import import_skills
from pytlas.cli.utils import install_logs
import pytlas.settings as settings
import logging
import os

class AgentModel:
    def __init__(self, agent, phone_number, sms_service):
        self.agent = agent
        self.phone_number = phone_number
        self.sms_service = sms_service
        def handle_new_sms(emiter, **kw):
            self.on_new_sms(emiter, **kw)
        self.handle_new_sms = handle_new_sms
        self.sms_service.on_new_sms.connect(handle_new_sms)

    def on_new_sms(self, emiter, sender, date, message):        
        logging.info("receive message at {0} from {1}: {2}".format(date, sender, message))
        if sender == self.phone_number:
            self.agent.parse(message)
        else:
            logging.info("accept message from {0}".format(self.phone_number))


    def on_done(self, require_input):
        pass

    def on_ask(self, slot, text, choices, **meta):
        message = text
        if choices:
            for choice in choices:
                message = "{0}\n\t-{1}".format(message, choice) 
        logging.info("asking to {0}: {1}".format(self.phone_number, message))
        self.sms_service.send(self.phone_number, message)

    def on_answer(self, text, cards, **meta):
        message = text
        logging.info("answering to {0}: {1}".format(self.phone_number, message))
        self.sms_service.send(self.phone_number, message)

class Cli(cmd.Cmd):
    def __init__(self, sms_service, pytlas_agent):
        super(Cli,self).__init__()
        self.sms_service = sms_service
        self.pytlas_agent = pytlas_agent

    def do_exit(self, args):
        self.sms_service.stop()
        self.sms_service.join()
        return True
    
    def default(self, args):
        pass

def main():
    parser = argparse.ArgumentParser(prog=__name__,description='Simple SMS send_serialer')
    parser.add_argument('--phone', action="store", dest="phone_number")
    parser.add_argument('--server', action="store", default="", dest="server_number")
    parser.add_argument('--pin', action="store", default="", dest="pin")
    parser.add_argument('--power', action="store_true", default=False, dest="power")
    parser.add_argument('--pytlas_conf', action="store", default=settings.DEFAULT_FILENAME, dest="pytlas_conf")
    parsed_args = parser.parse_args()
    sms_service = SMSService(parsed_args.power, parsed_args.pin, parsed_args.server_number)

    print("initialisation (please wait) ... ")
    print("start sms service")
    sms_service.initialisation()
    sms_service.start()
    print("start pytlas service")
    settings.load(parsed_args.pytlas_conf)
    install_logs(settings.getbool(settings.SETTING_VERBOSE), settings.getbool(settings.SETTING_DEBUG))
    import_skills(settings.getpath(settings.SETTING_SKILLS), settings.getbool(settings.SETTING_WATCH))

    from pytlas.interpreters.snips import SnipsInterpreter
    interpreter = SnipsInterpreter(settings.get(settings.SETTING_LANG), settings.getpath(settings.SETTING_CACHE))
    training_file = settings.getpath(settings.SETTING_TRAINING_FILE)
    if training_file:
        interpreter.fit_from_file(training_file)
    else:
        interpreter.fit_from_skill_data()
    pytlas_agent = Agent(interpreter, transitions_graph_path=settings.getpath(settings.SETTING_GRAPH_FILE), **os.environ)

    model = AgentModel(pytlas_agent, parsed_args.phone_number, sms_service)
    pytlas_agent.model = model
    print(" ... done")

    cli = Cli(sms_service, pytlas_agent)

    cli.cmdloop()

if __name__ == "__main__":
    main()
