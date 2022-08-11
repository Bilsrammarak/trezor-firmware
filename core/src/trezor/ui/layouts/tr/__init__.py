from typing import TYPE_CHECKING, Sequence

from trezor import io, log, loop, ui, wire, workflow
from trezor.enums import ButtonRequestType
from trezor.ui.popup import Popup

import trezorui2

from ...components.tr.text import Text
from ..common import button_request, interact

if TYPE_CHECKING:
    from typing import Any, NoReturn, Type, Awaitable, Iterable, TypeVar

    from ..common import PropertyType

    T = TypeVar("T")

    ExceptionType = BaseException | Type[BaseException]


# TODO: could create object holding all the data - text, title, btn_actions...


class RustLayoutContent:
    """Providing shortcuts to the data returned by layouts.

    Used only in debug mode.
    """

    # How will some information be identified in the content
    TITLE_TAG = " **TITLE** "
    CONTENT_TAG = " **CONTENT** "
    BTN_TAG = " **BTN** "
    EMPTY_BTN = "---"

    def __init__(self, raw_content: list[str]) -> None:
        self.raw_content = raw_content
        self.str_content = " ".join(raw_content).replace("  ", " ")
        # print("str_content", self.str_content)
        print(60 * "-")
        print("active_page:", self.active_page())
        print("page_count:", self.page_count())
        print("can_go_next:", self.can_go_next())
        print("get_next_button:", self.get_next_button())
        print(30 * "/")
        print(self.visible_screen())

    def active_page(self) -> int:
        """Current index of the active page."""
        return int(self.kw_pair("active_page"))

    def page_count(self) -> int:
        """Overall number of pages in this flow."""
        return int(self.kw_pair("page_count"))

    def can_go_next(self) -> bool:
        """Checking if there is a next page."""
        return self.get_next_button() != ""

    def get_next_button(self) -> str:
        """Position of the next button, if any."""
        btn_names = ("left", "middle", "right")
        for index, action in enumerate(self.button_actions()):
            if action == "Next":
                return btn_names[index]

        return ""

    def visible_screen(self) -> str:
        """Getting all the visible screen content - header, content, buttons."""
        title_separator = f"\n{20*'-'}\n"
        btn_separator = f"\n{20*'*'}\n"

        visible = ""
        if self.title():
            visible += self.title()
            visible += title_separator
        visible += self.content()
        visible += btn_separator
        visible += ", ".join(self.buttons())

        return visible

    def title(self) -> str:
        """Getting text that is displayed as a title."""
        # there could be multiple of those - title and subtitle for example
        title_strings = self._get_strings_inside_tag(self.str_content, self.TITLE_TAG)
        return "\n".join(title_strings)

    def content(self) -> str:
        """Getting text that is displayed in the main part of the screen."""
        content_strings = self._get_strings_inside_tag(
            self.str_content, self.CONTENT_TAG
        )
        # there are some unwanted spaces
        strings = [s.replace("\n ", "\n").lstrip() for s in content_strings]
        return "\n".join(strings)

    def buttons(self) -> tuple[str, str, str]:
        """Getting content and actions for all three buttons."""
        contents = self.buttons_content()
        actions = self.button_actions()
        return tuple(f"{contents[i]} [{actions[i]}]" for i in range(3))

    def buttons_content(self) -> tuple[str, str, str]:
        """Getting visual details for all three buttons."""
        btns = self._get_strings_inside_tag(self.str_content, self.BTN_TAG)
        assert len(btns) == 3
        return btns[0], btns[1], btns[2]

    def button_actions(self) -> tuple[str, str, str]:
        """Getting actions for all three buttons."""
        action_ids = ("left_action", "middle_action", "right_action")
        return tuple(self.kw_pair(action) for action in action_ids)

    def kw_pair(self, key: str) -> str:
        """Getting the value of a key-value pair."""
        # Pairs are sent in this format in the list:
        # [..., "key", "::", "value", ...]
        for key_index, item in enumerate(self.raw_content):
            if item == key:
                if self.raw_content[key_index + 1] == "::":
                    return self.raw_content[key_index + 2]

        return ""

    @staticmethod
    def _get_strings_inside_tag(string: str, tag: str) -> list[str]:
        """Getting all strings that are inside two same tags."""
        parts = string.split(tag)
        if len(parts) == 1:
            return []
        else:
            # returning all odd indexes in the list
            return parts[1::2]


