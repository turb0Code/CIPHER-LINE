from tinyec import registry
import secrets
import sys

curve = registry.get_curve('brainpoolP256r1')

def compress_point(point):
    return hex(point.x) + hex(point.y % 2)[2:]

def ecc_calc_encryption_keys(pubKey):
    ciphertextPrivKey = secrets.randbits(64)
    ciphertextPubKey = ciphertextPrivKey * curve.g
    sharedECCKey = pubKey * ciphertextPrivKey
    return (sharedECCKey, ciphertextPubKey)

def ecc_calc_decryption_key(privKey, ciphertextPubKey):
    sharedECCKey = ciphertextPubKey * privKey
    return sharedECCKey

privKey = secrets.randbits(1024)
pubKey = privKey * curve.g
sharedKey = pubKey * privKey

modulo_value = sys.maxunicode

print("private key:", hex(privKey))
print("public key:", compress_point(pubKey))

(encryptKey, ciphertextPubKey) = ecc_calc_encryption_keys(pubKey)
print("ciphertext pubKey:", compress_point(ciphertextPubKey))
print("encryption key:", compress_point(encryptKey))

decryptKey = ecc_calc_decryption_key(privKey, ciphertextPubKey)
print("decryption key:", compress_point(decryptKey))


print("\nTEST:")
pv_key1 = secrets.randbelow(curve.field.n)
pv_key2 = secrets.randbelow(curve.field.n)
pv_key3 = secrets.randbelow(curve.field.n)
print(f"key: {pv_key1}")
print(f"key: {pv_key2}")
print(f"key: {pv_key3}")

string = "HEY IT'S TEST"

print(f"RAW: {string}")

encrypted = ''.join(chr((ord(c) + sharedKey.x) % modulo_value) for c in string)
print(f"EC: {encrypted}")
encrypted = encrypted.encode('utf-8')
print(f"EC X2: {encrypted}")

encrypted = encrypted.decode('utf-8')
print(f"DC DC: {encrypted}")
decrypted = ''.join(chr((ord(c) - sharedKey.x) % modulo_value) for c in encrypted)
print(f"DC: {decrypted}")

