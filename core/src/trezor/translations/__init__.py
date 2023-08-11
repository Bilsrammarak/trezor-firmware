from trezor import utils

if utils.LANG == "cs":
    from .cs import *  # noqa: F401,F403
else:
    from .en import *  # noqa: F401,F403
