import hashlib


def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def merkle_root_hash(hashes: list[bytes]) -> bytes:
    if not hashes:
        return hashlib.sha256(b"").digest()

    current_level = hashes[:]
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            next_level.append(hashlib.sha256(left + right).digest())
        current_level = next_level
    return current_level[0]
