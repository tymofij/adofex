import time
from transifex.txcommon.log import logger

class TimeoutException(Exception):
    def __init__(self, command, stderr=None):
        self.stderr = stderr
        self.command = command

    def __str__(self):
        return repr("%s : %s" %
                    (str(self.command), self.stderr))

class Timer:
    """Utility class for measuring task executions

    This class has the following data attributes:
        self.duration : the wall time taken for the task
        self.cpu_duration : the time of CPU processing
    """

    def __init__(self, name="N/A", description="N/A"):
        self.name = name
        self.description = description

    def start(self):
        """Start the timers."""
        self._t0 = time.clock()
        self._t1 = time.time()

    def stop(self):
        """Stop the timers."""
        self.duration = time.time() - self._t1
        self.cpu_duration = time.clock() - self._t0

    def log(self):
        """Write timer values to tx logger."""
        logger.debug("Computing timer task \"%s\", task description : %s" %
            (self.name, self.description))
        logger.info("Timer Task \"%s\" Duration : %.3fsec (CPU %.3f)" %
                    (self.name, self.duration, self.cpu_duration))

    def __str__(self):
        return "%.3f" % self.duration
