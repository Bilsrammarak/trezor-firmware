from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from trezor.messages import AuthenticateDevice, AuthenticityProof


async def authenticate_device(msg: AuthenticateDevice) -> AuthenticityProof:
    from trezor import utils
    from trezor.crypto import optiga
    from trezor.crypto.hashlib import sha256
    from trezor.messages import AuthenticityProof
    from trezor.ui.layouts import confirm_action

    from apps.common.writers import write_compact_size

    await confirm_action(
        "authenticate_device",
        "Authenticate device",
        description="Do you wish to verify the authenticity of your device?",
    )

    header = b"AuthenticateDevice:"
    h = utils.HashWriter(sha256())
    write_compact_size(h, len(header))
    h.extend(header)
    write_compact_size(h, len(msg.challenge))
    h.extend(msg.challenge)

    ctx = sha256()
    ctx.update(msg.challenge)
    signature = optiga.sign(0, h.get_digest())

    return AuthenticityProof(certificate=optiga.get_certificate(1), signature=signature)
