import pytest
from PySide6.QtWidgets import QApplication

from ai_logic import _analyze_user_input, classify_request, extract_image_prompt
from character import Character


def test_analyze_user_input_no_name_error_on_simple_message():
    """Regression: 'hello bro' used to raise NameError in Level-2 context
    inference inside _analyze_user_input, which crashed the entire chat
    pipeline and surfaced as 'Something went wrong while processing...'."""
    analysis = _analyze_user_input("hello bro")
    assert isinstance(analysis, dict)
    assert "history_relevant" in analysis


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_classify_weather_request():
    result = classify_request("What's the weather today?")
    assert result["intent"] == "weather"


def test_classify_image_request():
    result = classify_request("Generate an image of a futuristic AI companion")
    assert result["intent"] == "image"


def test_classify_timer_request():
    result = classify_request("Set a timer for 10 minutes")
    assert result["intent"] == "timer"


def test_extract_image_prompt_removes_command_words():
    prompt = extract_image_prompt("Generate an image of a futuristic AI companion")
    assert "futuristic AI companion" in prompt
    assert "Generate" not in prompt


def test_character_react_updates_expression_and_notification(qapp):
    widget = Character()
    widget.show()
    qapp.processEvents()
    widget.react("email_received", {"message": "You have a new message"})
    qapp.processEvents()
    assert widget.current_event == "email_received"
    assert widget.notification_label.isVisible()
    widget.close()
    widget.deleteLater()
    qapp.processEvents()
