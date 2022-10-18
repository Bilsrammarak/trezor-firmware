from typing import Any
from ubinascii import unhexlify

from trezor import protobuf, wire
from trezor.crypto.curve import ed25519
from trezor.enums import EthereumDefinitionType
from trezor.messages import EthereumNetworkInfo, EthereumTokenInfo

from apps.ethereum import tokens

from . import helpers, networks

DEFINITIONS_PUBLIC_KEY = b""
MIN_DATA_VERSION = 1
FORMAT_VERSION = "trzd1"

if __debug__:
    DEFINITIONS_DEV_PUBLIC_KEY = unhexlify(
        "db995fe25169d141cab9bbba92baa01f9f2e1ece7df4cb2ac05190f37fcc1f9d"
    )


class EthereumDefinitionParser:
    def __init__(self, definition_bytes: bytes) -> None:
        current_position = 0

        try:
            # prefix
            self.format_version = definition_bytes[:8].rstrip(b"\0").decode("utf-8")
            self.definition_type: int = definition_bytes[8]
            self.data_version = int.from_bytes(definition_bytes[9:13], "big")
            self.payload_length_in_bytes = int.from_bytes(
                definition_bytes[13:15], "big"
            )
            current_position += 8 + 1 + 4 + 2

            # payload
            self.payload = definition_bytes[
                current_position : (current_position + self.payload_length_in_bytes)
            ]
            self.payload_with_prefix = definition_bytes[
                : (current_position + self.payload_length_in_bytes)
            ]
            current_position += self.payload_length_in_bytes

            # suffix - Merkle tree proof and signed root hash
            self.proof_length: int = definition_bytes[current_position]
            current_position += 1
            self.proof: list[bytes] = []
            for _ in range(self.proof_length):
                self.proof.append(
                    definition_bytes[current_position : (current_position + 32)]
                )
                current_position += 32
            self.signed_tree_root = definition_bytes[
                current_position : (current_position + 64)
            ]
        except IndexError:
            raise wire.DataError("Invalid Ethereum definition")


def decode_definition(
    definition: bytes, expected_type: EthereumDefinitionType
) -> EthereumNetworkInfo | EthereumTokenInfo:
    # check network definition
    parsed_definition = EthereumDefinitionParser(definition)

    # first check format version
    if parsed_definition.format_version != FORMAT_VERSION:
        raise wire.DataError("Invalid definition format")

    # second check the type of the data
    if parsed_definition.definition_type != expected_type:
        raise wire.DataError("Definition type mismatch")

    # third check data version
    if parsed_definition.data_version < MIN_DATA_VERSION:
        raise wire.DataError("Definition is outdated")

    # at the end verify the signature - compute Merkle tree root hash using provided leaf data and proof
    def compute_mt_root_hash(data: bytes, proof: list[bytes]) -> bytes:
        from trezor.crypto.hashlib import sha256

        hash = sha256(b"\x00" + data).digest()
        for p in proof:
            hash_a = min(hash, p)
            hash_b = max(hash, p)
            hash = sha256(b"\x01" + hash_a + hash_b).digest()

        return hash

    # verify Merkle proof
    root_hash = compute_mt_root_hash(
        parsed_definition.payload_with_prefix, parsed_definition.proof
    )

    if not ed25519.verify(
        DEFINITIONS_PUBLIC_KEY, parsed_definition.signed_tree_root, root_hash
    ):
        error_msg = wire.DataError("Invalid definition signature")
        if __debug__:
            # check against dev key
            if not ed25519.verify(
                DEFINITIONS_DEV_PUBLIC_KEY,
                parsed_definition.signed_tree_root,
                root_hash,
            ):
                raise error_msg
        else:
            raise error_msg

    # decode it if it's OK
    if expected_type == EthereumDefinitionType.NETWORK:
        info = protobuf.decode(parsed_definition.payload, EthereumNetworkInfo, True)
    else:
        info = protobuf.decode(parsed_definition.payload, EthereumTokenInfo, True)

    return info


