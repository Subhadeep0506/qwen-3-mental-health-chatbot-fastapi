from pydantic import BaseModel


class PredictRequest(BaseModel):
    session_id: str
    model: str
    model_provider: str
    prompt: str
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 512
    debug: bool = False
