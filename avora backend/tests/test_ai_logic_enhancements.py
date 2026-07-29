from ai_logic import classify_request, extract_image_prompt
from character import Character


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


def test_character_react_updates_expression_and_notification():
    widget = Character()
    widget.react("email_received", {"message": "You have a new message"})
    assert widget.current_event == "email_received"
    assert widget.notification_label.isVisible()
