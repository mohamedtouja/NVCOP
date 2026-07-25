/// Bitstream utilities used by the Huffman encoder and decoder.

pub struct BitWriter {
    buffer: Vec<u8>,
    current: u8,
    filled: u8,
}

impl BitWriter {
    pub fn new() -> Self {
        Self {
            buffer: Vec::new(),
            current: 0,
            filled: 0,
        }
    }

    pub fn write_bits(&mut self, mut bits: u32, mut len: u8) {
        while len > 0 {
            let space = 8 - self.filled;
            let write_len = space.min(len);
            let shift = len - write_len;
            let mask = ((1u32 << write_len) - 1) << shift;
            self.current |= ((bits & mask) >> shift) as u8 << (space - write_len);
            self.filled += write_len;
            len -= write_len;
            bits &= !mask;

            if self.filled == 8 {
                self.buffer.push(self.current);
                self.current = 0;
                self.filled = 0;
            }
        }
    }

    pub fn finish(mut self) -> Vec<u8> {
        if self.filled > 0 {
            self.buffer.push(self.current);
        }
        self.buffer
    }
}

pub struct BitReader<'a> {
    data: &'a [u8],
    byte_index: usize,
    current: u8,
    available: u8,
}

impl<'a> BitReader<'a> {
    pub fn new(data: &'a [u8]) -> Self {
        Self {
            data,
            byte_index: 0,
            current: 0,
            available: 0,
        }
    }

    pub fn read_bit(&mut self) -> Option<u8> {
        if self.available == 0 {
            if self.byte_index >= self.data.len() {
                return None;
            }
            self.current = self.data[self.byte_index];
            self.byte_index += 1;
            self.available = 8;
        }

        self.available -= 1;
        Some((self.current >> self.available) & 1)
    }
}
