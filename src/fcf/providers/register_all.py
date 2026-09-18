from fcf.providers.base import register
from fcf.providers.mock.image import MockImage
from fcf.providers.mock.llm import MockLLM
from fcf.providers.mock.tts import MockTTS
from fcf.providers.mock.video import MockVideo
from fcf.providers.mock.vision import MockVision


def register_defaults() -> None:
    register("llm", MockLLM())
    register("image", MockImage())
    register("tts", MockTTS())
    register("video", MockVideo())
    register("vision", MockVision())
