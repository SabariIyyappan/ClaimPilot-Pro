import hashlib
from typing import Dict


def compute_claim_hash(payload: Dict) -> str:
    """Deterministic hash for a claim payload.

    This is used only for local auditing to fingerprint a claim submission.
    Do not include PHI in the payload passed here in production systems.
    """
    # Sort payload items for determinism and hash the string representation
    s = str(sorted(payload.items()))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

