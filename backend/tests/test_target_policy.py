import pytest

from core.target_policy import TargetKey, TargetPolicy, TargetPolicyError


def test_only_closed_ot_key_resolves_to_internal_gateway() -> None:
    target = TargetPolicy.resolve(TargetKey.OT_GATEWAY_DEMO)

    assert target.key is TargetKey.OT_GATEWAY_DEMO
    assert target.display_name == "Water Pump Gateway"
    assert target.base_url == "http://ot-gateway-demo:8081"
    assert target.url_for("/health") == "http://ot-gateway-demo:8081/health"


@pytest.mark.parametrize(
    "untrusted_target",
    [
        "https://example.com",
        "http://127.0.0.1:8080",
        "http://169.254.169.254/latest/meta-data",
        "localhost",
    ],
)
def test_arbitrary_target_values_are_rejected_before_network(
    untrusted_target: str,
) -> None:
    with pytest.raises(TargetPolicyError):
        TargetPolicy.resolve(untrusted_target)  # type: ignore[arg-type]


def test_unsafe_environment_override_is_rejected() -> None:
    with pytest.raises(TargetPolicyError):
        TargetPolicy.resolve(
            TargetKey.OT_GATEWAY_DEMO,
            configured_url="http://169.254.169.254",
        )


@pytest.mark.parametrize(
    "endpoint",
    [
        "health",
        "//example.com/path",
        "https://example.com/path",
        "/\\example.com/path",
        "/health\nX-Test: injected",
    ],
)
def test_endpoint_cannot_replace_or_ambiguously_change_origin(endpoint: str) -> None:
    target = TargetPolicy.resolve(TargetKey.OT_GATEWAY_DEMO)

    with pytest.raises(TargetPolicyError):
        target.url_for(endpoint)

