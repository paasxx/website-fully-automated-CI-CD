from .nubank import NubankParser
from .btg import BTGParser
from .inter import InterParser

# Add new parsers here as new banks are supported
_PARSERS = {
    "nubank": NubankParser(),
    "inter":  InterParser(),
    "btg":    BTGParser(),
}


def get_parser(bank: str) -> "StatementParser":
    parser = _PARSERS.get(bank)
    if not parser:
        raise ValueError(f"No parser registered for bank: '{bank}'")
    return parser
