from __future__ import annotations
import re
from typing import Optional

TOKEN_MARKER = b"TK"
MODEL_JSON = 1
MODEL_PYTHON = 2

TOK_KEYWORD = 0x01
TOK_IDENTIFIER = 0x02
TOK_STRING = 0x03
TOK_NUMBER = 0x04
TOK_PUNCT = 0x05
TOK_BOOL_NULL = 0x06
TOK_WHITESPACE = 0x07
TOK_RAW = 0xFF

PYTHON_KEYWORDS = {
    "def": 1,
    "return": 2,
    "import": 3,
    "from": 4,
    "class": 5,
    "if": 6,
    "else": 7,
    "elif": 8,
    "for": 9,
    "while": 10,
    "try": 11,
    "except": 12,
    "with": 13,
    "as": 14,
    "pass": 15,
    "break": 16,
    "continue": 17,
    "lambda": 18,
    "True": 19,
    "False": 20,
    "None": 21,
}

PYTHON_TOKEN_RE = re.compile(
    r"(?P<ws>\s+)"
    r"|(?P<string>r?\"\"\".*?\"\"\"|r?'''[\s\S]*?'''|\"(?:\\.|[^\\\"])*\"|'(?:\\.|[^\\'])*')"
    r"|(?P<identifier>[A-Za-z_][A-Za-z0-9_]*)"
    r"|(?P<number>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
    r"|(?P<op>==|!=|<=|>=|:=|->|\+=|-=|\*=|/=|//=|%=|\*\*|<<|>>|[(){}\[\],.:;@=+\-*/%&|^~<>])"
    r"|(?P<other>.)",
    re.DOTALL,
)

JSON_KEYWORDS = {"true": 1, "false": 2, "null": 3}


def _emit_token(header: bytearray, token_type: int, payload: bytes = b"") -> None:
    header.append(token_type)
    if token_type in (TOK_IDENTIFIER, TOK_STRING, TOK_NUMBER, TOK_RAW, TOK_WHITESPACE):
        length = len(payload)
        header.extend(length.to_bytes(2, "little"))
        header.extend(payload)
    elif token_type == TOK_PUNCT:
        header.extend(payload)
    elif token_type == TOK_KEYWORD:
        header.extend(payload)
    elif token_type == TOK_BOOL_NULL:
        header.extend(payload)
    else:
        header.extend(payload)


def _encode_whitespace(segment: str) -> bytes:
    data = segment.encode("utf-8", errors="ignore")
    output = bytearray()
    offset = 0
    while offset < len(data):
        chunk = data[offset : offset + 65535]
        output.append(TOK_WHITESPACE)
        output.extend(len(chunk).to_bytes(2, "little"))
        output.extend(chunk)
        offset += len(chunk)
    return bytes(output)


def detect_token_model(data: bytes) -> Optional[int]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    printable = sum(1 for c in text if 32 <= ord(c) < 127 or c in "\n\r\t")
    if printable / max(1, len(text)) < 0.9:
        return None
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        if text.count(":") >= 1 and text.count('"') >= 2:
            return MODEL_JSON
    if any(keyword in text for keyword in ["def ", "return ", "import ", "class "]):
        return MODEL_PYTHON
    return None


def _tokenize_json(data: bytes) -> Optional[bytes]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    out = bytearray(TOKEN_MARKER)
    out.append(MODEL_JSON)
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            j = i + 1
            while j < n and text[j].isspace():
                j += 1
            _emit_token(out, TOK_WHITESPACE, text[i:j].encode("utf-8"))
            i = j
            continue
        if ch == '"':
            start = i
            i += 1
            escaped = False
            while i < n:
                if escaped:
                    escaped = False
                    i += 1
                    continue
                if text[i] == '\\':
                    escaped = True
                elif text[i] == '"':
                    i += 1
                    break
                i += 1
            _emit_token(out, TOK_STRING, text[start:i].encode("utf-8"))
            continue
        if ch in "{}[]:,":
            _emit_token(out, TOK_PUNCT, ch.encode("utf-8"))
            i += 1
            continue
        if ch == '-' or ch.isdigit():
            start = i
            i += 1
            while i < n and (text[i].isdigit() or text[i] in ".+-eE"):  # approximate number syntax
                i += 1
            _emit_token(out, TOK_NUMBER, text[start:i].encode("utf-8"))
            continue
        if text.startswith("true", i) or text.startswith("false", i) or text.startswith("null", i):
            for literal, code in JSON_KEYWORDS.items():
                if text.startswith(literal, i):
                    _emit_token(out, TOK_BOOL_NULL, bytes([code]))
                    i += len(literal)
                    break
            continue
        # fallback raw bytes for any unknown token
        _emit_token(out, TOK_RAW, ch.encode("utf-8"))
        i += 1
    return bytes(out)


