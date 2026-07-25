use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap};

use crate::entropy::bitstream::{BitReader, BitWriter};

#[derive(Debug, Eq, PartialEq)]
struct HuffmanNode {
    frequency: usize,
    symbol: Option<u8>,
    left: Option<Box<HuffmanNode>>,
    right: Option<Box<HuffmanNode>>,
}

impl Ord for HuffmanNode {
    fn cmp(&self, other: &Self) -> Ordering {
        other.frequency.cmp(&self.frequency)
    }
}

impl PartialOrd for HuffmanNode {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl HuffmanNode {
    fn leaf(symbol: u8, frequency: usize) -> Self {
        Self {
            frequency,
            symbol: Some(symbol),
            left: None,
            right: None,
        }
    }

    fn branch(left: HuffmanNode, right: HuffmanNode) -> Self {
        Self {
            frequency: left.frequency + right.frequency,
            symbol: None,
            left: Some(Box::new(left)),
            right: Some(Box::new(right)),
        }
    }
}

fn build_frequency_table(data: &[u8]) -> [usize; 256] {
    let mut frequencies = [0usize; 256];
    for &byte in data {
        frequencies[byte as usize] += 1;
    }
    frequencies
}

fn build_tree(frequencies: &[usize; 256]) -> Option<HuffmanNode> {
    let mut heap = BinaryHeap::new();
    for (symbol, &frequency) in frequencies.iter().enumerate() {
        if frequency > 0 {
            heap.push(HuffmanNode::leaf(symbol as u8, frequency));
        }
    }

    if heap.is_empty() {
        return None;
    }

    while heap.len() > 1 {
        let left = heap.pop().unwrap();
        let right = heap.pop().unwrap();
        heap.push(HuffmanNode::branch(left, right));
    }

    heap.pop()
}

fn collect_code_lengths(node: &HuffmanNode, depth: u8, lengths: &mut [u8; 256]) {
    if let Some(symbol) = node.symbol {
        lengths[symbol as usize] = depth.max(1);
        return;
    }
    if let Some(ref left) = node.left {
        collect_code_lengths(left, depth + 1, lengths);
    }
    if let Some(ref right) = node.right {
        collect_code_lengths(right, depth + 1, lengths);
    }
}

fn build_canonical_codes(lengths: &[u8; 256]) -> HashMap<u8, (u32, u8)> {
    let mut symbols: Vec<(u8, u8)> = lengths
        .iter()
        .enumerate()
        .filter_map(|(symbol, &length)| {
            if length > 0 {
                Some((symbol as u8, length))
            } else {
                None
            }
        })
        .collect();

    symbols.sort_by(|a, b| a.1.cmp(&b.1).then(a.0.cmp(&b.0)));

    let mut codes = HashMap::new();
    let mut code: u32 = 0;
    let mut previous_length = 0;

    for &(symbol, length) in &symbols {
        code <<= (length - previous_length) as u32;
        codes.insert(symbol, (code, length));
        code += 1;
        previous_length = length;
    }

    codes
}

/// Encode a raw byte stream using Huffman coding.
pub fn encode(data: &[u8]) -> Vec<u8> {
    let frequencies = build_frequency_table(data);
    let root = match build_tree(&frequencies) {
        Some(node) => node,
        None => return Vec::new(),
    };

    let mut code_lengths = [0u8; 256];
    collect_code_lengths(&root, 0, &mut code_lengths);
    let codes = build_canonical_codes(&code_lengths);

    let mut writer = BitWriter::new();
    writer.write_bits(0, 0); // align
    for length in code_lengths.iter() {
        writer.write_bits(*length as u32, 8);
    }

    for &byte in data {
        if let Some(&(code, length)) = codes.get(&byte) {
            writer.write_bits(code, length);
        }
    }

    writer.finish()
}

/// Decode a Huffman-coded byte stream.
pub fn decode(data: &[u8]) -> Vec<u8> {
    if data.len() < 256 {
        return Vec::new();
    }

    let header = &data[..256];
    let body = &data[256..];

    let mut code_lengths = [0u8; 256];
    code_lengths.copy_from_slice(header);

    let code_map = build_canonical_codes(&code_lengths);
    let mut lookup: HashMap<(u32, u8), u8> = HashMap::new();
    for (&symbol, &(code, length)) in &code_map {
        lookup.insert((code, length), symbol);
    }

    let mut output = Vec::new();
    let mut reader = BitReader::new(body);
    let mut current_code: u32 = 0;
    let mut current_len: u8 = 0;

    while let Some(bit) = reader.read_bit() {
        current_code = (current_code << 1) | (bit as u32);
        current_len += 1;

        if let Some(&symbol) = lookup.get(&(current_code, current_len)) {
            output.push(symbol);
            current_code = 0;
            current_len = 0;
        }
    }

    output
}
