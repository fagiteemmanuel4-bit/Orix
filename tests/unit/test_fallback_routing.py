import pytest
from orix.core.ai_providers import get_provider, route_task, RoutingProvider, MockProvider

def test_dynamic_task_routing():
    config = {"provider": "openai", "model": "gpt-4o-mini"}

    # Complex design/architecture keywords should route to Anthropic Claude 3.5 Sonnet
    routed_arch = route_task("Please design a scalable distributed auth architecture.", config)
    assert routed_arch["provider"] == "anthropic"
    assert routed_arch["model"] == "claude-3-5-sonnet-20241022"

    # Routine coding should route to GPT-4o-mini
    routed_code = route_task("Fix syntax error in script", config)
    assert routed_code["provider"] == "openai"
    assert routed_code["model"] == "gpt-4o-mini"

def test_routing_provider_fallback():
    # Setup target provider with a predictable failure (timeout)
    failing_target = get_provider({"provider": "mock", "mock_failure": "timeout"})
    # Setup working local fallback
    working_fallback = get_provider({"provider": "mock"})

    routing_provider = RoutingProvider(failing_target, fallback_provider=working_fallback)

    # Since target fails, it should seamlessly route to the working fallback model
    resp = routing_provider.generate([{"role": "user", "content": "hello"}])
    assert "steps" in resp
