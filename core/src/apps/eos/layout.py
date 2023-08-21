async def require_get_public_key(public_key: str) -> None:
    from trezor.ui.layouts import show_pubkey

    await show_pubkey(public_key)


async def require_sign_tx(num_actions: int) -> None:
    from trezor.enums import ButtonRequestType
    from trezor.strings import format_plural
    from trezor.ui.layouts import confirm_action
    from trezor import translations as TR

    await confirm_action(
        "confirm_tx",
        TR.eos__sign_transaction,
        description=TR.eos__about_to_sign_template,
        # TODO: translate plural
        description_param=format_plural("{count} {plural}", num_actions, "action"),
        br_code=ButtonRequestType.SignTx,
    )
