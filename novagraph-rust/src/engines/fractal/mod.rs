pub mod detector;

use crate::core::block::ENGINE_FRACTAL;
use crate::engines::{AnalysisResult, CompressionEngine};
use detector::FractalDetector;

/// Fractal compression engine for NovaGraph.
pub struct FractalEngine;

impl FractalEngine {
    pub fn new() -> Self {
        Self
    }
}

impl CompressionEngine for FractalEngine {
    fn analyze(&self, data: &[u8]) -> AnalysisResult {
        let detector = FractalDetector::new();
        let score = detector.detect(data).map_or(0.0, |candidate| candidate.repeats as f32);
        AnalysisResult { score }
    }

    fn compress(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }

    fn decompress(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }

    fn engine_id(&self) -> u8 {
        ENGINE_FRACTAL
    }
}
