from loguru import logger
import threading


class SingletonLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, log_file="app.log"):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SingletonLogger, cls).__new__(cls)
                    cls._instance._init_logger(log_file)
        return cls._instance

    def _init_logger(self, log_file):
        logger.remove()  # Remove default console handler
        logger.add(
            log_file,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            rotation="10 MB",
            retention="10 days",
            enqueue=True,
        )
        self.logger = logger

    def get_logger(self):
        return self.logger