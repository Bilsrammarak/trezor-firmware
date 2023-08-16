from trezorlib import messages
from trezorlib.debuglink import TrezorClientDebugLink as Client

from . import translations as TR
from .common import BRGeneratorType

B = messages.ButtonRequestType


class PinFlow:
    def __init__(self, client: Client):
        self.client = client
        self.debug = self.client.debug

    def setup_new_pin(
        self, pin: str, second_different_pin: str | None = None
    ) -> BRGeneratorType:
        yield  # Enter PIN
        assert "PinKeyboard" in self.debug.wait_layout().all_components()
        self.debug.input(pin)
        if self.debug.model == "R":
            yield  # Reenter PIN
            TR.assert_in(
                self.debug.wait_layout().text_content(), "pin.reenter_to_confirm"
            )
            self.debug.press_yes()
        yield  # Enter PIN again
        assert "PinKeyboard" in self.debug.wait_layout().all_components()
        if second_different_pin is not None:
            self.debug.input(second_different_pin)
        else:
            self.debug.input(pin)


class BackupFlow:
    def __init__(self, client: Client):
        self.client = client
        self.debug = self.client.debug

    def confirm_new_wallet(self) -> BRGeneratorType:
        yield
        TR.assert_in(self.debug.wait_layout().text_content(), "reset.by_continuing")
        if self.debug.model == "R":
            self.debug.press_right()
        self.debug.press_yes()


