use std::fs::File;
use std::io::{self, Read, Write};
use std::path::Path;

use crate::core::block::{Block, BlockMetadata};
use crate::crypto::merkle::{compute_merkle_root, sha256};

const NOVA_MAGIC: &[u8; 4] = b"NOVA";
const NOVA_VERSION: u8 = 1;

/// Writes a NOVA container to disk.
pub fn write_nova_file(path: &Path, blocks: &[Block]) -> io::Result<()> {
    let mut file = File::create(path)?;
    file.write_all(NOVA_MAGIC)?;
    file.write_all(&[NOVA_VERSION])?;
    file.write_all(&(blocks.len() as u32).to_le_bytes())?;

    let checksums: Vec<[u8; 32]> = blocks.iter().map(|block| block.metadata.checksum).collect();
    let merkle_root = compute_merkle_root(&checksums);
    file.write_all(&merkle_root)?;

    for block in blocks {
        let bytes = block.metadata.to_bytes();
        file.write_all(&bytes)?;
        file.write_all(&block.payload)?;
    }

    Ok(())
}

/// Reads a NOVA container from disk.
pub fn read_nova_file(path: &Path) -> io::Result<(Vec<Block>, [u8; 32])> {
    let mut file = File::open(path)?;
    let mut header = [0u8; 9];
    file.read_exact(&mut header)?;
    if &header[0..4] != NOVA_MAGIC {
        return Err(io::Error::new(io::ErrorKind::InvalidData, "Invalid NOVA magic"));
    }

    let version = header[4];
    if version != NOVA_VERSION {
        return Err(io::Error::new(io::ErrorKind::InvalidData, "Unsupported NOVA version"));
    }

    let block_count = u32::from_le_bytes(header[5..9].try_into().unwrap());
    let mut merkle_root = [0u8; 32];
    file.read_exact(&mut merkle_root)?;

    let mut blocks = Vec::with_capacity(block_count as usize);
    for _ in 0..block_count {
        let mut metadata_bytes = [0u8; BlockMetadata::SERIALIZED_LEN];
        file.read_exact(&mut metadata_bytes)?;

        let metadata = BlockMetadata::from_bytes(&metadata_bytes)
            .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "Invalid block metadata"))?;

        let mut payload = vec![0u8; metadata.compressed_size as usize];
        file.read_exact(&mut payload)?;

        blocks.push(Block { metadata, payload });
    }

    let computed_root = compute_merkle_root(&blocks.iter().map(|block| block.metadata.checksum).collect::<Vec<_>>());
    if computed_root != merkle_root {
        return Err(io::Error::new(io::ErrorKind::InvalidData, "Merkle root mismatch"));
    }

    Ok((blocks, merkle_root))
}
