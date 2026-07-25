use novagraph_rust::entropy::huffman::{decode, encode};

#[test]
fn huffman_roundtrip_preserves_original_bytes() {
    let payload = b"The NovaGraph Rust port now includes a Huffman entropy layer.";
    let encoded = encode(payload);
    let decoded = decode(&encoded);

    assert_eq!(decoded, payload);
}
