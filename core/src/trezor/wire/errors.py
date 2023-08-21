from trezor import translations as TR
from trezor.enums import FailureType


class Error(Exception):
    def __init__(self, code: FailureType, message: str) -> None:
        super().__init__()
        self.code = code
        self.message = message


class UnexpectedMessage(Error):
    def __init__(self, message: str) -> None:
        super().__init__(FailureType.UnexpectedMessage, message)


class ButtonExpected(Error):
    def __init__(self, message: str) -> None:
        super().__init__(FailureType.ButtonExpected, message)


class DataError(Error):
    def __init__(self, message: str) -> None:
        super().__init__(FailureType.DataError, message)


class ActionCancelled(Error):
    def __init__(self, message: str = TR.errors__cancelled) -> None:
        super().__init__(FailureType.ActionCancelled, message)


class PinExpected(Error):
    def __init__(self, message: str) -> None:
        super().__init__(FailureType.PinExpected, message)


class PinCancelled(Error):
    def __init__(self, message: str = TR.errors__pin_entry_cancelled) -> None:
        super().__init__(FailureType.PinCancelled, message)


class PinInvalid(Error):
    def __init__(self, message: str = TR.errors__pin_invalid) -> None:
        super().__init__(FailureType.PinInvalid, message)


class InvalidSignature(Error):
    def __init__(self, message: str) -> None:
        super().__init__(FailureType.InvalidSignature, message)


class ProcessError(Error):
    def __init__(self, message: str) -> None:
        super().__init__(FailureType.ProcessError, message)


class NotEnoughFunds(Error):
    def __init__(self, message: str) -> None:
        super().__init__(FailureType.NotEnoughFunds, message)


class NotInitialized(Error):
    def __init__(self, message: str) -> None:
        super().__init__(FailureType.NotInitialized, message)


class PinMismatch(Error):
    def __init__(self, message: str) -> None:
        super().__init__(FailureType.PinMismatch, message)


class WipeCodeMismatch(Error):
    def __init__(self, message: str) -> None:
        super().__init__(FailureType.WipeCodeMismatch, message)


class InvalidSession(Error):
    def __init__(self, message: str = TR.errors__invalid_session) -> None:
        super().__init__(FailureType.InvalidSession, message)


class FirmwareError(Error):
    def __init__(self, message: str) -> None:
        super().__init__(FailureType.FirmwareError, message)