class RecoveryFlow:
    def __init__(self, client: Client):
        self.client = client
        self.debug = self.client.debug

    def _text_content(self) -> str:
        return self.debug.wait_layout().text_content()

    def confirm_recovery(self) -> BRGeneratorType:
        yield
        TR.assert_in(self._text_content(), "reset.by_continuing")
        if self.debug.model == "R":
            self.debug.press_right()
        self.debug.press_yes()

    def confirm_dry_run(self) -> BRGeneratorType:
        yield
        TR.assert_in(self._text_content(), "recovery.check_dry_run")
        self.debug.press_yes()

    def setup_slip39_recovery(self, num_words: int) -> BRGeneratorType:
        if self.debug.model == "R":
            yield from self.tr_recovery_homescreen()
        yield from self.input_number_of_words(num_words)
        yield from self.enter_any_share()

    def setup_bip39_recovery(self, num_words: int) -> BRGeneratorType:
        if self.debug.model == "R":
            yield from self.tr_recovery_homescreen()
        yield from self.input_number_of_words(num_words)
        yield from self.enter_your_backup()

    def tr_recovery_homescreen(self) -> BRGeneratorType:
        yield
        TR.assert_in(self._text_content(), "recovery.num_of_words")
        self.debug.press_yes()

    def enter_your_backup(self) -> BRGeneratorType:
        yield
        TR.assert_in(self._text_content(), "recovery.enter_backup")
        is_dry_run = any(
            title in self.debug.wait_layout().title()
            for title in TR.translate("recovery.title_dry_run")
        )
        if self.debug.model == "R" and not is_dry_run:
            # Normal recovery has extra info (not dry run)
            self.debug.press_right(wait=True)
            self.debug.press_right(wait=True)
        self.debug.press_yes()

    def enter_any_share(self) -> BRGeneratorType:
        yield
        TR.assert_in(self._text_content(), "recovery.enter_any_share")
        is_dry_run = any(
            title in self.debug.wait_layout().title()
            for title in TR.translate("recovery.title_dry_run")
        )
        if self.debug.model == "R" and not is_dry_run:
            # Normal recovery has extra info (not dry run)
            self.debug.press_right(wait=True)
            self.debug.press_right(wait=True)
        self.debug.press_yes()

    def abort_recovery(self, confirm: bool) -> BRGeneratorType:
        yield
        if self.debug.model == "R":
            TR.assert_in(self._text_content(), "recovery.num_of_words")
        else:
            TR.assert_in(self._text_content(), "recovery.enter_any_share")
        self.debug.press_no()

        yield
        TR.assert_in(self._text_content(), "recovery.wanna_cancel_recovery")
        if self.debug.model == "R":
            self.debug.press_right()
        if confirm:
            self.debug.press_yes()
        else:
            self.debug.press_no()

    def input_number_of_words(self, num_words: int) -> BRGeneratorType:
        br = yield
        assert br.code == B.MnemonicWordCount
        if self.debug.model == "R":
            TR.assert_in(self.debug.wait_layout().title(), "word_count.title")
        else:
            TR.assert_in(self._text_content(), "recovery.num_of_words")
        self.debug.input(str(num_words))

    def warning_invalid_recovery_seed(self) -> BRGeneratorType:
        br = yield
        assert br.code == B.Warning
        TR.assert_in(self._text_content(), "recovery.invalid_seed_entered")
        self.debug.press_yes()

    def warning_invalid_recovery_share(self) -> BRGeneratorType:
        br = yield
        assert br.code == B.Warning
        TR.assert_in(self._text_content(), "recovery.invalid_share_entered")
        self.debug.press_yes()

    def warning_group_threshold_reached(self) -> BRGeneratorType:
        br = yield
        assert br.code == B.Warning
        TR.assert_in(self._text_content(), "recovery.group_threshold_reached")
        self.debug.press_yes()

    def warning_share_already_entered(self) -> BRGeneratorType:
        br = yield
        assert br.code == B.Warning
        TR.assert_in(self._text_content(), "recovery.share_already_entered")
        self.debug.press_yes()

    def warning_share_from_another_shamir(self) -> BRGeneratorType:
        br = yield
        assert br.code == B.Warning
        TR.assert_in(self._text_content(), "recovery.share_from_another_shamir")
        self.debug.press_yes()

    def success_share_group_entered(self) -> BRGeneratorType:
        yield
        TR.assert_in(self._text_content(), "recovery.you_have_entered")
        self.debug.press_yes()

    def success_wallet_recovered(self) -> BRGeneratorType:
        br = yield
        assert br.code == B.Success
        TR.assert_in(self._text_content(), "recovery.wallet_recovered")
        self.debug.press_yes()

    def success_bip39_dry_run_valid(self) -> BRGeneratorType:
        br = yield
        assert br.code == B.Success
        TR.assert_in(self._text_content(), "recovery.dry_run_bip39_valid_match")
        self.debug.press_yes()

    def success_slip39_dryrun_valid(self) -> BRGeneratorType:
        br = yield
        assert br.code == B.Success
        TR.assert_in(self._text_content(), "recovery.dry_run_slip39_valid_match")
        self.debug.press_yes()

    def warning_slip39_dryrun_mismatch(self) -> BRGeneratorType:
        br = yield
        assert br.code == B.Warning
        TR.assert_in(self._text_content(), "recovery.dry_run_slip39_valid_mismatch")
        self.debug.press_yes()

    def warning_bip39_dryrun_mismatch(self) -> BRGeneratorType:
        br = yield
        assert br.code == B.Warning
        TR.assert_in(self._text_content(), "recovery.dry_run_bip39_valid_mismatch")
        self.debug.press_yes()

    def success_more_shares_needed(
        self, count_needed: int | None = None
    ) -> BRGeneratorType:
        yield
        # TODO: do this plural assert
        # assert (
        #     "1 more share needed" in self._text_content()
        #     or "More shares needed" in self._text_content()
        # )
        if count_needed is not None:
            assert str(count_needed) in self._text_content()
        self.debug.press_yes()

    def input_mnemonic(self, mnemonic: list[str]) -> BRGeneratorType:
        br = yield
        assert br.code == B.MnemonicInput
        assert "MnemonicKeyboard" in self.debug.wait_layout().all_components()
        for _, word in enumerate(mnemonic):
            # TODO: do this format assert
            # if self.debug.model == "R":
            #     assert f"WORD {index + 1}" in self.debug.wait_layout().title()
            # else:
            #     assert f"Type word {index + 1}" in self._text_content()
            self.debug.input(word)

    def input_all_slip39_shares(
        self,
        shares: list[str],
        has_groups: bool = False,
        click_info: bool = False,
    ) -> BRGeneratorType:
        for index, share in enumerate(shares):
            mnemonic = share.split(" ")
            yield from self.input_mnemonic(mnemonic)

            if index < len(shares) - 1:
                if has_groups:
                    yield from self.success_share_group_entered()
                if self.debug.model == "T" and click_info:
                    yield from self.tt_click_info()
                yield from self.success_more_shares_needed()

    def tt_click_info(
        self,
    ) -> BRGeneratorType:
        # Moving through the INFO button
        self.debug.press_info()
        yield
        self.debug.swipe_up()
        self.debug.press_yes()
