from core.logger import SingletonLogger


class SingletonMeta(type):
    """A metaclass for creating singleton classes."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class State(metaclass=SingletonMeta):
    model, tokenizer = None, None
    logger = SingletonLogger().get_logger()
