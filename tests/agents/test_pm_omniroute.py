import io
import json

from agents.pm_omniroute import OmniRoutePMReviewer
from tests.workflows.test_trade_cycle import approved_state


def test_omniroute_reviewer_sends_research_and_reads_json(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return io.BytesIO(
            json.dumps({"choices": [{"message": {"content": '{"decision":"reject"}'}}]}).encode()
        )

    monkeypatch.setattr("agents.pm_omniroute.urlopen", fake_urlopen)
    review = OmniRoutePMReviewer("test-key", "test-model")(approved_state(), ())
    assert review == {"decision": "reject"}
    assert captured["url"] == "http://localhost:20128/v1/chat/completions"
    assert captured["body"]["model"] == "test-model"
    assert "run-1" in captured["body"]["messages"][1]["content"]
    assert captured["timeout"] == 30


def test_omniroute_reviewer_rejects_empty_configuration():
    import pytest

    with pytest.raises(ValueError):
        OmniRoutePMReviewer("", "test-model")
    with pytest.raises(ValueError):
        OmniRoutePMReviewer("test-key", "")