class RustLayout(ui.Layout):
    # pylint: disable=super-init-not-called
    def __init__(self, layout: Any):
        self.layout = layout
        self.timer = loop.Timer()

    def set_timer(self, token: int, deadline: int) -> None:
        self.timer.schedule(deadline, token)

    if __debug__:

        def create_tasks(self) -> tuple[loop.AwaitableTask, ...]:  # type: ignore [obscured-by-same-name]
            from apps.debug import confirm_signal, input_signal

            return (
                self.handle_input_and_rendering(),
                self.handle_timers(),
                confirm_signal(),
                input_signal(),
            )

        def read_content(self) -> list[str]:
            result: list[str] = []

            def callback(*args: str):
                for arg in args:
                    result.append(str(arg))

            self.layout.trace(callback)
            return result

    else:

        def create_tasks(self) -> tuple[loop.Task, ...]:
            return self.handle_timers(), self.handle_input_and_rendering()

    def _before_render(self) -> None:
        # Clear the screen of any leftovers.
        ui.backlight_fade(ui.style.BACKLIGHT_DIM)
        ui.display.clear()

        if __debug__ and self.should_notify_layout_change:
            from apps.debug import notify_layout_change

            # notify about change and do not notify again until next await.
            # (handle_rendering might be called multiple times in a single await,
            # because of the endless loop in __iter__)
            self.should_notify_layout_change = False
            notify_layout_change(self)

        # Turn the brightness on again.
        ui.backlight_fade(self.BACKLIGHT_LEVEL)

    def handle_input_and_rendering(self) -> loop.Task:  # type: ignore [awaitable-is-generator]
        button = loop.wait(io.BUTTON)
        self._before_render()
        ui.display.clear()
        self.layout.attach_timer_fn(self.set_timer)
        self.layout.paint()
        while True:
            if __debug__:
                # Printing debugging info, just temporary
                RustLayoutContent(self.read_content())
            # Using `yield` instead of `await` to avoid allocations.
            event, button_num = yield button
            workflow.idle_timer.touch()
            msg = None
            if event in (io.BUTTON_PRESSED, io.BUTTON_RELEASED):
                msg = self.layout.button_event(event, button_num)
            self.layout.paint()
            if msg is not None:
                raise ui.Result(msg)

    def handle_timers(self) -> loop.Task:  # type: ignore [awaitable-is-generator]
        while True:
            # Using `yield` instead of `await` to avoid allocations.
            token = yield self.timer
            msg = self.layout.timer(token)
            self.layout.paint()
            if msg is not None:
                raise ui.Result(msg)


# BELOW ARE CUSTOM FUNCTIONS FOR TR

# Temporary function, so we know where it is used
# Should be gradually replaced by custom designs/layouts
async def _placeholder_confirm(
    ctx: wire.GenericContext,
    br_type: str,
    title: str,
    data: str,
    description: str | None = None,
    br_code: ButtonRequestType = ButtonRequestType.Other,
) -> Any:
    return await confirm_text(
        ctx=ctx,
        br_type=br_type,
        title=title,
        data=data,
        description=description,
        br_code=br_code,
    )


async def get_bool(
    ctx: wire.GenericContext,
    br_type: str,
    title: str,
    data: str,
    description: str | None = None,
    verb: str | None = "CONFIRM",
    verb_cancel: str | None = "CANCEL",
    hold: bool = False,
    br_code: ButtonRequestType = ButtonRequestType.Other,
) -> bool:
    result = await interact(
        ctx,
        RustLayout(
            trezorui2.confirm_action(
                title=title,
                action=data,
                description=description,
                verb=verb,
                verb_cancel=verb_cancel,
                hold=hold,
                reverse=False,
            )
        ),
        br_type,
        br_code,
    )

    return result is trezorui2.CONFIRMED


