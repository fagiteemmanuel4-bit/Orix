import pytest
import requests
import yaml
from unittest.mock import patch, MagicMock
from orix.core.ai_builder import AIBuilder

@pytest.fixture
def builder():
    return AIBuilder(
        endpoint="https://fake-endpoint.com/v1",
        api_key="fake-api-key",
        model="fake-model"
    )

def test_ai_builder_missing_api_key():
    b = AIBuilder(endpoint="https://fake.com", api_key="", model="fake")
    with pytest.raises(ValueError, match="API key is missing"):
        b.build_spec("test prompt")

@patch("requests.post")
def test_ai_builder_valid_response(mock_post, builder):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "```yaml\nproject_name: test-app\nframework: fastapi\ndocker: true\n```"
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    spec = builder.build_spec("Build a FastAPI app")
    assert spec["project_name"] == "test-app"
    assert spec["framework"] == "fastapi"
    assert spec["docker"] is True

@patch("requests.post")
def test_ai_builder_malformed_yaml(mock_post, builder):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "```yaml\nproject_name: test-app\nframework: : fastapi\n```" # Malformed YAML syntax
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    with pytest.raises(ValueError, match="Failed to parse the AI response as a valid YAML specification"):
        builder.build_spec("prompt")

@patch("requests.post")
def test_ai_builder_empty_response(mock_post, builder):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": ""
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    with pytest.raises(ValueError, match="The AI model returned an empty response"):
        builder.build_spec("prompt")

@patch("requests.post")
def test_ai_builder_invalid_specification(mock_post, builder):
    # Spec is missing the required 'framework' field
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "```yaml\nproject_name: test-app\n```"
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    with pytest.raises(ValueError, match="The generated AI specification is invalid"):
        builder.build_spec("prompt")

@patch("requests.post")
def test_ai_builder_timeout(mock_post, builder):
    mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

    with pytest.raises(RuntimeError, match="The AI model request timed out"):
        builder.build_spec("prompt")

@patch("requests.post")
def test_ai_builder_provider_failure(mock_post, builder):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Internal Server Error")
    mock_post.return_value = mock_response

    with pytest.raises(RuntimeError, match="HTTP error"):
        builder.build_spec("prompt")

@patch("requests.post")
def test_ai_builder_unexpected_response_format(mock_post, builder):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {} # Unexpected empty dict / choices missing

    mock_post.return_value = mock_response

    with pytest.raises(ValueError, match="The AI model returned an empty response"):
        builder.build_spec("prompt")
