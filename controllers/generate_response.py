from typing import List, Optional

from controllers.load_model import load_model_via_api

SYSTEM_PROMPT = """You are a medical assistant tasked with answering user queries in conversational setting, responsibly and in as much detail as possible. Your responses should demonstrate critical reasoning, clear observations, and structured insights.
You must respond in the following format:
<think>
...
</think>
<answer>
...
</answer>
Try to be assistive and detailed in your responses and respond to queries and follow-up to previous queries. If you are unsure of the answer, you should ask for clarification or say you don't know. Never make up an answer.
"""


def generate_response(
    images: Optional[List[str]],
    prompt: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    memory: List[dict],
    model,
    tokenizer: Optional[any],
    model_provider: Optional[str],
    debug=True,
):
    """
    Generate a response based on the provided image and prompt.

    Args:
        image (str): Path to the image file.
        prompt (str): Text prompt for the model.
        temperature (float): Sampling temperature.
        top_p (float): Top-p sampling parameter.
        max_tokens (int): Maximum number of tokens to generate.

    Returns:
        str: Generated response.
    """

    if not debug:
        if images:
            messages = (
                [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                ]
                + memory
                + [
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ]
            )
        else:
            messages = (
                [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                ]
                + memory
                + [
                    {"role": "user", "content": prompt},
                ]
            )
        if model_provider != "local":
            model, _ = load_model_via_api(
                model_name=model,
                model_provider=model_provider,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            response = model.invoke(messages).content
        else:
            import torch

            torch.classes.__path__ = []
            input_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=True,
            )
            # image_inputs, _ = process_vision_info(messages)
            inputs = tokenizer(
                input_text,
                return_tensors="pt",
                add_special_tokens=False,
            ).to("cuda")

            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    use_cache=True,
                    temperature=temperature,
                    min_p=top_p,
                )
            generated_ids_trimmed = [
                out_ids[len(in_ids) :]
                for in_ids, out_ids in zip(inputs.input_ids, outputs)
            ]
            decoded = tokenizer.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]
            response = decoded.replace(tokenizer.eos_token, "")
    else:
        response = "This is a mock response for debugging purposes."
        if images:
            messages = memory + [
                {
                    "role": "user",
                    "content": [
                        *[
                            {"type": "image", "image": f"data:image;base64,{image}"}
                            for image in images
                        ],
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
        else:
            messages = memory + [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ]
    messages.append(
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": response},
            ],
        }
    )
    return response, messages[-2:]  # Returns only the last user and assistant messages
    return response, messages[-2:]  # Returns only the last user and assistant messages