async def raise_if_cancelled(a: Awaitable[T], exc: Any = wire.ActionCancelled) -> T:
    result = await a
    if result is trezorui2.CANCELLED:
        raise exc
    return result


# BELOW ARE THE SAME AS IN tt/__init__.py


# TODO: probably make special version of some `action` and
# `description` strings for model R, as those for model T
# have newlines at random places (suitable for T).
async def confirm_action(
    ctx: wire.GenericContext,
    br_type: str,
    title: str,
    action: str | None = None,
    description: str | None = None,
    description_param: str | None = None,
    description_param_font: int = ui.BOLD,
    verb: str | bytes | None = "CONFIRM",
    verb_cancel: str | bytes | None = "CANCEL",
    hold: bool = False,
    hold_danger: bool = False,
    icon: str | None = None,
    icon_color: int | None = None,
    reverse: bool = False,
    larger_vspace: bool = False,
    exc: ExceptionType = wire.ActionCancelled,
    br_code: ButtonRequestType = ButtonRequestType.Other,
) -> None:
    if isinstance(verb, bytes) or isinstance(verb_cancel, bytes):
        raise NotImplementedError

    if description is not None and description_param is not None:
        if description_param_font != ui.BOLD:
            log.error(__name__, "confirm_action description_param_font not implemented")
        description = description.format(description_param)

    # Making the button text UPPERCASE, so it is better readable
    if isinstance(verb, str):
        verb = verb.upper()
    if isinstance(verb_cancel, str):
        verb_cancel = verb_cancel.upper()

    await raise_if_cancelled(
        interact(
            ctx,
            RustLayout(
                trezorui2.confirm_action(
                    title=title,
                    action=action,
                    description=description,
                    verb=verb,
                    verb_cancel=verb_cancel,
                    hold=hold,
                    reverse=reverse,
                )
            ),
            br_type,
            br_code,
        ),
        exc,
    )


async def confirm_reset_device(
    ctx: wire.GenericContext, prompt: str, recovery: bool = False
) -> None:
    # Showing the tutorial, as this is the entry point of
    # both the creation of new wallet and recovery of existing seed
    # - the first user interactions with Trezor.
    # (it is also special for model R, so not having to clutter the
    # common code)
    await tutorial(ctx)

    return await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type="recover_device" if recovery else "setup_device",
            title="Recovery mode" if recovery else "Create new wallet",
            data="By continuing you agree to trezor.io/tos",
            description=prompt,
            br_code=ButtonRequestType.ProtectCall
            if recovery
            else ButtonRequestType.ResetDevice,
        )
    )


# TODO cleanup @ redesign
async def confirm_backup(ctx: wire.GenericContext) -> bool:
    if await get_bool(
        ctx=ctx,
        title="Success",
        data="\nNew wallet created successfully!\n\n\nYou should back up your new wallet right now.",
        verb="Back up",
        verb_cancel="Skip",
        br_type="backup_device",
        br_code=ButtonRequestType.ResetDevice,
    ):
        return True

    confirmed = await get_bool(
        ctx=ctx,
        title="Warning",
        data="Are you sure you want to skip the backup?\n\n",
        description="You can back up your Trezor once, at any time.",
        verb="Back up",
        verb_cancel="Skip",
        br_type="backup_device",
        br_code=ButtonRequestType.ResetDevice,
    )
    return confirmed


async def confirm_path_warning(
    ctx: wire.GenericContext, path: str, path_type: str = "Path"
) -> None:
    return await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type="path_warning",
            title="Confirm path",
            data=f"{path_type}\n{path} is unknown.\nAre you sure?",
            description="",
            br_code=ButtonRequestType.UnknownDerivationPath,
        )
    )


async def show_xpub(
    ctx: wire.GenericContext, xpub: str, title: str, cancel: str
) -> None:
    return await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type="show_xpub",
            title=title,
            data=xpub,
            description="",
            br_code=ButtonRequestType.PublicKey,
        )
    )


