import multiprocessing
import os
import pickle
from datetime import datetime
import logging
from logging.handlers import QueueHandler, QueueListener

class Logger:
    def __init__(self, log_file_path=None, include_timestamps=False, level=logging.INFO, console_output=True):

        if(log_file_path is None):
            if not os.path.exists("logs"):
                os.makedirs("logs")
            cwd = os.getcwd()
            log_file_path = cwd + "/logs/log-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".txt"

            # Create a log file or clear the existing one
            with open(log_file_path, "w") as log_file:
                log_file.write("")

        self.log_file_path = log_file_path
        self.include_timestamps = include_timestamps

        self.log_queue = multiprocessing.Queue()

        self.logger = logging.getLogger()
        self.logger.handlers = []

        console_handler = None
        if(console_output):
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(threadName)s: %(message)s')
            console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(self.log_file_path)

        if(console_output):
            self.queue_listener = QueueListener(self.log_queue, console_handler, file_handler)
        else:
            self.queue_listener = QueueListener(self.log_queue, file_handler)

        self.level_functions = {
            logging.DEBUG: self.logger.debug,
            logging.INFO: self.logger.info,
            logging.WARNING: self.logger.warning,
            logging.ERROR: self.logger.error,
            logging.CRITICAL: self.logger.critical,
            logging.FATAL: self.logger.fatal
        }

        self.level_names = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL",
            logging.FATAL: "FATAL"
        }

        self.level_values = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }

        self.updateLevel(level)

    def updateLevel(self, level):

        if (level is None):
            level = logging.INFO

        if (isinstance(level, str)):

            level = self.level_values.get(level.upper(), None)

            if(level is None):
                raise ValueError("Invalid logging level: " + str(level))

        self.logger.setLevel(level)
        self.logging_function = self.level_functions[level]

        if(self.logging_function is None):
            raise Exception("Invalid logging level: " + str(level))

    def start(self):
        self.queue_listener.start()

    def stop(self):
        self.queue_listener.enqueue_sentinel()
        self.queue_listener.stop()

    def log(self, message):

        file_handler = logging.FileHandler(self.log_file_path)
        self.logger.addHandler(file_handler)

        if (self.include_timestamps):
            message = str(self.level_names[self.logger.level]) + " " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + str(message)
        else:
            message = str(self.level_names[self.logger.level]) + " " + str(message)

        self.logging_function(message)
        self.logger.removeHandler(file_handler)

    def queue(self, message):
        record = logging.makeLogRecord({'msg': message})
        self.log_queue.put(record)


