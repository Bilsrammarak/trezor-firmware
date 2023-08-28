import pytest
from cryptography import x509

from trezorlib import device
from trezorlib.debuglink import TrezorClientDebugLink as Client

pytestmark = [pytest.mark.skip_t1, pytest.mark.skip_t2]


def test_authenticate_device(client: Client) -> None:
    # Issue an AuthenticateDevice challenge to Trezor.
    # NOTE Applications must generate a random challenge for each request.
    challenge = bytes.fromhex(
        "21f3d40e63c304d0312f62eb824113efd72ba1ee02bef6777e7f8a7b6f67ba16"
    )
    proof = device.authenticate(client, challenge)
    cert = x509.load_der_x509_certificate(proof.certificate)

    # NOTE Applications must verify certificate validity against a list of trusted CAs.

    # Verify the signature of the challenge.
    data = b"\x13AuthenticateDevice:" + bytes([len(challenge)]) + challenge
    cert.public_key().verify(proof.signature, data, cert.signature_algorithm_parameters)
