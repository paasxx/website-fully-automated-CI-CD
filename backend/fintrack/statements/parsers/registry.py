from .nubank import NubankParser

# Add new parsers here as new banks are supported
_PARSERS = {
    "nubank": NubankParser(),
}


def get_parser(bank: str) -> "StatementParser":
    parser = _PARSERS.get(bank)
    if not parser:
        raise ValueError(f"No parser registered for bank: '{bank}'")
    return parser
