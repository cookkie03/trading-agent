"""Le prove sul conto paper richiedono un'opzione esplicita."""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--alpaca-paper",
        action="store_true",
        default=False,
        help="Esegue anche letture autenticate Alpaca paper (mai ordini)",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--alpaca-paper"):
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="use --alpaca-paper to enable paper reads"))
