import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BILL_PROXY_PATH = ROOT / "supervisor" / "plugins" / "bill_guardian" / "bill_proxy.py"

spec = importlib.util.spec_from_file_location("unifai_bill_proxy", BILL_PROXY_PATH)
bill_proxy = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bill_proxy)

BillGuardian = bill_proxy.BillGuardian
extract_usage_tokens = bill_proxy.extract_usage_tokens


def test_estimate_tokens_uses_fast_heuristic():
    guardian = BillGuardian()
    assert guardian.estimate_tokens("abcd") == 2


def test_evaluate_budget_allows_small_payload():
    guardian = BillGuardian()
    result = guardian.evaluate_budget("anthropic-api", "hello")
    assert result == {"gate_open": True, "estimated_tokens": 2}


def test_evaluate_budget_allows_exact_limit():
    guardian = BillGuardian()
    payload = "A" * 39996
    result = guardian.evaluate_budget("anthropic-api", payload)
    assert result["gate_open"] is True
    assert result["estimated_tokens"] == guardian.MAX_ESTIMATED_TOKENS


def test_evaluate_budget_blocks_large_payload():
    guardian = BillGuardian()
    result = guardian.evaluate_budget("anthropic-api", "A" * 50000)
    assert result["gate_open"] is False
    assert "BUDGET_EXCEEDED" in result["reason"]


def test_extract_usage_tokens_openai_provider_returns_non_zero_total():
    usage = {"prompt_tokens": 11, "completion_tokens": 7}
    assert extract_usage_tokens("openai", usage) == 18


def test_extract_usage_tokens_anthropic_provider_returns_non_zero_total():
    usage = {"input_tokens": 13, "output_tokens": 5}
    assert extract_usage_tokens("anthropic", usage) == 18


def test_extract_usage_tokens_rejects_missing_fields_instead_of_silent_zero():
    usage = {"prompt_tokens": 11}
    try:
        extract_usage_tokens("openai", usage)
    except KeyError as exc:
        assert str(exc) == "'completion_tokens'"
    else:
        raise AssertionError("expected missing token field to raise KeyError")
