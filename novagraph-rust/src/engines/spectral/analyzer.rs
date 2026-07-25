/// Spectral analyzer for NovaGraph.
pub struct SpectralAnalyzer;

impl SpectralAnalyzer {
    pub fn new() -> Self {
        Self
    }

    pub fn analyze(&self, data: &[u8]) -> f32 {
        if data.is_empty() {
            return 0.0;
        }

        let n = data.len().min(64);
        let mut score = 0.0;
        for k in 1..=8 {
            let mut coefficient = 0.0;
            for (i, &value) in data.iter().take(n).enumerate() {
                let x = (value as f32 / 255.0) - 0.5;
                let angle = std::f32::consts::PI * (k as f32) * (i as f32 + 0.5) / (n as f32);
                coefficient += x * angle.cos();
            }
            score += coefficient.abs();
        }

        score / 8.0
    }
}