async def show_address(
    ctx: wire.GenericContext,
    address: str,
    *,
    case_sensitive: bool = True,
    address_qr: str | None = None,
    title: str = "Confirm address",
    network: str | None = None,
    multisig_index: int | None = None,
    xpubs: Sequence[str] = (),
    address_extra: str | None = None,
    title_qr: str | None = None,
) -> None:
    text = ""
    if network:
        text += f"{network} network\n"
    if address_extra:
        text += f"{address_extra}\n"
    text += address
    return await _placeholder_confirm(
        ctx=ctx,
        br_type="show_address",
        title=title,
        data=text,
        description="",
        br_code=ButtonRequestType.Address,
    )


def show_pubkey(
    ctx: wire.Context, pubkey: str, title: str = "Confirm public key"
) -> Awaitable[None]:
    return confirm_blob(
        ctx,
        br_type="show_pubkey",
        title=title,
        data=pubkey,
        br_code=ButtonRequestType.PublicKey,
    )


async def _show_modal(
    ctx: wire.GenericContext,
    br_type: str,
    br_code: ButtonRequestType,
    header: str,
    subheader: str | None,
    content: str,
    button_confirm: str | None,
    button_cancel: str | None,
    icon: str,
    icon_color: int,
    exc: ExceptionType = wire.ActionCancelled,
) -> None:
    await confirm_action(
        ctx=ctx,
        br_type=br_type,
        br_code=br_code,
        title=header,
        action=subheader,
        description=content,
        verb=button_confirm,
        verb_cancel=button_cancel,
        exc=exc,
    )


async def show_error_and_raise(
    ctx: wire.GenericContext,
    br_type: str,
    content: str,
    header: str = "Error",
    subheader: str | None = None,
    button: str = "Close",
    red: bool = False,
    exc: ExceptionType = wire.ActionCancelled,
) -> NoReturn:
    await _show_modal(
        ctx=ctx,
        br_type=br_type,
        br_code=ButtonRequestType.Other,
        header=header,
        subheader=subheader,
        content=content,
        button_confirm=None,
        button_cancel=button,
        icon=ui.ICON_WRONG,
        icon_color=ui.RED if red else ui.ORANGE_ICON,
        exc=exc,
    )
    raise exc


def show_warning(
    ctx: wire.GenericContext,
    br_type: str,
    content: str,
    header: str = "Warning",
    subheader: str | None = None,
    button: str = "Try again",
    br_code: ButtonRequestType = ButtonRequestType.Warning,
    icon: str = ui.ICON_WRONG,
    icon_color: int = ui.RED,
) -> Awaitable[None]:
    return _show_modal(
        ctx,
        br_type=br_type,
        br_code=br_code,
        header=header,
        subheader=subheader,
        content=content,
        button_confirm=button,
        button_cancel=None,
        icon=icon,
        icon_color=icon_color,
    )


def show_success(
    ctx: wire.GenericContext,
    br_type: str,
    content: str,
    subheader: str | None = None,
    button: str = "Continue",
) -> Awaitable[None]:
    return _show_modal(
        ctx,
        br_type=br_type,
        br_code=ButtonRequestType.Success,
        header="Success",
        subheader=subheader,
        content=content,
        button_confirm=button,
        button_cancel=None,
        icon=ui.ICON_CONFIRM,
        icon_color=ui.GREEN,
    )


async def confirm_output(
    ctx: wire.GenericContext,
    address: str,
    amount: str,
    subtitle: str = "",
    font_amount: int = ui.NORMAL,  # TODO cleanup @ redesign
    title: str = "Confirm sending",
    width_paginated: int = 0,
    width: int = 0,
    icon: str = ui.ICON_SEND,
    to_str: str = "\nto\n",
    to_paginated: bool = True,
    color_to: str = "",
    br_code: ButtonRequestType = ButtonRequestType.ConfirmOutput,
) -> None:
    # Creating the truncated address here, not having to do it in Rust
    chars_to_take = 4
    ellipsis = " ... "
    truncated_address = address[:chars_to_take] + ellipsis + address[-chars_to_take:]

    # Also splitting the address into chunks delimited by whitespace
    chunk_length = 4
    delimiter = " "
    address_chunks: list[str] = []
    for i in range(0, len(address), chunk_length):
        address_chunks.append(address[i : i + chunk_length])
    address_str = delimiter.join(address_chunks)

    await raise_if_cancelled(
        interact(
            ctx,
            RustLayout(
                trezorui2.confirm_output_r(
                    address=address_str,
                    truncated_address=truncated_address,
                    amount=amount,
                )
            ),
            "confirm_output",
            br_code,
        )
    )


