import hashlib


def assign_variant(user_id: str, experiment_id: str, variants: list):
    """
    Deterministic assignment using hashing.
    """

    hash_input = f"{user_id}:{experiment_id}".encode()
    hash_value = int(hashlib.sha256(hash_input).hexdigest(), 16)

    bucket = hash_value % 100

    cumulative = 0

    for variant in variants:
        cumulative += variant.weight
        if bucket < cumulative:
            return variant

    return variants[-1]