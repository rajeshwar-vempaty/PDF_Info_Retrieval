"""
Dark Theme UI Templates for PaperMind.

Professional dark theme styling inspired by modern research tools.
"""

from typing import List, Dict, Optional


class DarkTheme:
    """
    Dark theme CSS and HTML templates for PaperMind interface.
    """

    # Color Palette
    COLORS = {
        'bg_primary': '#0f172a',      # slate-950
        'bg_secondary': '#1e293b',    # slate-800
        'bg_tertiary': '#334155',     # slate-700
        'text_primary': '#f1f5f9',    # slate-100
        'text_secondary': '#94a3b8',  # slate-400
        'text_muted': '#64748b',      # slate-500
        'accent_primary': '#8b5cf6',  # violet-500
        'accent_secondary': '#a855f7', # fuchsia-500
        'border': '#334155',          # slate-700
        'success': '#22c55e',         # green-500
        'warning': '#f59e0b',         # amber-500
        'error': '#ef4444',           # red-500
        'info': '#3b82f6',            # blue-500
    }

    CSS = '''
<style>
/* ==================== GLOBAL STYLES ==================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    background-color: #0f172a !important;
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #1e293b;
}

::-webkit-scrollbar-thumb {
    background: #475569;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #64748b;
}

/* ==================== HEADER ==================== */
.app-header {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-bottom: 1px solid #334155;
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: -1rem -1rem 1rem -1rem;
}

.app-logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.logo-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
}

.app-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #f1f5f9;
    margin: 0;
}

.app-subtitle {
    font-size: 0.875rem;
    color: #64748b;
    margin: 0;
}

/* ==================== PANELS ==================== */
.panel {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    overflow: hidden;
}

.panel-header {
    background: #0f172a;
    padding: 1rem;
    border-bottom: 1px solid #334155;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.panel-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.panel-content {
    padding: 1rem;
    max-height: 70vh;
    overflow-y: auto;
}

/* ==================== NAVIGATION TABS ==================== */
.nav-tabs {
    display: flex;
    border-bottom: 1px solid #334155;
    background: #0f172a;
}

.nav-tab {
    flex: 1;
    padding: 0.75rem;
    text-align: center;
    font-size: 0.75rem;
    font-weight: 500;
    color: #64748b;
    cursor: pointer;
    transition: all 0.2s;
    border-bottom: 2px solid transparent;
}

.nav-tab:hover {
    color: #94a3b8;
    background: rgba(139, 92, 246, 0.1);
}

.nav-tab.active {
    color: #8b5cf6;
    border-bottom-color: #8b5cf6;
    background: rgba(139, 92, 246, 0.1);
}

.nav-tab-icon {
    font-size: 1rem;
    margin-bottom: 0.25rem;
}

/* ==================== SECTIONS LIST ==================== */
.section-item {
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    background: rgba(51, 65, 85, 0.3);
}

.section-item:hover {
    background: rgba(139, 92, 246, 0.15);
}

.section-item.active {
    background: rgba(139, 92, 246, 0.2);
    border-left: 3px solid #8b5cf6;
}

.section-title {
    font-size: 0.875rem;
    color: #f1f5f9;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
}

.section-page {
    font-size: 0.75rem;
    color: #64748b;
}

.progress-bar {
    height: 3px;
    background: #334155;
    border-radius: 2px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #8b5cf6 0%, #a855f7 100%);
    border-radius: 2px;
    transition: width 0.3s;
}

/* ==================== GLOSSARY TERMS ==================== */
.term-card {
    background: rgba(51, 65, 85, 0.3);
    border-radius: 8px;
    padding: 0.875rem;
    margin-bottom: 0.5rem;
    transition: all 0.2s;
}

.term-card:hover {
    background: rgba(51, 65, 85, 0.5);
}

.term-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.term-name {
    font-size: 0.875rem;
    font-weight: 500;
    color: #a78bfa;
}

.term-frequency {
    font-size: 0.75rem;
    color: #64748b;
    background: rgba(100, 116, 139, 0.3);
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
}

.term-definition {
    font-size: 0.8rem;
    color: #94a3b8;
    line-height: 1.5;
}

.term-action {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: #8b5cf6;
    display: flex;
    align-items: center;
    gap: 0.25rem;
    opacity: 0;
    transition: opacity 0.2s;
}

.term-card:hover .term-action {
    opacity: 1;
}

/* ==================== FIGURES & TABLES ==================== */
.figure-card {
    background: rgba(51, 65, 85, 0.3);
    border-radius: 8px;
    padding: 0.875rem;
    margin-bottom: 0.5rem;
    display: flex;
    gap: 0.75rem;
    transition: all 0.2s;
}

.figure-card:hover {
    background: rgba(51, 65, 85, 0.5);
}

.figure-thumbnail {
    width: 50px;
    height: 50px;
    background: #334155;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    flex-shrink: 0;
}

.figure-info {
    flex: 1;
    min-width: 0;
}

.figure-type {
    font-size: 0.7rem;
    padding: 0.125rem 0.375rem;
    border-radius: 4px;
    display: inline-block;
    margin-right: 0.5rem;
}

.figure-type.figure {
    background: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
}

.figure-type.table {
    background: rgba(34, 197, 94, 0.2);
    color: #4ade80;
}

.figure-type.equation {
    background: rgba(249, 115, 22, 0.2);
    color: #fb923c;
}

.figure-title {
    font-size: 0.875rem;
    color: #f1f5f9;
    margin-top: 0.25rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ==================== CHAT INTERFACE ==================== */
.chat-container {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.chat-message {
    display: flex;
    gap: 0.75rem;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.message-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 0.875rem;
}

.message-avatar.ai {
    background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
}

.message-avatar.user {
    background: #334155;
}

.message-content {
    flex: 1;
    min-width: 0;
}

.message-bubble {
    padding: 0.875rem 1rem;
    border-radius: 12px;
    font-size: 0.875rem;
    line-height: 1.6;
}

.message-bubble.ai {
    background: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
}

.message-bubble.user {
    background: rgba(139, 92, 246, 0.2);
    color: #e0e7ff;
    margin-left: auto;
    max-width: 85%;
}

.message-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.message-action-btn {
    padding: 0.25rem;
    color: #64748b;
    cursor: pointer;
    transition: color 0.2s;
}

.message-action-btn:hover {
    color: #94a3b8;
}

/* Source Citation */
.source-citation {
    background: rgba(15, 23, 42, 0.5);
    border-left: 2px solid #8b5cf6;
    padding: 0.5rem 0.75rem;
    margin-top: 0.5rem;
    border-radius: 0 6px 6px 0;
    font-size: 0.8rem;
}

.source-link {
    color: #64748b;
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
}

.source-link:hover {
    color: #8b5cf6;
}

/* ==================== QUICK ACTIONS ==================== */
.quick-actions {
    background: rgba(30, 41, 59, 0.5);
    border-bottom: 1px solid #334155;
    padding: 0.75rem;
}

.quick-actions-title {
    font-size: 0.75rem;
    color: #64748b;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.quick-actions-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
}

.quick-action-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    color: #f1f5f9;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s;
}

.quick-action-btn:hover {
    background: #334155;
    border-color: #8b5cf6;
}

.quick-action-icon {
    font-size: 0.875rem;
}

.quick-action-icon.purple { color: #a78bfa; }
.quick-action-icon.blue { color: #60a5fa; }
.quick-action-icon.yellow { color: #fbbf24; }
.quick-action-icon.pink { color: #f472b6; }

/* ==================== SUMMARY LEVEL TOGGLE ==================== */
.summary-toggle {
    display: flex;
    background: #1e293b;
    border-radius: 8px;
    padding: 0.25rem;
    margin-bottom: 1rem;
}

.summary-toggle-btn {
    flex: 1;
    padding: 0.5rem;
    text-align: center;
    font-size: 0.75rem;
    font-weight: 500;
    color: #64748b;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
}

.summary-toggle-btn:hover {
    color: #94a3b8;
}

.summary-toggle-btn.active {
    background: #8b5cf6;
    color: white;
}

/* ==================== SUGGESTED QUESTIONS ==================== */
.suggested-questions {
    background: rgba(30, 41, 59, 0.5);
    border-top: 1px solid #334155;
    padding: 0.75rem;
}

.suggested-questions-title {
    font-size: 0.75rem;
    color: #64748b;
    margin-bottom: 0.5rem;
}

.question-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
}

.question-chip {
    padding: 0.375rem 0.75rem;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 20px;
    font-size: 0.75rem;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.2s;
}

.question-chip:hover {
    background: #334155;
    color: #f1f5f9;
    border-color: #8b5cf6;
}

/* ==================== CHAT INPUT ==================== */
.chat-input-container {
    padding: 0.75rem;
    border-top: 1px solid #334155;
    background: #0f172a;
}

.chat-input-wrapper {
    position: relative;
}

.chat-input {
    width: 100%;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 0.875rem 4rem 0.875rem 1rem;
    color: #f1f5f9;
    font-size: 0.875rem;
    resize: none;
    outline: none;
    transition: border-color 0.2s;
}

.chat-input:focus {
    border-color: #8b5cf6;
}

.chat-input::placeholder {
    color: #64748b;
}

.chat-input-actions {
    position: absolute;
    right: 0.5rem;
    bottom: 0.5rem;
    display: flex;
    gap: 0.25rem;
}

.chat-send-btn {
    padding: 0.5rem;
    background: #8b5cf6;
    border: none;
    border-radius: 8px;
    color: white;
    cursor: pointer;
    transition: background 0.2s;
}

.chat-send-btn:hover {
    background: #7c3aed;
}

/* ==================== EQUATION EXPLANATION ==================== */
.equation-box {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.75rem 0;
}

.equation-display {
    font-family: 'Courier New', monospace;
    font-size: 1.1rem;
    color: #f1f5f9;
    text-align: center;
    padding: 0.75rem;
    background: #0f172a;
    border-radius: 6px;
    margin-bottom: 0.75rem;
}

.equation-variables {
    background: rgba(30, 41, 59, 0.5);
    border-radius: 6px;
    padding: 0.75rem;
    margin-bottom: 0.75rem;
}

.equation-variables-title {
    font-size: 0.75rem;
    color: #64748b;
    margin-bottom: 0.5rem;
}

.equation-var {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
    margin-bottom: 0.25rem;
}

.equation-var-name {
    padding: 0.125rem 0.375rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
}

.equation-var-name.blue {
    background: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
}

.equation-var-name.green {
    background: rgba(34, 197, 94, 0.2);
    color: #4ade80;
}

.equation-var-name.orange {
    background: rgba(249, 115, 22, 0.2);
    color: #fb923c;
}

.equation-var-name.pink {
    background: rgba(236, 72, 153, 0.2);
    color: #f472b6;
}

.equation-var-desc {
    color: #94a3b8;
}

.equation-steps {
    margin-top: 0.75rem;
}

.equation-step {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.8rem;
}

.equation-step-num {
    width: 20px;
    height: 20px;
    background: rgba(139, 92, 246, 0.3);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #a78bfa;
    font-size: 0.7rem;
    flex-shrink: 0;
}

.equation-step-text {
    color: #94a3b8;
}

/* ==================== STATUS BAR ==================== */
.status-bar {
    background: #0f172a;
    border-top: 1px solid #334155;
    padding: 0.5rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.75rem;
    color: #64748b;
    margin: 1rem -1rem -1rem -1rem;
}

.status-stats {
    display: flex;
    gap: 1.5rem;
}

.status-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.status-dot {
    width: 8px;
    height: 8px;
    background: #22c55e;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* ==================== WELCOME SCREEN ==================== */
.welcome-container {
    text-align: center;
    padding: 3rem 1rem;
}

.welcome-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
}

.welcome-title {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
}

.welcome-subtitle {
    font-size: 1.25rem;
    color: #64748b;
    margin-bottom: 1.5rem;
}

.welcome-description {
    color: #94a3b8;
    max-width: 600px;
    margin: 0 auto 2rem;
    line-height: 1.6;
}

/* Feature Cards */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    max-width: 800px;
    margin: 0 auto;
}

.feature-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s;
}

.feature-card:hover {
    border-color: #8b5cf6;
    transform: translateY(-2px);
}

.feature-icon {
    font-size: 2rem;
    margin-bottom: 0.75rem;
}

.feature-title {
    font-size: 1rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 0.5rem;
}

.feature-desc {
    font-size: 0.875rem;
    color: #94a3b8;
}

/* ==================== READING STATS ==================== */
.reading-stats {
    background: rgba(51, 65, 85, 0.3);
    border-radius: 8px;
    padding: 0.875rem;
    margin-top: 1rem;
}

.reading-stats-title {
    font-size: 0.75rem;
    color: #64748b;
    margin-bottom: 0.5rem;
}

.reading-stats-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
}

.reading-stats-value {
    color: #f1f5f9;
}

.reading-stats-label {
    color: #64748b;
}

/* ==================== STREAMLIT OVERRIDES ==================== */
.stButton > button {
    background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

.stTextInput > div > div > input {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
}

.stTextInput > div > div > input:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 1px #8b5cf6 !important;
}

.stSelectbox > div > div {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: #0f172a !important;
    gap: 0 !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748b !important;
    border-bottom: 2px solid transparent !important;
}

.stTabs [aria-selected="true"] {
    color: #8b5cf6 !important;
    border-bottom-color: #8b5cf6 !important;
}

.stExpander {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}

div[data-testid="stExpander"] details summary span {
    color: #f1f5f9 !important;
}

.stAlert {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
}

.stMarkdown {
    color: #f1f5f9 !important;
}

div[data-testid="stMetric"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}

div[data-testid="stMetricValue"] {
    color: #8b5cf6 !important;
}

div[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}

/* File uploader */
.stFileUploader {
    background: #1e293b !important;
    border: 2px dashed #334155 !important;
    border-radius: 12px !important;
}

.stFileUploader:hover {
    border-color: #8b5cf6 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #1e293b !important;
    border-right: 1px solid #334155 !important;
}

section[data-testid="stSidebar"] .stMarkdown {
    color: #f1f5f9 !important;
}
</style>
'''

    @classmethod
    def get_css(cls) -> str:
        return cls.CSS

    @classmethod
    def render_header(cls, filename: str = None) -> str:
        """Render the app header."""
        file_display = f'<span style="color: #64748b; font-size: 0.875rem;">| {filename}</span>' if filename else ''
        return f'''
        <div class="app-header">
            <div class="app-logo">
                <div class="logo-icon">📄</div>
                <div>
                    <h1 class="app-title">PaperMind {file_display}</h1>
                    <p class="app-subtitle">AI-Powered Research Paper Analysis</p>
                </div>
            </div>
        </div>
        '''

    @classmethod
    def render_welcome(cls) -> str:
        """Render welcome screen."""
        return '''
        <div class="welcome-container">
            <div class="welcome-icon">📚</div>
            <h1 class="welcome-title">PaperMind</h1>
            <p class="welcome-subtitle">AI-Powered Research Paper Analysis</p>
            <p class="welcome-description">
                Upload your research papers and let AI help you understand complex concepts,
                equations, and terminology. Get instant explanations, summaries, and insights.
            </p>
        </div>
        '''

    @classmethod
    def render_features(cls) -> str:
        """Render feature cards."""
        return '''
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">📖</div>
                <h3 class="feature-title">Glossary & Terms</h3>
                <p class="feature-desc">Auto-detect technical terms with AI-powered definitions</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📐</div>
                <h3 class="feature-title">Equation Explainer</h3>
                <p class="feature-desc">Step-by-step breakdown of mathematical formulas</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3 class="feature-title">Figure Analysis</h3>
                <p class="feature-desc">Understand charts, tables, and visualizations</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <h3 class="feature-title">Smart Q&A</h3>
                <p class="feature-desc">Ask questions in plain language, get accurate answers</p>
            </div>
        </div>
        '''

    @classmethod
    def render_section_item(cls, section, is_active: bool = False) -> str:
        """Render a section navigation item."""
        active_class = 'active' if is_active else ''
        return f'''
        <div class="section-item {active_class}">
            <div class="section-title">
                <span>{section.title}</span>
                <span class="section-page">p.{section.page}</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {section.progress}%"></div>
            </div>
        </div>
        '''

    @classmethod
    def render_term_card(cls, term) -> str:
        """Render a glossary term card."""
        return f'''
        <div class="term-card">
            <div class="term-header">
                <span class="term-name">{term.term}</span>
                <span class="term-frequency">{term.frequency}x</span>
            </div>
            <p class="term-definition">{term.definition or term.context[:100] + "..." if term.context else "Click to get AI explanation"}</p>
            <div class="term-action">✨ Explain more</div>
        </div>
        '''

    @classmethod
    def render_figure_card(cls, figure) -> str:
        """Render a figure/table/equation card."""
        icons = {'figure': '📊', 'table': '📋', 'equation': '∑'}
        icon = icons.get(figure.type, '📄')
        return f'''
        <div class="figure-card">
            <div class="figure-thumbnail">{icon}</div>
            <div class="figure-info">
                <span class="figure-type {figure.type}">{figure.type}</span>
                <span class="section-page">p.{figure.page}</span>
                <div class="figure-title">{figure.title}</div>
            </div>
        </div>
        '''

    @classmethod
    def render_ai_message(cls, content: str, sources: List[str] = None) -> str:
        """Render an AI chat message."""
        sources_html = ''
        if sources:
            sources_html = '<div class="source-citation">'
            for i, source in enumerate(sources[:2]):
                sources_html += f'<div class="source-link">📍 Source {i+1}: {source[:100]}...</div>'
            sources_html += '</div>'

        return f'''
        <div class="chat-message">
            <div class="message-avatar ai">✨</div>
            <div class="message-content">
                <div class="message-bubble ai">
                    {content}
                    {sources_html}
                </div>
                <div class="message-actions">
                    <span class="message-action-btn">👍</span>
                    <span class="message-action-btn">👎</span>
                    <span class="message-action-btn">📋</span>
                </div>
            </div>
        </div>
        '''

    @classmethod
    def render_user_message(cls, content: str) -> str:
        """Render a user chat message."""
        return f'''
        <div class="chat-message" style="justify-content: flex-end;">
            <div class="message-bubble user">{content}</div>
        </div>
        '''

    @classmethod
    def render_equation_explanation(cls, equation: str, explanation: Dict) -> str:
        """Render an equation explanation."""
        vars_html = ''
        colors = ['blue', 'green', 'orange', 'pink']
        for i, var in enumerate(explanation.get('variables', [])):
            color = colors[i % len(colors)]
            parts = var.split(':', 1) if ':' in var else [var, '']
            vars_html += f'''
            <div class="equation-var">
                <code class="equation-var-name {color}">{parts[0].strip()}</code>
                <span class="equation-var-desc">{parts[1].strip() if len(parts) > 1 else ''}</span>
            </div>
            '''

        steps_html = ''
        for i, step in enumerate(explanation.get('steps', []), 1):
            steps_html += f'''
            <div class="equation-step">
                <span class="equation-step-num">{i}</span>
                <span class="equation-step-text">{step}</span>
            </div>
            '''

        return f'''
        <div class="equation-box">
            <div class="equation-display">{equation}</div>
            <p style="color: #f1f5f9; font-size: 0.875rem; margin-bottom: 0.75rem;">
                {explanation.get('explanation', '')}
            </p>
            <div class="equation-variables">
                <div class="equation-variables-title">Variables:</div>
                {vars_html}
            </div>
            <div class="equation-steps">
                {steps_html}
            </div>
        </div>
        '''

    @classmethod
    def render_quick_actions(cls) -> str:
        """Render quick action buttons."""
        return '''
        <div class="quick-actions">
            <div class="quick-actions-title">Quick Actions</div>
            <div class="quick-actions-grid">
                <div class="quick-action-btn">
                    <span class="quick-action-icon purple">✨</span>
                    Summarize this page
                </div>
                <div class="quick-action-btn">
                    <span class="quick-action-icon blue">📐</span>
                    Explain equations
                </div>
                <div class="quick-action-btn">
                    <span class="quick-action-icon yellow">💡</span>
                    Key takeaways
                </div>
                <div class="quick-action-btn">
                    <span class="quick-action-icon pink">🧠</span>
                    Prerequisites
                </div>
            </div>
        </div>
        '''

    @classmethod
    def render_suggested_questions(cls, questions: List[str]) -> str:
        """Render suggested question chips."""
        chips_html = ''
        for q in questions[:5]:
            chips_html += f'<span class="question-chip">{q}</span>'

        return f'''
        <div class="suggested-questions">
            <div class="suggested-questions-title">Suggested questions:</div>
            <div class="question-chips">
                {chips_html}
            </div>
        </div>
        '''

    @classmethod
    def render_status_bar(cls, stats: Dict) -> str:
        """Render the status bar."""
        return f'''
        <div class="status-bar">
            <div class="status-stats">
                <span class="status-item">📄 {stats.get('pages', 'N/A')} pages</span>
                <span class="status-item">📝 {stats.get('words', 'N/A')} words</span>
                <span class="status-item">📊 {stats.get('figures', 0)} figures</span>
                <span class="status-item">📋 {stats.get('tables', 0)} tables</span>
            </div>
            <div class="status-indicator">
                <span class="status-dot"></span>
                <span>AI Ready</span>
            </div>
        </div>
        '''

    @classmethod
    def render_reading_stats(cls, percent: int, time_left: str) -> str:
        """Render reading progress stats."""
        return f'''
        <div class="reading-stats">
            <div class="reading-stats-title">Reading Progress</div>
            <div class="reading-stats-row">
                <span class="reading-stats-value">{percent}% complete</span>
                <span class="reading-stats-label">~{time_left} left</span>
            </div>
        </div>
        '''