async def tutorial(
    ctx: wire.GenericContext,
    br_code: ButtonRequestType = ButtonRequestType.Other,
) -> None:
    """Showing users how to interact with the device."""
    await interact(
        ctx,
        RustLayout(trezorui2.tutorial()),
        "tutorial",
        br_code,
    )


async def confirm_payment_request(
    ctx: wire.GenericContext,
    recipient_name: str,
    amount: str,
    memos: list[str],
) -> Any:
    memos_str = "\n".join(memos)
    return await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type="confirm_payment_request",
            title="Confirm sending",
            data=f"{amount} to\n{recipient_name}\n{memos_str}",
            description="",
            br_code=ButtonRequestType.ConfirmOutput,
        )
    )


async def should_show_more(
    ctx: wire.GenericContext,
    title: str,
    para: Iterable[tuple[int, str]],
    button_text: str = "Show all",
    br_type: str = "should_show_more",
    br_code: ButtonRequestType = ButtonRequestType.Other,
    icon: str = ui.ICON_DEFAULT,
    icon_color: int = ui.ORANGE_ICON,
) -> bool:
    return await get_bool(
        ctx=ctx,
        title=title,
        data="Should show more?",
        br_type=br_type,
        br_code=br_code,
    )


async def confirm_blob(
    ctx: wire.GenericContext,
    br_type: str,
    title: str,
    data: bytes | str,
    description: str | None = None,
    hold: bool = False,
    br_code: ButtonRequestType = ButtonRequestType.Other,
    icon: str = ui.ICON_SEND,  # TODO cleanup @ redesign
    icon_color: int = ui.GREEN,  # TODO cleanup @ redesign
    ask_pagination: bool = False,
) -> None:
    await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type=br_type,
            title=title,
            data=str(data),
            description=description,
            br_code=br_code,
        )
    )


async def confirm_address(
    ctx: wire.GenericContext,
    title: str,
    address: str,
    description: str | None = "Address:",
    br_type: str = "confirm_address",
    br_code: ButtonRequestType = ButtonRequestType.Other,
    icon: str = ui.ICON_SEND,  # TODO cleanup @ redesign
    icon_color: int = ui.GREEN,  # TODO cleanup @ redesign
) -> Awaitable[None]:
    return confirm_blob(
        ctx=ctx,
        br_type=br_type,
        title=title,
        data=address,
        description=description,
        br_code=br_code,
    )


async def confirm_text(
    ctx: wire.GenericContext,
    br_type: str,
    title: str,
    data: str,
    description: str | None = None,
    br_code: ButtonRequestType = ButtonRequestType.Other,
    icon: str = ui.ICON_SEND,  # TODO cleanup @ redesign
    icon_color: int = ui.GREEN,  # TODO cleanup @ redesign
) -> Any:
    result = await interact(
        ctx,
        RustLayout(
            trezorui2.confirm_text(
                title=title,
                data=data,
                description=description,
            )
        ),
        br_type,
        br_code,
    )
    return result


def confirm_amount(
    ctx: wire.GenericContext,
    title: str,
    amount: str,
    description: str = "Amount:",
    br_type: str = "confirm_amount",
    br_code: ButtonRequestType = ButtonRequestType.Other,
    icon: str = ui.ICON_SEND,  # TODO cleanup @ redesign
    icon_color: int = ui.GREEN,  # TODO cleanup @ redesign
) -> Awaitable[None]:
    return _placeholder_confirm(
        ctx=ctx,
        br_type=br_type,
        title=title,
        data=amount,
        description=description,
        br_code=br_code,
    )


