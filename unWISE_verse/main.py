import logging
from unWISE_verse import UserInterface
from unWISE_verse.Logger import Logger

if __name__ == "__main__":
    logger = Logger(console_output=False, include_timestamps=False, level=logging.INFO)
    logger.start()
    UI = UserInterface.UserInterface(logger=logger)
    logger.stop()
