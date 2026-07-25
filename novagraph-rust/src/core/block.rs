use std::convert::TryInto;

/// Raw storage compression method.
pub const COMPRESSION_METHOD_RAW: u8 = 0;
/// Huffman compression method for encoded blocks.
pub const COMPRESSION_METHOD_HUFFMAN: u8 = 1;

/// Raw engine identifier for Phase 1.
pub const ENGINE_RAW: u8 = 0;
/// Huffman engine identifier placeholder.
pub const ENGINE_HUFFMAN: u8 = 1;
/// Graph engine identifier placeholder.
pub const ENGINE_GRAPH: u8 = 2;
/// Fractal engine identifier placeholder.
pub const ENGINE_FRACTAL: u8 = 3;
/// Spectral engine identifier placeholder.
pub const ENGINE_SPECTRAL: u8 = 4;

/// Block metadata stored inside the NOVA container.
#[derive(Debug, Clone)]
pub struct BlockMetadata {
    pub block_id: u32,
    pub original_size: u32,
    pub compressed_size: u32,
    pub compression_method: u8,
    pub engine_id: u8,
    pub checksum: [u8; 32],
}

/// A block payload plus metadata.
pub struct Block {
    pub metadata: BlockMetadata,
    pub payload: Vec<u8>,
}

impl BlockMetadata {
    pub const SERIALIZED_LEN: usize = 4 + 4 + 4 + 1 + 1 + 32;

    /// Serialize metadata into a fixed-size byte array.
    pub fn to_bytes(&self) -> [u8; Self::SERIALIZED_LEN] {
        let mut buffer = [0u8; Self::SERIALIZED_LEN];
        buffer[0..4].copy_from_slice(&self.block_id.to_le_bytes());
        buffer[4..8].copy_from_slice(&self.original_size.to_le_bytes());
        buffer[8..12].copy_from_slice(&self.compressed_size.to_le_bytes());
        buffer[12] = self.compression_method;
        buffer[13] = self.engine_id;
        buffer[14..46].copy_from_slice(&self.checksum);
        buffer
    }

    /// Deserialize metadata from a byte slice.
    pub fn from_bytes(bytes: &[u8]) -> Option<Self> {
        if bytes.len() != Self::SERIALIZED_LEN {
            return None;
        }

        let block_id = u32::from_le_bytes(bytes[0..4].try_into().ok()?);
        let original_size = u32::from_le_bytes(bytes[4..8].try_into().ok()?);
        let compressed_size = u32::from_le_bytes(bytes[8..12].try_into().ok()?);
        let compression_method = bytes[12];
        let engine_id = bytes[13];
        let checksum = bytes[14..46].try_into().ok()?;

        Some(BlockMetadata {
            block_id,
            original_size,
            compressed_size,
            compression_method,
            engine_id,
            checksum,
        })
    }
}
