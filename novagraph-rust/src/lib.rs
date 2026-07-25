//! NovaGraph Compressor Rust port.
//!
//! Phase 1 implements file reading, block splitting, the NOVA container format,
//! and decompression validation with byte-perfect roundtrip verification.

pub mod core;
pub mod engines;
pub mod optimizer;
pub mod entropy;
pub mod crypto;
pub mod benchmark;

pub use core::{NovaCompressor, NovaDecompressor};
