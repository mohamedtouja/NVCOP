/// Graph builder component for relationships and transition matrices.
pub struct GraphBuilder;

pub struct GraphModel {
    pub transition_counts: [usize; 65536],
    pub node_counts: [usize; 256],
    pub edge_count: usize,
}

impl GraphBuilder {
    pub fn new() -> Self {
        Self
    }

    pub fn build(&self, data: &[u8]) -> GraphModel {
        let mut transition_counts = [0usize; 65536];
        let mut node_counts = [0usize; 256];
        let mut edge_count = 0;

        for window in data.windows(2) {
            let key = ((window[0] as usize) << 8) | (window[1] as usize);
            transition_counts[key] += 1;
            node_counts[window[0] as usize] += 1;
            edge_count += 1;
        }

        if let Some(&last) = data.last() {
            node_counts[last as usize] += 1;
        }

        GraphModel {
            transition_counts,
            node_counts,
            edge_count,
        }
    }
}
