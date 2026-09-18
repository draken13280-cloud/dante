from fcf.providers.base import BinaryResult, Usage, VideoRequest


class KenBurnsVideo:
    name = "ffmpeg_kenburns"

    def estimate_cost(self, req) -> int:
        return 0

    async def generate(self, req: VideoRequest) -> BinaryResult:
        from fcf.providers.mock.video import MockVideo

        return await MockVideo().generate(req)
