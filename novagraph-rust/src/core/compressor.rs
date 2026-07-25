use rayon::prelude::*;
use std::collections::HashMap;
use std::fs::File;
use std::io::{self, BufReader, Read};
use std::path::Path;
use std::time::{Duration, Instant};

use crate::core::block::{Block, BlockMetadata, COMPRESSION_METHOD_HUFFMAN, COMPRESSION_METHOD_RAW};
use crate::core::format::write_nova_file;
use crate::crypto::merkle::sha256;
use crate::entropy::huffman::encode as huffman_encode;
use crate::engines::{CompressionEngine, graph::GraphEngine};

/// A simple raw compressor that preserves Phase 1 semantics.
pub struct NovaCompressor {
    block_size: usize,
    engine: Box<dyn CompressionEngine + Send + Sync>,
}

/// Per-stage timing information for compression profiling.
pub struct StageTiming {
    pub stage: String,
    pub duration_ms: f64,
}

/// Engine usage counts by engine ID.
pub struct EngineUsage {
    pub engine_id: u8,
    pub count: u32,
}

/// Compression report produced by the NovaGraph compressor.
pub struct CompressionReport {
    pub blocks: usize,
    pub total_original_bytes: u64,
    pub total_compressed_bytes: u64,
    pub compression_ratio: f64,
    pub raw_blocks: usize,
    pub huffman_blocks: usize,
    pub engine_usage: Vec<EngineUsage>,
    pub stage_timings: Vec<StageTiming>,
    pub compression_time_ms: f64,
}

impl NovaCompressor {
    /// Create a compressor with a raw default engine.
    pub fn new(block_size: usize) -> Self {
        Self {
            block_size,
            engine: Box::new(crate::engines::RawEngine::new()),
        }
    }

    /// Create a compressor using the NovaGraph graph engine.
    pub fn new_graph(block_size: usize) -> Self {
        Self {
            block_size,
            engine: Box::new(GraphEngine::new()),
        }
    }

    /// Create a compressor using the NovaGraph fractal engine.
    pub fn new_fractal(block_size: usize) -> Self {
        Self {
            block_size,
            engine: Box::new(crate::engines::fractal::FractalEngine::new()),
        }
    }

    /// Create a compressor using the NovaGraph spectral engine.
    pub fn new_spectral(block_size: usize) -> Self {
        Self {
            block_size,
            engine: Box::new(crate::engines::spectral::SpectralEngine::new()),
        }
    }
    /// Create a compressor using the NovaGraph fractal engine.
    pub fn new_fractal(block_size: usize) -> Self {
        Self {
            block_size,
            engine: Box::new(crate::engines::fractal::FractalEngine::new()),
        }
    }

    /// Create a compressor using the NovaGraph spectral engine.
    pub fn new_spectral(block_size: usize) -> Self {
        Self {
            block_size,
            engine: Box::new(crate::engines::spectral::SpectralEngine::new()),
        }
    }
    /// Create a compressor with a custom pluggable engine.
    pub fn with_engine(block_size: usize, engine: Box<dyn CompressionEngine + Send + Sync>) -> Self {
        Self { block_size, engine }
    }

    fn compress_block(&self, block_id: u32, payload: Vec<u8>) -> io::Result<(Block, Duration, Duration)> {
        let engine_start = Instant::now();
        self.engine.analyze(&payload);
        let engine_payload = self.engine.compress(&payload);
        let engine_time = engine_start.elapsed();

        let checksum = sha256(&payload);
        let huffman_start = Instant::now();
        let encoded = huffman_encode(&engine_payload);
        let huffman_time = huffman_start.elapsed();

        let (compressed_payload, compression_method) = if encoded.len() < engine_payload.len() {
            (encoded, COMPRESSION_METHOD_HUFFMAN)
        } else {
            (engine_payload, COMPRESSION_METHOD_RAW)
        };

        let metadata = BlockMetadata {
            block_id,
            original_size: payload.len() as u32,
            compressed_size: compressed_payload.len() as u32,
            compression_method,
            engine_id: self.engine.engine_id(),
            checksum,
        };

        Ok((Block {
            metadata,
            payload: compressed_payload,
        }, engine_time, huffman_time))
    }

