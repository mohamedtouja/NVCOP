use sha2::{Digest, Sha256};

/// Compute a SHA-256 digest for a single byte sequence.
pub fn sha256(data: &[u8]) -> [u8; 32] {
    let digest = Sha256::digest(data);
    digest.into()
}

/// Compute a simple Merkle root from a list of SHA-256 leaf hashes.
pub fn compute_merkle_root(leaves: &[[u8; 32]]) -> [u8; 32] {
    if leaves.is_empty() {
        return sha256(&[]);
    }

    let mut current_level: Vec<[u8; 32]> = leaves.to_vec();
    while current_level.len() > 1 {
        let mut next_level = Vec::with_capacity((current_level.len() + 1) / 2);
        for chunk in current_level.chunks(2) {
            let combined = if chunk.len() == 2 {
                [chunk[0].as_ref(), chunk[1].as_ref()].concat()
            } else {
                chunk[0].to_vec()
            };
            next_level.push(sha256(&combined));
        }
        current_level = next_level;
    }

    current_level[0]
}
