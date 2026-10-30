from abc import ABC, abstractmethod

class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, system_instruction: str, history: list, image_bytes: bytes = None, image_mime: str = None) -> str:
        pass

    @abstractmethod
    async def generate_image(self, prompt: str) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def get_capabilities(self) -> dict:
        pass
