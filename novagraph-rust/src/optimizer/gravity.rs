/// Pattern gravity scoring for NovaGraph.
pub fn score_gravity(data: &[u8]) -> f32 {
    if data.len() < 2 {
        return 0.0;
    }

    let mut seen = [0usize; 65536];
    for window in data.windows(2) {
        let index = ((window[0] as usize) << 8) | (window[1] as usize);
        seen[index] += 1;
    }

    let repeated_count = seen.iter().filter(|&&count| count > 1).count();
    repeated_count as f32 / 65536.0
}
