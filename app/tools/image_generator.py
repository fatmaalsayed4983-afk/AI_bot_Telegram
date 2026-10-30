import asyncio
import logging
import urllib.parse
import random
import requests

logger = logging.getLogger(__name__)


class ImageGeneratorTool:

    @staticmethod
    async def generate(
        prompt: str,
        width: int = 1024,
        height: int = 1024
    ) -> bytes:

        loop = asyncio.get_running_loop()

        def generate_image():

            encoded_prompt = urllib.parse.quote(prompt)

            seed = random.randint(1, 999999)

            url = (
                f"https://image.pollinations.ai/prompt/"
                f"{encoded_prompt}"
                f"?width={width}"
                f"&height={height}"
                f"&nologo=true"
                f"&seed={seed}"
            )

            logger.info(
                "Generating image using Pollinations..."
            )

            response = requests.get(
                url,
                timeout=60
            )

            if response.status_code == 200:

                if not response.content:
                    raise RuntimeError(
                        "Pollinations returned an empty image."
                    )

                return response.content

            raise RuntimeError(
                f"Pollinations API failure "
                f"(HTTP {response.status_code})"
            )

        try:

            image_bytes = await loop.run_in_executor(
                None,
                generate_image
            )

            logger.info(
                "Image generated successfully using Pollinations."
            )

            return image_bytes

        except Exception as e:

            logger.error(
                f"Pollinations image generation error: {e}"
            )

            raise