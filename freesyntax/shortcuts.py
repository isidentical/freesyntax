import io
import tokenize


def get_tokens(source):
    buffer = io.StringIO(source)
    tokens = tokenize.generate_tokens(buffer.readline)
    return tuple(tokens)


def untokenize(source):
    return tokenize.untokenize(source)
