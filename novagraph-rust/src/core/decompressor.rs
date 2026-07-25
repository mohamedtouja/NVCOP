use rayon::prelude::*;
use std::fs::File;
use std::io::{self, Write};
use std::path::Path;
use std::time::{Duration, Instant};

use crate::core::block::{COMPRESSION_METHOD_HUFFMAN, COMPRESSION_METHOD_RAW};
use crate::core::format::read_nova_file;
use crate::crypto::merkle::sha256;
use crate::entropy::huffman::decode as huffman_decode;

/// Per-stage timing information for decompression profiling.
pub struct StageTiming {
    pub stage: String,
    pub duration_ms: f64,
}

/// Decompression report produced by the NovaGraph decompressor.
pub struct DecompressionReport {
    pub blocks: usize,
    pub total_original_bytes: u64,
    pub decompression_time_ms: f64,
    pub stage_timings: Vec<StageTiming>,
}

/// A NOVA decompressor for Phase 1.
pub struct NovaDecompressor;

impl NovaDecompressor {
    /// Create a new decompressor.
    pub fn new() -> Self {
        Self
    }

    fn decompress_block(&self, block_data: &[u8], compression_method: u8) -> io::Result<Vec<u8>> {
        match compression_method {
            COMPRESSION_METHOD_RAW => Ok(block_data.to_vec()),
            COMPRESSION_METHOD_HUFFMAN => Ok(huffman_decode(block_data)),
            unknown => Err(io::Error::new(
                io::ErrorKind::InvalidData,
                format!("Unsupported compression method {}", unknown),
            )),
        }
    }

    /// Read a NOVA container and restore the original file while returning a profiling report.
    pub fn decompress_file_with_report(
        &self,
        input_path: &Path,
        output_path: &Path,
    ) -> io::Result<DecompressionReport> {
        let total_start = Instant::now();
        let read_start = Instant::now();
        let (blocks, _) = read_nova_file(input_path)?;
        let read_time = read_start.elapsed();

        let decode_start = Instant::now();
        let mut decoded_blocks: Vec<Result<(u32, Vec<u8>), io::Error>> = blocks
            .into_par_iter()
            .map(|block| {
                let payload = self.decompress_block(&block.payload, block.metadata.compression_method)?;
                if payload.len() != block.metadata.original_size as usize {
                    return Err(io::Error::new(
                        io::ErrorKind::InvalidData,
                        "Block size mismatch during decompression",
                    ));
                }
                let computed_hash = sha256(&payload);
                if computed_hash != block.metadata.checksum {
                    return Err(io::Error::new(
                        io::ErrorKind::InvalidData,
                        "Block hash mismatch",
                    ));
                }
                Ok((block.metadata.block_id, payload))
            })
            .collect();
        let decode_time = decode_start.elapsed();

        let mut output = File::create(output_path)?;
        decoded_blocks.sort_by_key(|result| match result {
            Ok((block_id, _)) => *block_id,
            Err(_) => u32::MAX,
        });

        let write_start = Instant::now();
        let mut total_original_bytes = 0u64;
        for result in decoded_blocks {
            let (_block_id, payload) = result?;
            total_original_bytes += payload.len() as u64;
            output.write_all(&payload)?;
        }
        let write_time = write_start.elapsed();

        let decompression_time = total_start.elapsed();
        let stage_timings = vec![
            StageTiming {
                stage: "Read File".to_string(),
                duration_ms: read_time.as_secs_f64() * 1000.0,
            },
            StageTiming {
                stage: "Decode Blocks".to_string(),
                duration_ms: decode_time.as_secs_f64() * 1000.0,
            },
            StageTiming {
                stage: "Write File".to_string(),
                duration_ms: write_time.as_secs_f64() * 1000.0,
            },
        ];

        Ok(DecompressionReport {
            blocks: decoded_blocks.len(),
            total_original_bytes,
            decompression_time_ms: decompression_time.as_secs_f64() * 1000.0,
            stage_timings,
        })
    }

    /// Read a NOVA container and restore the original file.
    pub fn decompress_file(&self, input_path: &Path, output_path: &Path) -> io::Result<()> {
        self.decompress_file_with_report(input_path, output_path)
            .map(|_| ())
    }
}
