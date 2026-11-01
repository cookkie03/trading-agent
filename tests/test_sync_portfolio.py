import os

from scripts.sync_portfolio import _load_local_env


def test_load_local_env_reads_values_without_overwriting_environment(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "ALPACA_API_KEY=from-file\n"
        "ALPACA_SECRET_KEY='secret-from-file'\n"
        'ALPACA_TRADING_URL="https://paper.example"\n'
        "# ignored\n"
        "INVALID_LINE\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ALPACA_API_KEY", "already-exported")
    monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
    monkeypatch.delenv("ALPACA_TRADING_URL", raising=False)

    _load_local_env()

    assert os.environ["ALPACA_API_KEY"] == "already-exported"
    assert os.environ["ALPACA_SECRET_KEY"] == "secret-from-file"
    assert os.environ["ALPACA_TRADING_URL"] == "https://paper.example"