async def confirm_properties(
    ctx: wire.GenericContext,
    br_type: str,
    title: str,
    props: Iterable[PropertyType],
    icon: str = ui.ICON_SEND,  # TODO cleanup @ redesign
    icon_color: int = ui.GREEN,  # TODO cleanup @ redesign
    hold: bool = False,
    br_code: ButtonRequestType = ButtonRequestType.ConfirmOutput,
) -> None:
    await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type=br_type,
            title=title,
            data="\n\n".join(f"{name or ''}\n{value or ''}" for name, value in props),
            description="",
            br_code=br_code,
        )
    )


async def confirm_total(
    ctx: wire.GenericContext,
    total_amount: str,
    fee_amount: str,
    fee_rate_amount: str | None = None,
    title: str = "Send transaction?",
    total_label: str = "Total amount:",
    fee_label: str = "Including fee:",
    icon_color: int = ui.GREEN,
    br_type: str = "confirm_total",
    br_code: ButtonRequestType = ButtonRequestType.SignTx,
) -> None:
    await raise_if_cancelled(
        interact(
            ctx,
            RustLayout(
                trezorui2.confirm_total_r(
                    title=title,
                    total_amount=total_amount,
                    fee_amount=fee_amount,
                    fee_rate_amount=fee_rate_amount,
                    total_label=total_label,
                    fee_label=fee_label,
                )
            ),
            br_type,
            br_code,
        )
    )


async def confirm_joint_total(
    ctx: wire.GenericContext, spending_amount: str, total_amount: str
) -> None:
    await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type="confirm_joint_total",
            title="Joint transaction",
            data=f"You are contributing:\n{spending_amount}\nto the total amount:\n{total_amount}",
            description="",
            br_code=ButtonRequestType.SignTx,
        )
    )


async def confirm_metadata(
    ctx: wire.GenericContext,
    br_type: str,
    title: str,
    content: str,
    param: str | None = None,
    br_code: ButtonRequestType = ButtonRequestType.SignTx,
    hide_continue: bool = False,
    hold: bool = False,
    param_font: int = ui.BOLD,
    icon: str = ui.ICON_SEND,  # TODO cleanup @ redesign
    icon_color: int = ui.GREEN,  # TODO cleanup @ redesign
    larger_vspace: bool = False,  # TODO cleanup @ redesign
) -> None:
    text = content.format(param)
    if not hide_continue:
        text += "\n\nContinue?"

    await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type=br_type,
            title=title,
            data=text,
            description="",
            br_code=br_code,
        )
    )


async def confirm_replacement(
    ctx: wire.GenericContext, description: str, txid: str
) -> None:
    await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type="confirm_replacement",
            title=description,
            data=f"Confirm transaction ID:\n{txid}",
            description="",
            br_code=ButtonRequestType.SignTx,
        )
    )


async def confirm_modify_output(
    ctx: wire.GenericContext,
    address: str,
    sign: int,
    amount_change: str,
    amount_new: str,
) -> None:
    text = "Address:\n{address}\n\n"
    if sign < 0:
        text += "Decrease amount by:\n{amount_change}\n\n"
    else:
        text += "Increase amount by:\n{amount_change}\n\n"
    text += "New amount:\n{amount_new}"

    await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type="modify_output",
            title="Modify amount",
            data=text,
            description="",
            br_code=ButtonRequestType.ConfirmOutput,
        )
    )


async def confirm_modify_fee(
    ctx: wire.GenericContext,
    sign: int,
    user_fee_change: str,
    total_fee_new: str,
) -> None:
    text = ""
    if sign == 0:
        text += "Your fee did not change.\n"
    else:
        if sign < 0:
            text += "Decrease your fee by:\n"
        else:
            text += "Increase your fee by:\n"
        text += f"{user_fee_change}\n"
    text += f"Transaction fee:\n{total_fee_new}"

    await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type="modify_fee",
            title="Modify fee",
            data=text,
            description="",
            br_code=ButtonRequestType.SignTx,
        )
    )


