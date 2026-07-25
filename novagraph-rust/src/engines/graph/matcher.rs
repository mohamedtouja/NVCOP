use crate::engines::graph::builder::GraphModel;

/// A candidate repeated pattern discovered from graph transitions.
pub struct PatternCandidate {
    pub pattern: Vec<u8>,
    pub frequency: usize,
}

/// Pattern matcher for NovaGraph graph analysis.
pub struct PatternMatcher;

impl PatternMatcher {
    pub fn new() -> Self {
        Self
    }

    pub fn find_repeated_patterns(&self, model: &GraphModel) -> Vec<PatternCandidate> {
        let mut candidates = Vec::new();
        for index in 0..model.transition_counts.len() {
            let frequency = model.transition_counts[index];
            if frequency > 1 {
                let first = ((index >> 8) & 0xFF) as u8;
                let second = (index & 0xFF) as u8;
                candidates.push(PatternCandidate {
                    pattern: vec![first, second],
                    frequency,
                });
            }
        }

        candidates.sort_by(|a, b| b.frequency.cmp(&a.frequency));
        candidates.truncate(16);
        candidates
    }
}
