import os


def load_model(debug=True):
    import torch

    torch.classes.__path__ = []
    model, tokenizer = None, None
    if not debug:
        from unsloth import FastLanguageModel

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name="./model/Qwen3-4B-Thinking-2507",
            max_seq_length=4096,
            dtype=None,
            load_in_4bit=True,
            load_in_8bit=False,
        )
        model.load_adapter("./model/best-cot-on-sft-ckpt")
        model = FastLanguageModel.for_inference(model)
    return model, tokenizer


def load_model_via_api(
    model_name: str,
    model_provider: str = "groq",
    max_tokens: int = 4096,
    temperature: float = 0.0,
):
    if model_provider == "groq":
        from langchain_groq.chat_models import ChatGroq

        model = ChatGroq(
            model=model_name,
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_format="raw",
        )

    return model, None
