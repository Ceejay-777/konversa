class CaptionGenerationError(Exception):
    pass


class CaptionBusinessError(CaptionGenerationError):
    pass


class CaptionInfrastructureError(CaptionGenerationError):
    pass


class CaptionRateLimitError(CaptionInfrastructureError):
    pass