import importlib


def test_sanitize_user_text_cleans_whitespace():
    app_utils = importlib.import_module("app_utils")

    assert app_utils.sanitize_user_text("   hello   world   ") == "hello world"
    assert app_utils.sanitize_user_text("hello\n\nworld") == "hello world"


def test_clean_ai_reply_collapses_repeated_newlines():
    app_utils = importlib.import_module("app_utils")

    text = "Hello\n\n\nWorld"
    assert app_utils.clean_ai_reply(text) == "Hello\n\nWorld"


def test_format_status_returns_expected_shape():
    app_utils = importlib.import_module("app_utils")

    assert app_utils.format_status("thinking", "AI is thinking") == "AI is thinking"
    assert app_utils.format_status("ready") == "Ready"
