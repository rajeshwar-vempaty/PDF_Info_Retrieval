"""
UI Templates module for Streamlit chat interface.

This module provides HTML/CSS templates for rendering chat messages
in the Streamlit application with consistent styling.
"""

from typing import Optional


class ChatTemplates:
    """
    Provides HTML/CSS templates for chat message display.

    This class contains all styling and template methods for rendering
    user and bot messages in a consistent, visually appealing format.

    Example:
        >>> templates = ChatTemplates()
        >>> html = templates.render_bot_message("Hello!")
        >>> st.write(html, unsafe_allow_html=True)
    """

    # Base CSS styles for chat interface
    CSS = '''
<style>
.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    background-color: #f0f0f0;
    color: #333;
}

.chat-message.bot {
    background-color: #e8f4f8;
    border-left: 4px solid #4a90a4;
}

.chat-message.user {
    background-color: #f0f0f0;
    border-left: 4px solid #6c757d;
}

.chat-message .message {
    padding: 0.5rem 1rem;
    flex-grow: 1;
    line-height: 1.5;
}

.chat-message .message p {
    margin: 0;
}

.chat-message.error {
    background-color: #fee;
    border-left: 4px solid #dc3545;
    color: #721c24;
}

.chat-message.warning {
    background-color: #fff3cd;
    border-left: 4px solid #ffc107;
    color: #856404;
}

.chat-message.info {
    background-color: #d1ecf1;
    border-left: 4px solid #17a2b8;
    color: #0c5460;
}

.processing-status {
    padding: 0.5rem 1rem;
    background-color: #e9ecef;
    border-radius: 0.25rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}

.processing-status.success {
    background-color: #d4edda;
    color: #155724;
}

.processing-status.error {
    background-color: #f8d7da;
    color: #721c24;
}
</style>
'''

    # Message templates
    BOT_TEMPLATE = '''
<div class="chat-message bot">
    <div class="message">{{MSG}}</div>
</div>
'''

    USER_TEMPLATE = '''
<div class="chat-message user">
    <div class="message">{{MSG}}</div>
</div>
'''

    ERROR_TEMPLATE = '''
<div class="chat-message error">
    <div class="message">{{MSG}}</div>
</div>
'''

    WARNING_TEMPLATE = '''
<div class="chat-message warning">
    <div class="message">{{MSG}}</div>
</div>
'''

    INFO_TEMPLATE = '''
<div class="chat-message info">
    <div class="message">{{MSG}}</div>
</div>
'''

    STATUS_TEMPLATE = '''
<div class="processing-status {{STATUS_CLASS}}">
    {{MSG}}
</div>
'''

    def __init__(self):
        """Initialize the chat templates."""
        pass

    @classmethod
    def get_css(cls) -> str:
        """
        Get the CSS styles for the chat interface.

        Returns:
            str: CSS styles as HTML string.
        """
        return cls.CSS

    @classmethod
    def render_bot_message(cls, message: str) -> str:
        """
        Render a bot/assistant message.

        Args:
            message: The message content to display.

        Returns:
            str: HTML string for the bot message.
        """
        return cls.BOT_TEMPLATE.replace("{{MSG}}", message)

    @classmethod
    def render_user_message(cls, message: str) -> str:
        """
        Render a user message.

        Args:
            message: The message content to display.

        Returns:
            str: HTML string for the user message.
        """
        return cls.USER_TEMPLATE.replace("{{MSG}}", message)

    @classmethod
    def render_error_message(cls, message: str) -> str:
        """
        Render an error message.

        Args:
            message: The error message content.

        Returns:
            str: HTML string for the error message.
        """
        return cls.ERROR_TEMPLATE.replace("{{MSG}}", message)

    @classmethod
    def render_warning_message(cls, message: str) -> str:
        """
        Render a warning message.

        Args:
            message: The warning message content.

        Returns:
            str: HTML string for the warning message.
        """
        return cls.WARNING_TEMPLATE.replace("{{MSG}}", message)

    @classmethod
    def render_info_message(cls, message: str) -> str:
        """
        Render an info message.

        Args:
            message: The info message content.

        Returns:
            str: HTML string for the info message.
        """
        return cls.INFO_TEMPLATE.replace("{{MSG}}", message)

    @classmethod
    def render_status(
        cls,
        message: str,
        status: Optional[str] = None
    ) -> str:
        """
        Render a processing status message.

        Args:
            message: The status message.
            status: Status type ('success', 'error', or None for default).

        Returns:
            str: HTML string for the status message.
        """
        status_class = status if status in ['success', 'error'] else ''
        return cls.STATUS_TEMPLATE.replace(
            "{{MSG}}", message
        ).replace("{{STATUS_CLASS}}", status_class)

    @classmethod
    def render_chat_history(
        cls,
        history: list,
        include_css: bool = False
    ) -> str:
        """
        Render complete chat history.

        Args:
            history: List of message dicts with 'role' and 'content' keys.
            include_css: If True, includes CSS in the output.

        Returns:
            str: Complete HTML for chat history.
        """
        html_parts = []

        if include_css:
            html_parts.append(cls.CSS)

        for message in history:
            role = message.get('role', 'user')
            content = message.get('content', '')

            if role == 'user':
                html_parts.append(cls.render_user_message(content))
            elif role == 'assistant':
                html_parts.append(cls.render_bot_message(content))
            elif role == 'error':
                html_parts.append(cls.render_error_message(content))
            elif role == 'warning':
                html_parts.append(cls.render_warning_message(content))
            else:
                html_parts.append(cls.render_info_message(content))

        return '\n'.join(html_parts)


# Legacy compatibility - expose templates directly
css = ChatTemplates.CSS
bot_template = ChatTemplates.BOT_TEMPLATE
user_template = ChatTemplates.USER_TEMPLATE
