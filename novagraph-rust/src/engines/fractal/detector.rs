/// Fractal detector for NovaGraph.
pub struct FractalDetector;

/// A detected fractal pattern and the number of consecutive repeats.
pub struct FractalPattern {
    pub pattern: Vec<u8>,
    pub repeats: usize,
}

impl FractalDetector {
    pub fn new() -> Self {
        Self
    }

    pub fn detect(&self, data: &[u8]) -> Option<FractalPattern> {
        let max_pattern_len = data.len().min(64);
        let mut best: Option<FractalPattern> = None;

        for length in 4..=max_pattern_len {
            if length * 2 > data.len() {
                break;
            }
            let pattern = &data[..length];
            let mut repeats = 1;
            while repeats * length + length <= data.len() {
                let start = repeats * length;
                if &data[start..start + length] == pattern {
                    repeats += 1;
                } else {
                    break;
                }
            }

            if repeats > 1 {
                let candidate = FractalPattern {
                    pattern: pattern.to_vec(),
                    repeats,
                };
                if best.as_ref().map_or(true, |existing| repeats > existing.repeats) {
                    best = Some(candidate);
                }
            }
        }

        best
    }
}
