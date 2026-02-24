from __future__ import annotations

import base64


def openai_vision_extract(image_data: list[bytes], api_key: str, model: str = "gpt-4o") -> str:
    """Extract text from document images using OpenAI vision."""
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("openai package not installed; install with `.[ocr]`") from exc

    if not image_data:
        return ""

    client = OpenAI(api_key=api_key)
    content: list[dict[str, object]] = [
        {
            "type": "input_text",
            "text": (
                "Extract all visible document text. Preserve line breaks and key-value structure. "
                "Do not summarize or infer missing values."
            ),
        }
    ]
    for image in image_data:
        encoded = base64.b64encode(image).decode("ascii")
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:image/png;base64,{encoded}",
            }
        )

    response = client.responses.create(
        model=model,
        input=[{"role": "user", "content": content}],
    )
    return response.output_text.strip()
