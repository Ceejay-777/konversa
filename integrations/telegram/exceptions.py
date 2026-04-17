class TelegramAPIError(Exception):
    pass


class TelegramRequestError(TelegramAPIError):
    pass


class TelegramResponseError(TelegramAPIError):
    pass