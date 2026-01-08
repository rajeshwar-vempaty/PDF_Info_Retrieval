# 📚 PaperMind - AI-Powered Research Paper Analysis

<div align="center">

![PaperMind Banner](https://img.shields.io/badge/PaperMind-AI%20Research%20Assistant-8b5cf6?style=for-the-badge&logo=bookstack&logoColor=white)

[![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-ff4b4b?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.1.20-1c3c3c?style=flat-square)](https://langchain.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**Transform how you read research papers with AI-powered analysis**

[Live Demo](#demo) • [Features](#features) • [Installation](#installation) • [Usage](#usage)

</div>

---

## 🎯 Problem Statement

Reading research papers is challenging due to:
- 📖 **Technical Jargon**: Unfamiliar domain-specific terms and acronyms
- 📐 **Complex Equations**: Mathematical formulas without clear explanations
- 📊 **Dense Figures**: Charts and tables that need interpretation
- 📄 **Information Overload**: Long documents with scattered insights

**PaperMind solves these pain points** by providing an intelligent AI assistant that helps you understand any research paper quickly and thoroughly.

---

## ✨ Features

### 🔍 Smart Document Analysis
- **Automatic Section Detection**: Identifies Abstract, Introduction, Methods, Results, etc.
- **Technical Term Glossary**: Auto-detects jargon with AI-powered definitions
- **Figure & Table Extraction**: Lists all visual elements with explanations
- **Citation Analysis**: Tracks most referenced works

### 📐 Equation Explainer
- **Step-by-Step Breakdown**: Explains mathematical formulas in plain English
- **Variable Definitions**: Defines each symbol and its meaning
- **Context-Aware**: Uses paper context for accurate explanations

### 💬 Intelligent Q&A
- **Natural Language Queries**: Ask questions in plain English
- **Three Explanation Levels**: Brief, Detailed, or Expert responses
- **Source Citations**: Every answer includes relevant passages
- **Persistent Chat**: Conversation history maintained throughout session

### ⚡ Quick Actions
- **Summarize**: Get paper overview in seconds
- **Key Takeaways**: Extract main findings
- **Prerequisites**: Identify required background knowledge
- **Explain Equations**: Break down all mathematical content

### 🎨 Professional Dark Theme UI
- Modern, eye-friendly dark interface
- Three-panel layout for efficient navigation
- Reading progress tracking
- Export chat history as JSON

---

## 🖼️ Screenshots

<div align="center">

| Welcome Screen | Document Analysis |
|:---:|:---:|
| Upload papers and get started | View sections, terms, and figures |

| AI Chat | Equation Explainer |
|:---:|:---:|
| Ask questions, get cited answers | Step-by-step math breakdowns |

</div>

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API Key

### Installation

```bash
# Clone the repository
git clone https://github.com/rajeshwar-vempaty/PDF_Info_Retrieval.git
cd PDF_Info_Retrieval

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Run the App

```bash
# Standard version
streamlit run app.py

# Enhanced version with dark theme
streamlit run app_enhanced.py
```

Visit `http://localhost:8501` in your browser.

---

## 📁 Project Structure

```
PDF_Info_Retrieval/
├── app.py                      # Standard Streamlit application
├── app_enhanced.py             # Enhanced version with dark theme
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .env.example               # Environment template
│
├── src/                       # Source modules
│   ├── __init__.py
│   ├── config.py              # Configuration settings
│   ├── pdf_processor.py       # PDF text extraction
│   ├── text_processor.py      # Text cleaning & chunking
│   ├── vector_store.py        # FAISS vector store
│   ├── conversation.py        # LangChain conversation
│   ├── document_analyzer.py   # Basic document analysis
│   ├── paper_analyzer.py      # Advanced paper analysis
│   │
│   └── ui/                    # UI components
│       ├── __init__.py
│       ├── templates.py       # Chat templates
│       └── dark_theme.py      # Dark theme styling
│
├── tests/                     # Test suite
│   └── ...
│
└── .streamlit/
    └── config.toml            # Streamlit configuration
```

---

## 🔧 Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chunk_size` | 1500 | Text chunk size for processing |
| `llm_model_name` | gpt-3.5-turbo | OpenAI model to use |
| `llm_temperature` | 0.7 | Response creativity (0-1) |
| `embedding_model_type` | openai | Embedding model type |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PaperMind                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │   PDF    │───▶│  Text    │───▶│  Vector  │───▶│  FAISS   │  │
│  │ Processor│    │ Processor│    │  Store   │    │  Index   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                        │         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │         │
│  │  Paper   │    │ Document │    │   Dark   │         │         │
│  │ Analyzer │    │ Analyzer │    │  Theme   │         │         │
│  └──────────┘    └──────────┘    └──────────┘         │         │
│       │               │               │               │         │
│       └───────────────┴───────────────┴───────────────┘         │
│                               │                                  │
│                               ▼                                  │
│                    ┌──────────────────┐                         │
│                    │   Conversation   │                         │
│                    │     Manager      │                         │
│                    │   (LangChain)    │                         │
│                    └──────────────────┘                         │
│                               │                                  │
│                               ▼                                  │
│                    ┌──────────────────┐                         │
│                    │   OpenAI GPT    │                          │
│                    └──────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_paper_analyzer.py -v
```

---

## 🌐 Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add secrets in Streamlit Cloud dashboard:
   ```toml
   OPENAI_API_KEY = "your-api-key"
   ```
5. Deploy!

### Docker

```bash
docker build -t papermind .
docker run -p 8501:8501 -e OPENAI_API_KEY=your-key papermind
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) - LLM application framework
- [Streamlit](https://streamlit.io/) - Web application framework
- [OpenAI](https://openai.com/) - Language models
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search

---

<div align="center">

**Built with ❤️ by [Rajeshwar Vempaty](https://github.com/rajeshwar-vempaty)**

⭐ Star this repo if you find it helpful!

</div>
