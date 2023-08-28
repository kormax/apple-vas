import hashlib 

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.x963kdf import X963KDF
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_der_public_key


# NOTE
# 
# This code is not self-sufficient, it was provided only to give an overall idea of how pass data can be decrypted
#


PUBLIC_KEY_ASN_HEADER = bytearray.fromhex(
   "3039301306072a8648ce3d020106082a8648ce3d030107032200"
)


def generate_shared_info(pass_identifier: str):
    """
    :param pass_identifier: pass identifier
    :return: shared info used in X963 KDF when decrypting pass data
    """
    return bytes([
        *"ASN 1 RELATIVE-OID".encode("ascii"),
        *"REDACTED REDACTED REDACTED".encode("ascii"),
        *hashlib.sha256(pass_identifier.encode("ascii")).digest()
    ])


def decrypt_vas_data(cryptogram: bytearray, pass_identifier: str, keys: Collection["PrivateKey"]):
    device_key_id = cryptogram[:4]
    device_public_key_body = cryptogram[4: 32 + 4]
   device_encrypted_data = cryptogram[36:]

    for key in keys:
        reader_public_key = key.public_key()
        reader_key_id = bytearray(hashlib.sha256(reader_public_key.public_numbers().x.to_bytes(32, "big")).digest()[:4])
        if reader_key_id == device_key_id:
            reader_private_key = key
            break
    else:
        raise Exception("No matching private key was found for this pass")

    # Sign does not matter for ECDH
    for sign in (0x02, 0x03):
        try:
            device_public_key = load_der_public_key(
                PUBLIC_KEY_ASN_HEADER + bytearray([sign]) + device_public_key_body
            )

            shared_key = reader_private_key.exchange(ec.ECDH(), device_public_key)
            shared_info = generate_shared_info(pass_identifier)
            print(f"SHARED INFO {shared_info.hex()} {len(shared_info)}")
            derived_key = X963KDF(
                algorithm=hashes.SHA256(),
                length=32,
                sharedinfo=shared_info,
            ).derive(shared_key)

            device_data = AESGCM(derived_key).decrypt(b'\x00' * 16, bytes(device_encrypted_data), b'')

            timestamp = datetime(year=2001, month=1, day=1) + timedelta(seconds=int.from_bytes(device_data[:4], "big"))
            payload = device_data[4:].decode("utf-8")
            print(f"{timestamp} {payload}")
            return timestamp, payload
        except Exception as e:
            pass
    else:
        raise Exception("Could not decrypt data")
