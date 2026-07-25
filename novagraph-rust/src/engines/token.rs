/// Tokenizer placeholder for NovaGraph Phase 2.

/// A simple token engine stub that preserves raw bytes while providing a
/// pluggable entry point for later semantic tokenization.
pub struct TokenEngine;

impl TokenEngine {
    pub fn new() -> Self {
        Self
    }

    pub fn tokenize(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }

    pub fn detokenize(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }
}