    /// Compress a file into the NOVA container and return a profiling report.
    pub fn compress_file_with_report(
        &self,
        input_path: &Path,
        output_path: &Path,
    ) -> io::Result<CompressionReport> {
        let total_start = Instant::now();
        let file = File::open(input_path)?;
        let mut reader = BufReader::new(file);
        let mut payloads = Vec::new();
        let mut block_id = 0u32;
        let mut read_time = Duration::ZERO;
        let mut split_time = Duration::ZERO;

        loop {
            let mut buffer = vec![0u8; self.block_size];
            let chunk_start = Instant::now();
            let bytes_read = reader.read(&mut buffer)?;
            read_time += chunk_start.elapsed();
            if bytes_read == 0 {
                break;
            }
            let split_start = Instant::now();
            buffer.truncate(bytes_read);
            payloads.push((block_id, buffer));
            block_id += 1;
            split_time += split_start.elapsed();
        }

        let mut engine_time = Duration::ZERO;
        let mut huffman_time = Duration::ZERO;
        let compressed_blocks: Vec<_> = payloads
            .into_par_iter()
            .map(|(block_id, payload)| {
                let (block, engine_duration, huffman_duration) = self.compress_block(block_id, payload)?;
                Ok((block, engine_duration, huffman_duration))
            })
            .collect();

        let mut blocks = Vec::with_capacity(compressed_blocks.len());
        for result in compressed_blocks {
            let (block, engine_duration, huffman_duration) = result?;
            engine_time += engine_duration;
            huffman_time += huffman_duration;
            blocks.push(block);
        }

        let write_start = Instant::now();
        write_nova_file(output_path, &blocks)?;
        let write_time = write_start.elapsed();

        let total_original_bytes: u64 = blocks.iter().map(|block| block.metadata.original_size as u64).sum();
        let total_compressed_bytes: u64 = blocks.iter().map(|block| block.metadata.compressed_size as u64).sum();
        let raw_blocks = blocks
            .iter()
            .filter(|block| block.metadata.compression_method == COMPRESSION_METHOD_RAW)
            .count();
        let huffman_blocks = blocks
            .iter()
            .filter(|block| block.metadata.compression_method == COMPRESSION_METHOD_HUFFMAN)
            .count();

        let mut engine_counts = HashMap::new();
        for block in &blocks {
            *engine_counts.entry(block.metadata.engine_id).or_insert(0) += 1;
        }

        let engine_usage = engine_counts
            .into_iter()
            .map(|(engine_id, count)| EngineUsage { engine_id, count })
            .collect();

        let compression_time = total_start.elapsed();
        let compression_ratio = if total_original_bytes == 0 {
            0.0
        } else {
            total_compressed_bytes as f64 / total_original_bytes as f64
        };

        let stage_timings = vec![
            StageTiming {
                stage: "Read File".to_string(),
                duration_ms: read_time.as_secs_f64() * 1000.0,
            },
            StageTiming {
                stage: "Block Split".to_string(),
                duration_ms: split_time.as_secs_f64() * 1000.0,
            },
            StageTiming {
                stage: "Engine".to_string(),
                duration_ms: engine_time.as_secs_f64() * 1000.0,
            },
            StageTiming {
                stage: "Huffman".to_string(),
                duration_ms: huffman_time.as_secs_f64() * 1000.0,
            },
            StageTiming {
                stage: "Write File".to_string(),
                duration_ms: write_time.as_secs_f64() * 1000.0,
            },
        ];

        Ok(CompressionReport {
            blocks: blocks.len(),
            total_original_bytes,
            total_compressed_bytes,
            compression_ratio,
            raw_blocks,
            huffman_blocks,
            engine_usage,
            stage_timings,
            compression_time_ms: compression_time.as_secs_f64() * 1000.0,
        })
    }

    /// Compress a file into the NOVA container using block-based raw storage.
    pub fn compress_file(&self, input_path: &Path, output_path: &Path) -> io::Result<()> {
        self.compress_file_with_report(input_path, output_path)
            .map(|_| ())
    }
}