def _get_network_definiton(
    encoded_network_definition: bytes | None, ref_chain_id: int | None = None
) -> EthereumNetworkInfo | None:
    if encoded_network_definition is None and ref_chain_id is None:
        return None

    if ref_chain_id is not None:
        # if we have a built-in definition, use it
        network = networks.by_chain_id(ref_chain_id)
        if network is not None:
            return network  # type: EthereumNetworkInfo

    if encoded_network_definition is not None:
        # get definition if it was send
        network = decode_definition(
            encoded_network_definition, EthereumDefinitionType.NETWORK
        )

        # check referential chain_id with encoded chain_id
        if ref_chain_id is not None and network.chain_id != ref_chain_id:
            raise wire.DataError("Network definition mismatch")

        return network  # type: ignore [Expression of type "EthereumNetworkInfo | EthereumTokenInfo" cannot be assigned to return type "EthereumNetworkInfo | None"]

    return None


def _get_token_definiton(
    encoded_token_definition: bytes | None,
    ref_chain_id: int | None = None,
    ref_address: bytes | None = None,
) -> EthereumTokenInfo:
    if encoded_token_definition is None and (
        ref_chain_id is None or ref_address is None
    ):
        return tokens.UNKNOWN_TOKEN

    # if we have a built-in definition, use it
    if ref_chain_id is not None and ref_address is not None:
        token = tokens.token_by_chain_address(ref_chain_id, ref_address)
        if token is not tokens.UNKNOWN_TOKEN:
            return token

    if encoded_token_definition is not None:
        # get definition if it was send
        token: EthereumTokenInfo = decode_definition(  # type: ignore [Expression of type "EthereumNetworkInfo | EthereumTokenInfo" cannot be assigned to declared type "EthereumTokenInfo"]
            encoded_token_definition, EthereumDefinitionType.TOKEN
        )

        # check token against ref_chain_id and ref_address
        if (ref_chain_id is None or token.chain_id == ref_chain_id) and (
            ref_address is None or token.address == ref_address
        ):
            return token

    return tokens.UNKNOWN_TOKEN


class Definitions:
    """Class that holds Ethereum definitions - network and tokens. Prefers built-in definitions over encoded ones."""

    def __init__(
        self,
        encoded_network_definition: bytes | None = None,
        encoded_token_definition: bytes | None = None,
        ref_chain_id: int | None = None,
        ref_token_address: bytes | None = None,
    ) -> None:
        self.network = _get_network_definiton(encoded_network_definition, ref_chain_id)
        self.tokens: dict[bytes, EthereumTokenInfo] = {}

        # if we have some network, we can try to get token
        if self.network is not None:
            token = _get_token_definiton(
                encoded_token_definition, self.network.chain_id, ref_token_address
            )
            if token is not tokens.UNKNOWN_TOKEN:
                self.tokens[token.address] = token


def get_definitions_from_msg(msg: Any) -> Definitions:
    encoded_network_definition: bytes | None = None
    encoded_token_definition: bytes | None = None
    chain_id: int | None = None
    token_address: bytes | None = None

    # first try to get both definitions
    try:
        if msg.definitions is not None:
            encoded_network_definition = msg.definitions.encoded_network
            encoded_token_definition = msg.definitions.encoded_token
    except AttributeError:
        pass

    # check if we have network definition, if not give it a last try
    if encoded_network_definition is None:
        try:
            encoded_network_definition = msg.encoded_network
        except AttributeError:
            pass

    # get chain_id
    try:
        chain_id = msg.chain_id
    except AttributeError:
        pass

    # get token_address
    try:
        token_address = helpers.bytes_from_address(msg.to)
    except AttributeError:
        pass

    return Definitions(
        encoded_network_definition, encoded_token_definition, chain_id, token_address
    )