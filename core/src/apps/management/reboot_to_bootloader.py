from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from trezor.messages import RebootToBootloader
    from typing import NoReturn


async def reboot_to_bootloader(msg: RebootToBootloader) -> NoReturn:
    from trezor import io, loop, utils, translations as TR
    from trezor.messages import Success
    from trezor.ui.layouts import confirm_action
    from trezor.wire.context import get_context

    await confirm_action(
        "reboot",
        TR.reboot_to_bootloader__title,
        TR.reboot_to_bootloader__restart,
        verb=TR.buttons__restart,
    )
    ctx = get_context()
    await ctx.write(Success(message="Rebooting"))
    # make sure the outgoing USB buffer is flushed
    await loop.wait(ctx.iface.iface_num() | io.POLL_WRITE)
    utils.reboot_to_bootloader()
    raise RuntimeError
