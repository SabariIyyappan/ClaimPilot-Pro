import hashlib
from typing import Dict


def compute_claim_hash(payload: Dict) -> str:
    # Simple deterministic hash (not for PHI in real apps)
    s = str(sorted(payload.items()))
    h = hashlib.sha256(s.encode('utf-8')).hexdigest()
    return h


def create_mock_tx(hash_hex: str) -> Dict:
    # Return a mock transaction payload referencing the claim hash
    return {"tx_hash": "0x" + hash_hex[:60], "network": "polygon-mumbai", "status": "mocked"}
