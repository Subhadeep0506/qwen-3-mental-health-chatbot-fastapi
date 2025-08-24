import os

from core.load_model import load_model


class State:
    history = []
    model, tokenizer = None, None

    def __init__(self):
        self.history = []
        # self.model, self.tokenizer = load_model(debug=os.getenv("DEBUG") == "1")