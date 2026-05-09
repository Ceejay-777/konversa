import requests
from django.conf import settings

from openrouter.errors import TooManyRequestsResponseError
from openrouter import OpenRouter

from .exceptions import CaptionBusinessError, CaptionInfrastructureError, CaptionRateLimitError

def build_prompt(product, seller_profile):
    return f"""
        You are a sales copywriter for small Nigerian social media businesses.
        You write captions that sound natural, simple, and human.
        Avoid overhyping. Avoid robotic marketing tone.
        Use simple words, easy to understand even for non-native speakers
        
        Seller style:
        {seller_profile or "Casual small business seller"}

        Here is the product:
        Name: {product.title}
        Description: {product.description}
        Price: ₦{product.price}
        Stock: {product.stock}

        Return a single caption (no title, no bullets).
        Length: 20-40 words. Lines: 2-4 lines
        Optional emoji only if natural. Seperate lines with new lines.
    """.strip()

def generate_caption(product, seller_profile=None):
    prompt = build_prompt(product, seller_profile)
    content = [{"type": "text", "text": prompt}]
    if product.image:
        content.append({"type": "image_url", "image_url": {"url": product.image.url}})

    try:
        with OpenRouter(api_key=settings.OPENROUTER_API_KEY) as client:
            response = client.chat.send(
                model="openrouter/free:gpt-3.5-turbo",
                messages=[{"role": "user", "content": content}]
            )
        
        caption = response.choices[0].message.content
        
        if not caption:
            raise CaptionBusinessError("AI returned empty caption.")

        if len(caption.strip()) < 5:
            raise CaptionBusinessError("Caption too short.")
        
        return caption, response.model
    
    except TooManyRequestsResponseError as exc:
        raise CaptionRateLimitError("OpenRouter rate limit exceeded.") from exc

    except CaptionBusinessError:
        raise

    except Exception as exc:
        raise CaptionInfrastructureError(f"Caption generation failed: {str(exc)}") from exc