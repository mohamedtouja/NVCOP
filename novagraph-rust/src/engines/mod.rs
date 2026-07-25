pub mod graph;
pub mod fractal;
pub mod spectral;
pub mod cellular;
pub mod topology;
pub mod token;

use crate::core::block::ENGINE_RAW;

/// The compression engine contract for NovaGraph.
pub trait CompressionEngine {
    fn analyze(&self, data: &[u8]) -> AnalysisResult;
    fn compress(&self, data: &[u8]) -> Vec<u8>;
    fn decompress(&self, data: &[u8]) -> Vec<u8>;
    fn engine_id(&self) -> u8;
}

/// A lightweight analysis result produced by an engine.
pub struct AnalysisResult {
    pub score: f32,
}

impl AnalysisResult {
    /// Default analysis result for Phase 1.
    pub fn default() -> Self {
        Self { score: 0.0 }
    }
}

/// A raw placeholder engine used during Phase 1.
pub struct RawEngine;

impl RawEngine {
    pub fn new() -> Self {
        Self
    }
}

impl CompressionEngine for RawEngine {
    fn analyze(&self, _data: &[u8]) -> AnalysisResult {
        AnalysisResult::default()
    }

    fn compress(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }

    fn decompress(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }

    fn engine_id(&self) -> u8 {
        ENGINE_RAW
    }
}
