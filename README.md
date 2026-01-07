# PDF Info Retrieval

**Interactive PDF Knowledge Extraction System**

A RAG (Retrieval-Augmented Generation) based application for extracting and querying information from PDF research documents. Upload your PDFs, and ask questions about their content using natural language.

## Features

- **Multi-PDF Support**: Upload and process multiple PDF documents simultaneously
- **Academic-Aware Processing**: Intelligent text chunking that respects research paper sections (Abstract, Introduction, Methods, Results, Discussion, Conclusion)
- **Conversational Interface**: Ask follow-up questions with context maintained across the conversation
- **Flexible Embeddings**: Choose between OpenAI or HuggingFace embedding models
- **Smart Text Cleaning**: Removes noise like email addresses, figure captions, and non-ASCII characters
- **Response Validation**: Filters out irrelevant or too-short responses

## Project Structure

```
PDF_Info_Retrieval/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── .env.example               # Example environment configuration
├── .gitignore                 # Git ignore rules
│
├── src/                       # Source code modules
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration and settings
│   ├── pdf_processor.py      # PDF text extraction
│   ├── text_processor.py     # Text cleaning and chunking
│   ├── vector_store.py       # Vector store management
│   ├── conversation.py       # Conversation chain handling
│   │
│   └── ui/                   # UI components
│       ├── __init__.py
│       └── templates.py      # HTML/CSS templates
│
└── tests/                    # Test suite
    ├── __init__.py
    ├── test_config.py
    ├── test_pdf_processor.py
    ├── test_text_processor.py
    ├── test_vector_store.py
    ├── test_conversation.py
    └── test_ui_templates.py
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/PDF_Info_Retrieval.git
   cd PDF_Info_Retrieval
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your-openai-api-key
   HUGGINGFACEHUB_API_TOKEN=your-huggingface-token  # Optional
   ```

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

### Using the Application

1. **Upload PDFs**: Use the sidebar to upload one or more PDF documents
2. **Process Documents**: Click the "Process" button to extract and index the content
3. **Ask Questions**: Type your questions in the main input field
4. **View Responses**: The AI will provide answers based on the document content

### Example Questions

- "What are the main findings of this research?"
- "Summarize the methodology used in the study"
- "What conclusions did the authors draw?"
- "Explain the results section"

## Configuration

The application can be configured through the `src/config.py` module:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chunk_size` | 1500 | Maximum characters per text chunk |
| `min_response_length` | 30 | Minimum response length for relevance |
| `embedding_model_type` | "openai" | Embedding model ("openai" or "huggingface") |
| `llm_model_name` | "gpt-3.5-turbo" | LLM model for conversation |
| `llm_temperature` | 0.7 | LLM temperature setting |

## Architecture

### RAG Pipeline

```
PDF Upload → Extract Text → Clean & Chunk → Create Embeddings → FAISS Vector Store
                                                                        ↓
User Question → Retrieve Similar Chunks → Generate Response with Context
```

### Components

1. **PDFProcessor**: Extracts raw text from PDF files using pdfplumber
2. **TextProcessor**: Cleans text and splits it into chunks
3. **VectorStoreManager**: Creates and manages FAISS vector store
4. **ConversationManager**: Handles the conversational retrieval chain

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_text_processor.py

# Run with verbose output
pytest -v
```

## API Reference

### PDFProcessor

```python
from src.pdf_processor import PDFProcessor

processor = PDFProcessor()
text = processor.extract_text_from_files(pdf_files)
summary = processor.get_processing_summary()
```

### TextProcessor

```python
from src.text_processor import TextProcessor

processor = TextProcessor()
cleaned = processor.clean_text(raw_text)
chunks = processor.create_chunks(cleaned)
stats = processor.get_stats(raw_text)
```

### VectorStoreManager

```python
from src.vector_store import VectorStoreManager

manager = VectorStoreManager()
vectorstore = manager.create_vectorstore(text_chunks)
results = manager.similarity_search("query", k=4)
```

### ConversationManager

```python
from src.conversation import ConversationManager

manager = ConversationManager()
chain = manager.create_chain(vectorstore)
response = manager.ask("What is the main topic?")
```

## Dependencies

### Core
- **Streamlit**: Web application framework
- **LangChain**: LLM application framework
- **OpenAI**: GPT language models and embeddings

### PDF Processing
- **pdfplumber**: PDF text extraction

### Vector Search
- **FAISS**: Efficient similarity search

### Embeddings
- **Sentence Transformers**: Alternative embedding models
- **HuggingFace Hub**: Model repository access

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not found"**
   - Ensure `.env` file exists with valid API key
   - Check that `python-dotenv` is installed

2. **"Failed to process PDF"**
   - Verify PDF is not corrupted or password-protected
   - Check that PDF contains extractable text (not scanned images)

3. **"Vector store creation failed"**
   - Verify API keys are valid
   - Check internet connection for OpenAI API access

4. **"No relevant information found"**
   - Try rephrasing your question
   - Ensure the document was processed successfully

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [LangChain](https://langchain.com/) for the LLM framework
- [Streamlit](https://streamlit.io/) for the web UI framework
- [OpenAI](https://openai.com/) for the language models
- [FAISS](https://github.com/facebookresearch/faiss) for vector similarity search
