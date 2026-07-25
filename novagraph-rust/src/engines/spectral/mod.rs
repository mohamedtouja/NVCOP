pub mod analyzer;

use crate::core::block::ENGINE_SPECTRAL;
use crate::engines::{AnalysisResult, CompressionEngine};
use analyzer::SpectralAnalyzer;

/// Spectral compression engine for NovaGraph.
pub struct SpectralEngine;

impl SpectralEngine {
    pub fn new() -> Self {
        Self
    }
}

impl CompressionEngine for SpectralEngine {
    fn analyze(&self, data: &[u8]) -> AnalysisResult {
        let analyzer = SpectralAnalyzer::new();
        let score = analyzer.analyze(data);
        AnalysisResult { score }
    }

    fn compress(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }

    fn decompress(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }

    fn engine_id(&self) -> u8 {
        ENGINE_SPECTRAL
    }
}
