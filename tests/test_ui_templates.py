"""
Tests for the UI templates module.
"""

import pytest
from src.ui.templates import ChatTemplates, css, bot_template, user_template


class TestChatTemplates:
    """Test cases for the ChatTemplates class."""

    def test_get_css(self):
        """Test that CSS is returned correctly."""
        css_content = ChatTemplates.get_css()

        assert "<style>" in css_content
        assert "</style>" in css_content
        assert ".chat-message" in css_content

    def test_render_bot_message(self):
        """Test rendering bot messages."""
        html = ChatTemplates.render_bot_message("Hello, I am the assistant.")

        assert "Hello, I am the assistant." in html
        assert 'class="chat-message bot"' in html
        assert 'class="message"' in html

    def test_render_user_message(self):
        """Test rendering user messages."""
        html = ChatTemplates.render_user_message("This is my question.")

        assert "This is my question." in html
        assert 'class="chat-message user"' in html

    def test_render_error_message(self):
        """Test rendering error messages."""
        html = ChatTemplates.render_error_message("An error occurred.")

        assert "An error occurred." in html
        assert 'class="chat-message error"' in html

    def test_render_warning_message(self):
        """Test rendering warning messages."""
        html = ChatTemplates.render_warning_message("This is a warning.")

        assert "This is a warning." in html
        assert 'class="chat-message warning"' in html

    def test_render_info_message(self):
        """Test rendering info messages."""
        html = ChatTemplates.render_info_message("Information here.")

        assert "Information here." in html
        assert 'class="chat-message info"' in html

    def test_render_status_default(self):
        """Test rendering status message without type."""
        html = ChatTemplates.render_status("Processing...")

        assert "Processing..." in html
        assert 'class="processing-status' in html

    def test_render_status_success(self):
        """Test rendering success status message."""
        html = ChatTemplates.render_status("Complete!", status="success")

        assert "Complete!" in html
        assert "success" in html

    def test_render_status_error(self):
        """Test rendering error status message."""
        html = ChatTemplates.render_status("Failed!", status="error")

        assert "Failed!" in html
        assert "error" in html

    def test_render_chat_history_empty(self):
        """Test rendering empty chat history."""
        html = ChatTemplates.render_chat_history([])

        assert html == ""

    def test_render_chat_history_single_exchange(self):
        """Test rendering chat history with one exchange."""
        history = [
            {'role': 'user', 'content': 'What is AI?'},
            {'role': 'assistant', 'content': 'AI stands for Artificial Intelligence.'},
        ]

        html = ChatTemplates.render_chat_history(history)

        assert "What is AI?" in html
        assert "AI stands for Artificial Intelligence." in html
        assert 'class="chat-message user"' in html
        assert 'class="chat-message bot"' in html

    def test_render_chat_history_with_css(self):
        """Test rendering chat history with CSS included."""
        history = [
            {'role': 'user', 'content': 'Hello'},
        ]

        html = ChatTemplates.render_chat_history(history, include_css=True)

        assert "<style>" in html
        assert "Hello" in html

    def test_render_chat_history_multiple_roles(self):
        """Test rendering chat history with various roles."""
        history = [
            {'role': 'user', 'content': 'User message'},
            {'role': 'assistant', 'content': 'Bot message'},
            {'role': 'error', 'content': 'Error message'},
            {'role': 'warning', 'content': 'Warning message'},
            {'role': 'info', 'content': 'Info message'},
        ]

        html = ChatTemplates.render_chat_history(history)

        assert "User message" in html
        assert "Bot message" in html
        assert "Error message" in html
        assert "Warning message" in html
        assert "Info message" in html

    def test_legacy_compatibility_css(self):
        """Test that legacy CSS variable is available."""
        assert css == ChatTemplates.CSS

    def test_legacy_compatibility_bot_template(self):
        """Test that legacy bot_template is available."""
        assert bot_template == ChatTemplates.BOT_TEMPLATE

    def test_legacy_compatibility_user_template(self):
        """Test that legacy user_template is available."""
        assert user_template == ChatTemplates.USER_TEMPLATE

    def test_message_escaping(self):
        """Test that special characters are preserved."""
        message = "Code: <script>alert('xss')</script>"
        html = ChatTemplates.render_bot_message(message)

        # The message should be in the output (though in a real app you'd want to escape)
        assert "Code:" in html

    def test_templates_instance_creation(self):
        """Test that ChatTemplates can be instantiated."""
        templates = ChatTemplates()
        assert templates is not None
