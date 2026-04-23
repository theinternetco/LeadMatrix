# app/services/ai_image.py
import os
import logging

logger = logging.getLogger("ai_image")


def generate_post_image(prompt: str, business_id: int) -> str:
    """
    Generate an AI image for a GMB post.
    Replace the body below with your real AI image API call.

    Upgrade options:
      - Stability AI: pip install stability-sdk
      - Replicate FLUX.1: pip install replicate
      - OpenAI DALL-E 3: pip install openai
    """
    # ── Stability AI (uncomment when STABILITY_API_KEY is set) ───────────────
    # import requests, base64
    # api_key = os.getenv("STABILITY_API_KEY")
    # if not api_key:
    #     raise ValueError("STABILITY_API_KEY not set in environment")
    # r = requests.post(
    #     "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
    #     headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    #     json={"text_prompts": [{"text": prompt}], "width": 1024, "height": 1024, "samples": 1},
    #     timeout=30,
    # )
    # b64 = r.json()["artifacts"][0]["base64"]
    # return f"data:image/png;base64,{b64}"

    # ── Replicate FLUX.1 (uncomment when REPLICATE_API_TOKEN is set) ─────────
    # import replicate
    # output = replicate.run(
    #     "black-forest-labs/flux-schnell",
    #     input={"prompt": prompt, "num_outputs": 1}
    # )
    # return output[0]

    # ── Picsum placeholder (active by default — no API key needed) ───────────
    seed = abs(hash(prompt + str(business_id))) % 9999
    url  = f"https://picsum.photos/seed/{seed}/800/600"
    logger.info("ai_image placeholder: seed=%s url=%s", seed, url)
    return url