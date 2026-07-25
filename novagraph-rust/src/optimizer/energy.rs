/// Pattern energy estimation for NovaGraph.
pub fn estimate_energy(data: &[u8]) -> f32 {
    if data.is_empty() {
        return 0.0;
    }

    let mut counts = [0usize; 256];
    for &byte in data {
        counts[byte as usize] += 1;
    }

    let total = data.len() as f32;
    let mut energy = 0.0;
    for &count in counts.iter() {
        if count > 0 {
            let probability = count as f32 / total;
            energy -= probability * probability.log2();
        }
    }

    energy
}
