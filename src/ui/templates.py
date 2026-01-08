"""
UI Templates module for Streamlit chat interface.

This module provides HTML/CSS templates for rendering chat messages
and UI components with professional styling.
"""

from typing import Optional, List, Dict


class ChatTemplates:
    """
    Provides HTML/CSS templates for professional chat interface.
    """

    CSS = '''
<style>
/* Global Styles */
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}

.main-header h1 {
    margin: 0;
    font-size: 2.5rem;
}

.main-header p {
    margin: 0.5rem 0 0 0;
    opacity: 0.9;
}

/* Chat Container */
.chat-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 10px;
    margin-bottom: 1rem;
}

/* Chat Messages */
.chat-message {
    padding: 1rem 1.25rem;
    border-radius: 15px;
    margin-bottom: 1rem;
    display: flex;
    align-items: flex-start;
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.chat-message.user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    margin-left: 20%;
    border-bottom-right-radius: 5px;
}

.chat-message.bot {
    background: white;
    color: #333;
    margin-right: 20%;
    border-bottom-left-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.chat-message .avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    margin-right: 1rem;
    flex-shrink: 0;
}

.chat-message.user .avatar {
    background: rgba(255,255,255,0.2);
    order: 2;
    margin-right: 0;
    margin-left: 1rem;
}

.chat-message.bot .avatar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.chat-message .message {
    flex-grow: 1;
    line-height: 1.6;
}

.chat-message .message p {
    margin: 0;
}

/* Stats Cards */
.stats-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.stat-card {
    background: white;
    padding: 1.25rem;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    transition: transform 0.2s;
}

.stat-card:hover {
    transform: translateY(-2px);
}

.stat-card .stat-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.stat-card .stat-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
}

.stat-card .stat-label {
    font-size: 0.85rem;
    color: #666;
    margin-top: 0.25rem;
}

/* Keywords */
.keywords-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.keyword-tag {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.35rem 0.75rem;
    border-radius: 20px;
    font-size: 0.85rem;
    display: inline-block;
}

/* Suggested Questions */
.suggested-questions {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 10px;
    margin-top: 1rem;
}

.suggested-questions h4 {
    margin: 0 0 0.75rem 0;
    color: #333;
}

.question-chip {
    background: white;
    border: 1px solid #ddd;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    margin: 0.25rem;
    display: inline-block;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.9rem;
}

.question-chip:hover {
    background: #667eea;
    color: white;
    border-color: #667eea;
}

/* Analysis Panel */
.analysis-panel {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    margin-bottom: 1rem;
}

.analysis-panel h3 {
    margin: 0 0 1rem 0;
    color: #333;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Alert Messages */
.chat-message.error {
    background: #fff5f5;
    border-left: 4px solid #dc3545;
    color: #721c24;
    margin: 0;
    border-radius: 5px;
}

.chat-message.warning {
    background: #fff9e6;
    border-left: 4px solid #ffc107;
    color: #856404;
    margin: 0;
    border-radius: 5px;
}

.chat-message.info {
    background: #e7f3ff;
    border-left: 4px solid #17a2b8;
    color: #0c5460;
    margin: 0;
    border-radius: 5px;
}

.chat-message.success {
    background: #e8f5e9;
    border-left: 4px solid #28a745;
    color: #155724;
    margin: 0;
    border-radius: 5px;
}

/* Source Citations */
.source-citation {
    background: #f8f9fa;
    border-left: 3px solid #667eea;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    border-radius: 0 5px 5px 0;
    font-size: 0.9rem;
}

.source-citation .source-header {
    font-weight: bold;
    color: #667eea;
    margin-bottom: 0.25rem;
}

/* Footer */
.app-footer {
    text-align: center;
    padding: 1rem;
    color: #666;
    font-size: 0.85rem;
    margin-top: 2rem;
}

.app-footer a {
    color: #667eea;
    text-decoration: none;
}
</style>
'''

    BOT_TEMPLATE = '''
<div class="chat-message bot">
    <div class="avatar">🤖</div>
    <div class="message">{{MSG}}</div>
</div>
'''

    USER_TEMPLATE = '''
<div class="chat-message user">
    <div class="avatar">👤</div>
    <div class="message">{{MSG}}</div>
</div>
'''

    ERROR_TEMPLATE = '''
<div class="chat-message error">
    <div class="message">⚠️ {{MSG}}</div>
</div>
'''

    WARNING_TEMPLATE = '''
<div class="chat-message warning">
    <div class="message">💡 {{MSG}}</div>
</div>
'''

    INFO_TEMPLATE = '''
<div class="chat-message info">
    <div class="message">ℹ️ {{MSG}}</div>
</div>
'''

    SUCCESS_TEMPLATE = '''
<div class="chat-message success">
    <div class="message">✅ {{MSG}}</div>
</div>
'''

    @classmethod
    def get_css(cls) -> str:
        return cls.CSS

    @classmethod
    def render_bot_message(cls, message: str) -> str:
        return cls.BOT_TEMPLATE.replace("{{MSG}}", message)

    @classmethod
    def render_user_message(cls, message: str) -> str:
        return cls.USER_TEMPLATE.replace("{{MSG}}", message)

    @classmethod
    def render_error_message(cls, message: str) -> str:
        return cls.ERROR_TEMPLATE.replace("{{MSG}}", message)

    @classmethod
    def render_warning_message(cls, message: str) -> str:
        return cls.WARNING_TEMPLATE.replace("{{MSG}}", message)

    @classmethod
    def render_info_message(cls, message: str) -> str:
        return cls.INFO_TEMPLATE.replace("{{MSG}}", message)

    @classmethod
    def render_success_message(cls, message: str) -> str:
        return cls.SUCCESS_TEMPLATE.replace("{{MSG}}", message)

    @classmethod
    def render_stats_cards(cls, stats: Dict) -> str:
        """Render statistics cards."""
        cards_html = '<div class="stats-container">'

        icons = {
            'pages': '📄',
            'words': '📝',
            'characters': '🔤',
            'reading_time': '⏱️',
            'chunks': '📦',
            'sentences': '💬'
        }

        for key, value in stats.items():
            icon = icons.get(key, '📊')
            label = key.replace('_', ' ').title()
            cards_html += f'''
            <div class="stat-card">
                <div class="stat-icon">{icon}</div>
                <div class="stat-value">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
            '''

        cards_html += '</div>'
        return cards_html

    @classmethod
    def render_keywords(cls, keywords: List[str]) -> str:
        """Render keyword tags."""
        html = '<div class="keywords-container">'
        for keyword in keywords[:15]:  # Limit to 15 keywords
            html += f'<span class="keyword-tag">{keyword}</span>'
        html += '</div>'
        return html

    @classmethod
    def render_suggested_questions(cls, questions: List[str]) -> str:
        """Render suggested questions."""
        html = '<div class="suggested-questions"><h4>💡 Suggested Questions:</h4>'
        for q in questions:
            html += f'<span class="question-chip">{q}</span>'
        html += '</div>'
        return html

    @classmethod
    def render_source_citation(cls, index: int, content: str) -> str:
        """Render a source citation."""
        return f'''
        <div class="source-citation">
            <div class="source-header">Source {index}</div>
            <div>{content}</div>
        </div>
        '''


# Legacy compatibility
css = ChatTemplates.CSS
bot_template = ChatTemplates.BOT_TEMPLATE
user_template = ChatTemplates.USER_TEMPLATE
