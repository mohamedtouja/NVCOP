pub mod builder;
pub mod matcher;

use crate::core::block::ENGINE_GRAPH;
use crate::optimizer::{estimate_energy, score_gravity};
use super::{AnalysisResult, CompressionEngine};

use builder::GraphBuilder;
use matcher::PatternMatcher;

/// Graph engine for NovaGraph that computes transition graphs and pattern gravity.
pub struct GraphEngine;

impl GraphEngine {
    pub fn new() -> Self {
        Self
    }
}

impl CompressionEngine for GraphEngine {
    fn analyze(&self, data: &[u8]) -> AnalysisResult {
        let model = GraphBuilder::new().build(data);
        let matches = PatternMatcher::new().find_repeated_patterns(&model);
        let gravity = score_gravity(data);
        let energy = estimate_energy(data);

        let score = gravity * 0.6 + energy * 0.3 + (matches.len() as f32 * 0.1);
        AnalysisResult { score }
    }

    fn compress(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }

    fn decompress(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }

    fn engine_id(&self) -> u8 {
        ENGINE_GRAPH
    }
}
