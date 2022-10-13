import os

DEBUG_ENV = os.environ.get("VOCABSIEVE_DEBUG", "")
DEBUGGING = True if DEBUG_ENV else False