def _tokenize_python(data: bytes) -> Optional[bytes]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    out = bytearray(TOKEN_MARKER)
    out.append(MODEL_PYTHON)
    pos = 0
    n = len(text)
    for match in PYTHON_TOKEN_RE.finditer(text):
        kind = match.lastgroup
        token = match.group(0)
        if kind == "ws":
            _emit_token(out, TOK_WHITESPACE, token.encode("utf-8"))
        elif kind == "string":
            _emit_token(out, TOK_STRING, token.encode("utf-8"))
        elif kind == "identifier":
            if token in PYTHON_KEYWORDS:
                _emit_token(out, TOK_KEYWORD, bytes([PYTHON_KEYWORDS[token]]))
            else:
                _emit_token(out, TOK_IDENTIFIER, token.encode("utf-8"))
        elif kind == "number":
            _emit_token(out, TOK_NUMBER, token.encode("utf-8"))
        elif kind == "op":
            _emit_token(out, TOK_PUNCT, token.encode("utf-8"))
        else:
            _emit_token(out, TOK_RAW, token.encode("utf-8"))
    return bytes(out)


def tokenize_data(data: bytes) -> Optional[bytes]:
    model = detect_token_model(data)
    if model == MODEL_JSON:
        return _tokenize_json(data)
    if model == MODEL_PYTHON:
        return _tokenize_python(data)
    return None


def decode_token_stream(data: bytes) -> bytes:
    if not data.startswith(TOKEN_MARKER) or len(data) < 3:
        raise ValueError("Invalid token stream")
    model = data[2]
    payload = data[3:]
    if model == MODEL_JSON:
        return _decode_json_tokens(payload)
    if model == MODEL_PYTHON:
        return _decode_python_tokens(payload)
    raise ValueError("Unknown token model")


def _decode_json_tokens(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        token_type = data[i]
        i += 1
        if token_type in (TOK_IDENTIFIER, TOK_STRING, TOK_NUMBER, TOK_RAW, TOK_WHITESPACE):
            length = int.from_bytes(data[i : i + 2], "little")
            i += 2
            out.extend(data[i : i + length])
            i += length
        elif token_type == TOK_PUNCT:
            out.extend(data[i : i + 1])
            i += 1
        elif token_type == TOK_BOOL_NULL:
            code = data[i]
            i += 1
            literal = {1: b"true", 2: b"false", 3: b"null"}.get(code, b"")
            out.extend(literal)
        else:
            raise ValueError("Invalid JSON token stream")
    return bytes(out)


def _decode_python_tokens(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        token_type = data[i]
        i += 1
        if token_type in (TOK_IDENTIFIER, TOK_STRING, TOK_NUMBER, TOK_RAW, TOK_WHITESPACE):
            length = int.from_bytes(data[i : i + 2], "little")
            i += 2
            out.extend(data[i : i + length])
            i += length
        elif token_type == TOK_KEYWORD:
            keyword_id = data[i]
            i += 1
            keyword = next((k for k, v in PYTHON_KEYWORDS.items() if v == keyword_id), None)
            if keyword is None:
                raise ValueError("Invalid Python keyword token")
            out.extend(keyword.encode("utf-8"))
        elif token_type == TOK_PUNCT:
            # punctuation bytes may be one or more bytes; for simplicity, read one.
            out.extend(data[i : i + 1])
            i += 1
        else:
            raise ValueError("Invalid Python token stream")
    return bytes(out)