async def confirm_coinjoin(
    ctx: wire.GenericContext, coin_name: str, max_rounds: int, max_fee_per_vbyte: str
) -> None:
    await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type="coinjoin_final",
            title="Authorize CoinJoin",
            data=f"Coin name: {coin_name}\n\nMaximum rounds: {max_rounds}\n\nMaximum mining fee:\n{max_fee_per_vbyte} sats/vbyte",
            description="",
            br_code=ButtonRequestType.Other,
        )
    )


# TODO cleanup @ redesign
async def confirm_sign_identity(
    ctx: wire.GenericContext, proto: str, identity: str, challenge_visual: str | None
) -> None:
    text = ""
    if challenge_visual:
        text += f"{challenge_visual}\n\n"
    text += identity

    await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type="confirm_sign_identity",
            title=f"Sign {proto}",
            data=text,
            description="",
            br_code=ButtonRequestType.Other,
        )
    )


async def confirm_signverify(
    ctx: wire.GenericContext, coin: str, message: str, address: str, verify: bool
) -> None:
    if verify:
        header = f"Verify {coin} message"
        br_type = "verify_message"
    else:
        header = f"Sign {coin} message"
        br_type = "sign_message"

    await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type=br_type,
            title=header,
            data=f"Confirm address:\n{address}",
            description="",
            br_code=ButtonRequestType.Other,
        )
    )

    await raise_if_cancelled(
        _placeholder_confirm(
            ctx=ctx,
            br_type=br_type,
            title=header,
            data=f"Confirm message:\n{message}",
            description="",
            br_code=ButtonRequestType.Other,
        )
    )


async def show_popup(
    title: str,
    description: str,
    subtitle: str | None = None,
    description_param: str = "",
    timeout_ms: int = 3000,
    icon: str = ui.ICON_WRONG,
) -> None:
    text = Text(title, icon)
    # Need to add two newlines at the beginning of the text,
    # so it is not colliding with the icon
    if subtitle is not None:
        subtitle = f"\n\n{subtitle}"
        text.bold(subtitle)
        text.br_half()
    else:
        description = f"\n\n{description}"
    text.format_parametrized(description, description_param)
    await Popup(text, timeout_ms)


def draw_simple_text(
    title: str, description: str = "", icon: str = ui.ICON_CONFIG
) -> None:
    text = Text(title, icon, new_lines=False)
    # Need to add two newlines at the beginning of the text,
    # so it is not colliding with the icon
    description = f"\n\n{description}"
    text.normal(description)
    ui.draw_simple(text)


async def request_passphrase_on_device(ctx: wire.GenericContext, max_len: int) -> str:
    await button_request(
        ctx, "passphrase_device", code=ButtonRequestType.PassphraseEntry
    )

    result = await ctx.wait(
        RustLayout(
            trezorui2.request_passphrase(
                prompt="Enter passphrase",
                max_len=max_len,
            )
        )
    )
    if result is trezorui2.CANCELLED:
        raise wire.ActionCancelled("Passphrase entry cancelled")

    assert isinstance(result, str)
    return result


async def request_pin_on_device(
    ctx: wire.GenericContext,
    prompt: str,
    attempts_remaining: int | None,
    allow_cancel: bool,
    shuffle: bool = False,
) -> str:
    await button_request(ctx, "pin_device", code=ButtonRequestType.PinEntry)

    if attempts_remaining is None:
        subprompt = ""
    elif attempts_remaining == 1:
        subprompt = "Last attempt"
    else:
        subprompt = f"{attempts_remaining} tries left"

    while True:
        result = await ctx.wait(
            RustLayout(
                trezorui2.request_pin(
                    prompt=prompt,
                    subprompt=subprompt,
                    allow_cancel=allow_cancel,
                    shuffle=shuffle,  # type: ignore [No parameter named "shuffle"]
                )
            )
        )
        if result is trezorui2.CANCELLED:
            raise wire.PinCancelled
        assert isinstance(result, str)
        return result
