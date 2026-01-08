"""
Advanced Paper Analyzer for Research Documents.

This module provides specialized analysis for academic papers including:
- Section extraction (Abstract, Introduction, Methods, etc.)
- Technical term/glossary detection
- Figure, table, and equation extraction
- Citation analysis
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from collections import Counter
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from src.config import Config, default_config

logger = logging.getLogger(__name__)


def clean_pdf_text(text: str) -> str:
    """
    Clean garbled text commonly found in PDF extractions.
    Fixes issues like ligatures, reversed characters, and encoding problems.
    """
    if not text:
        return ""

    # Remove common garbled patterns (reversed text markers, control chars)
    # Pattern like >FOO< or similar reversed bracket patterns
    text = re.sub(r'>[A-Za-z]+<', '', text)

    # Remove control characters and non-printable characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    # Fix common ligature issues
    ligatures = {
        'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 'ﬃ': 'ffi', 'ﬄ': 'ffl',
        'ﬅ': 'st', 'ﬆ': 'st', '—': '-', '–': '-', '"': '"', '"': '"',
        ''': "'", ''': "'", '…': '...', '•': '-',
    }
    for lig, replacement in ligatures.items():
        text = text.replace(lig, replacement)

    # Remove excessive whitespace but preserve sentence structure
    text = re.sub(r'\s+', ' ', text)

    # Remove isolated special characters
    text = re.sub(r'\s[<>]\s', ' ', text)

    # Clean up any remaining angle brackets not part of valid content
    text = re.sub(r'<[^>]{0,3}>', '', text)

    return text.strip()


# Common academic section patterns
SECTION_PATTERNS = [
    (r'abstract', 'Abstract'),
    (r'introduction', 'Introduction'),
    (r'related\s*work', 'Related Work'),
    (r'background', 'Background'),
    (r'literature\s*review', 'Literature Review'),
    (r'method(?:ology|s)?', 'Methodology'),
    (r'approach', 'Approach'),
    (r'experiment(?:s|al)?(?:\s*setup)?', 'Experiments'),
    (r'result(?:s)?', 'Results'),
    (r'evaluation', 'Evaluation'),
    (r'discussion', 'Discussion'),
    (r'analysis', 'Analysis'),
    (r'conclusion(?:s)?', 'Conclusion'),
    (r'future\s*work', 'Future Work'),
    (r'acknowledge?ment(?:s)?', 'Acknowledgments'),
    (r'reference(?:s)?', 'References'),
    (r'appendix', 'Appendix'),
]

# Technical terms that commonly need explanation
COMMON_TECHNICAL_TERMS = {
    'transformer', 'attention', 'embedding', 'encoder', 'decoder',
    'neural network', 'deep learning', 'machine learning', 'nlp',
    'bert', 'gpt', 'lstm', 'rnn', 'cnn', 'gan', 'vae',
    'gradient descent', 'backpropagation', 'optimization', 'loss function',
    'softmax', 'relu', 'sigmoid', 'activation function',
    'fine-tuning', 'pre-training', 'transfer learning',
    'tokenization', 'vocabulary', 'corpus',
    'precision', 'recall', 'f1 score', 'accuracy', 'bleu',
    'hyperparameter', 'epoch', 'batch size', 'learning rate',
    'overfitting', 'underfitting', 'regularization', 'dropout',
    'convolution', 'pooling', 'kernel', 'stride',
    'self-attention', 'multi-head attention', 'positional encoding',
    'layer normalization', 'batch normalization',
    'cross-entropy', 'kl divergence', 'mse', 'mae',
    'adam', 'sgd', 'momentum', 'scheduler',
    'inference', 'training', 'validation', 'test set',
    'benchmark', 'baseline', 'state-of-the-art', 'sota',
    'ablation study', 'case study', 'empirical',
    'latent', 'representation', 'feature', 'dimension',
    'semantic', 'syntactic', 'contextual',
    'supervised', 'unsupervised', 'semi-supervised', 'reinforcement',
    'classification', 'regression', 'clustering', 'segmentation',
    'retrieval', 'generation', 'summarization', 'translation',
}


@dataclass
class Section:
    """Represents a document section."""
    id: str
    title: str
    content: str
    page: int
    start_pos: int
    end_pos: int
    progress: int = 0


@dataclass
class Term:
    """Represents a technical term."""
    term: str
    definition: str
    frequency: int
    context: str


@dataclass
class Figure:
    """Represents a figure, table, or equation."""
    id: int
    type: str  # 'figure', 'table', 'equation'
    title: str
    caption: str
    page: int
    content: str


@dataclass
class Citation:
    """Represents a citation/reference."""
    id: int
    authors: str
    year: str
    title: str
    cited_count: int


class PaperAnalyzer:
    """
    Advanced analyzer for academic/research papers.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or default_config
        self._llm = None

    def _get_llm(self):
        """Get or create LLM instance."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.config.llm_model_name,
                temperature=0.3
            )
        return self._llm

    def extract_sections(self, text: str) -> List[Section]:
        """
        Extract document sections from academic paper.

        Args:
            text: The document text.

        Returns:
            List of Section objects.
        """
        sections = []
        text_lower = text.lower()

        # Find all section headers
        section_matches = []
        for pattern, title in SECTION_PATTERNS:
            # Look for numbered sections like "1. Introduction" or "I. Introduction"
            regex = rf'(?:^|\n)\s*(?:[\dIVXivx]+\.?\s*)?({pattern})\s*(?:\n|$)'
            for match in re.finditer(regex, text_lower, re.IGNORECASE):
                section_matches.append({
                    'title': title,
                    'start': match.start(),
                    'matched': match.group(1)
                })

        # Sort by position
        section_matches.sort(key=lambda x: x['start'])

        # Extract section content
        for i, section in enumerate(section_matches):
            start = section['start']
            end = section_matches[i + 1]['start'] if i + 1 < len(section_matches) else len(text)

            content = text[start:end].strip()
            # Estimate page (rough approximation: ~3000 chars per page)
            page = max(1, start // 3000 + 1)

            sections.append(Section(
                id=section['title'].lower().replace(' ', '_'),
                title=section['title'],
                content=content[:2000],  # Limit content size
                page=page,
                start_pos=start,
                end_pos=end,
                progress=0
            ))

        # If no sections found, create a default structure
        if not sections:
            sections = [
                Section(
                    id='document',
                    title='Full Document',
                    content=text[:2000],
                    page=1,
                    start_pos=0,
                    end_pos=len(text),
                    progress=0
                )
            ]

        return sections

    def extract_technical_terms(self, text: str, top_n: int = 20) -> List[Term]:
        """
        Extract and identify technical terms that may need explanation.

        Args:
            text: The document text.
            top_n: Maximum number of terms to return.

        Returns:
            List of Term objects.
        """
        # Clean the text first to remove garbled characters
        cleaned_text = clean_pdf_text(text)
        text_lower = cleaned_text.lower()
        terms = []

        # Count occurrences of known technical terms
        term_counts = {}
        for term in COMMON_TECHNICAL_TERMS:
            count = len(re.findall(rf'\b{re.escape(term)}\b', text_lower))
            if count > 0:
                term_counts[term] = count

        # Also look for capitalized acronyms and technical-looking terms
        acronyms = re.findall(r'\b([A-Z]{2,6})\b', cleaned_text)
        acronym_counts = Counter(acronyms)

        # Combine and sort by frequency
        all_terms = list(term_counts.items())
        for acronym, count in acronym_counts.most_common(10):
            if acronym not in ['THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'EACH']:
                all_terms.append((acronym, count))

        all_terms.sort(key=lambda x: x[1], reverse=True)

        # Create Term objects
        for term, count in all_terms[:top_n]:
            # Find a context sentence - use a more robust pattern
            # Look for sentences containing the term
            sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
            context = ""
            for sentence in sentences:
                if re.search(rf'\b{re.escape(term)}\b', sentence, re.IGNORECASE):
                    # Clean and validate the sentence
                    clean_sentence = clean_pdf_text(sentence)
                    # Only use if it looks like a valid sentence
                    if len(clean_sentence) > 20 and clean_sentence[0].isupper():
                        context = clean_sentence
                        break

            # Truncate and ensure clean output
            if context:
                context = context[:200]
                # Make sure context doesn't end mid-word
                if len(context) == 200:
                    last_space = context.rfind(' ')
                    if last_space > 150:
                        context = context[:last_space] + "..."

            terms.append(Term(
                term=term.title() if term.islower() else term,
                definition="",  # Will be filled by AI if needed
                frequency=count,
                context=context if context else "Term found in document"
            ))

        return terms

    def extract_figures_tables_equations(self, text: str) -> List[Figure]:
        """
        Extract figures, tables, and equations from the document.

        Args:
            text: The document text.

        Returns:
            List of Figure objects.
        """
        items = []
        item_id = 1

        # Find figures
        fig_patterns = [
            r'(?:Figure|Fig\.?)\s*(\d+)[:\.]?\s*([^\n]+)',
            r'(?:Figure|Fig\.?)\s*(\d+)',
        ]
        for pattern in fig_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                num = match.group(1)
                caption = match.group(2).strip() if len(match.groups()) > 1 else f"Figure {num}"
                page = max(1, match.start() // 3000 + 1)

                items.append(Figure(
                    id=item_id,
                    type='figure',
                    title=f"Figure {num}",
                    caption=caption[:100],
                    page=page,
                    content=match.group(0)
                ))
                item_id += 1

        # Find tables
        table_patterns = [
            r'(?:Table)\s*(\d+)[:\.]?\s*([^\n]+)',
            r'(?:Table)\s*(\d+)',
        ]
        for pattern in table_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                num = match.group(1)
                caption = match.group(2).strip() if len(match.groups()) > 1 else f"Table {num}"
                page = max(1, match.start() // 3000 + 1)

                items.append(Figure(
                    id=item_id,
                    type='table',
                    title=f"Table {num}",
                    caption=caption[:100],
                    page=page,
                    content=match.group(0)
                ))
                item_id += 1

        # Find equations
        eq_patterns = [
            r'(?:Equation|Eq\.?)\s*[(\[]?(\d+)[)\]]?',
            r'\$\$([^$]+)\$\$',  # LaTeX display math
            r'\\\[([^\]]+)\\\]',  # LaTeX equation
        ]
        for pattern in eq_patterns:
            for match in re.finditer(pattern, text):
                page = max(1, match.start() // 3000 + 1)
                content = match.group(1) if match.groups() else match.group(0)

                items.append(Figure(
                    id=item_id,
                    type='equation',
                    title=f"Equation {item_id}",
                    caption="Mathematical expression",
                    page=page,
                    content=content[:200]
                ))
                item_id += 1

        return items[:20]  # Limit to 20 items

    def extract_citations(self, text: str) -> List[Citation]:
        """
        Extract citations and references from the document.

        Args:
            text: The document text.

        Returns:
            List of Citation objects.
        """
        citations = []

        # Pattern for common citation formats
        # [Author et al., 2020] or (Author et al., 2020) or Author et al. (2020)
        patterns = [
            r'\[([A-Z][a-z]+(?:\s+et\s+al\.?)?),?\s*(\d{4})\]',
            r'\(([A-Z][a-z]+(?:\s+et\s+al\.?)?),?\s*(\d{4})\)',
            r'([A-Z][a-z]+(?:\s+et\s+al\.?))\s*\((\d{4})\)',
        ]

        citation_counts = {}
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                author = match.group(1)
                year = match.group(2)
                key = f"{author}_{year}"

                if key not in citation_counts:
                    citation_counts[key] = {
                        'authors': author,
                        'year': year,
                        'count': 0
                    }
                citation_counts[key]['count'] += 1

        # Sort by citation count
        sorted_citations = sorted(
            citation_counts.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )

        for i, (key, data) in enumerate(sorted_citations[:15]):
            citations.append(Citation(
                id=i + 1,
                authors=data['authors'],
                year=data['year'],
                title="",  # Would need reference section parsing
                cited_count=data['count']
            ))

        return citations

    def generate_term_definition(self, term: str, context: str) -> str:
        """
        Generate a definition for a technical term using AI.

        Args:
            term: The term to define.
            context: Context from the document.

        Returns:
            Definition string.
        """
        try:
            llm = self._get_llm()

            prompt = PromptTemplate(
                input_variables=["term", "context"],
                template="""Define the following technical term in 1-2 sentences.
Keep it simple but accurate for someone reading a research paper.

Term: {term}
Context from paper: {context}

Definition:"""
            )

            response = llm.invoke(prompt.format(term=term, context=context[:500]))
            return response.content.strip()

        except Exception as e:
            logger.error(f"Failed to generate definition: {e}")
            return ""

    def explain_equation(self, equation: str, context: str) -> Dict:
        """
        Explain an equation step by step.

        Args:
            equation: The equation text.
            context: Surrounding context.

        Returns:
            Dict with explanation and variable definitions.
        """
        try:
            llm = self._get_llm()

            prompt = PromptTemplate(
                input_variables=["equation", "context"],
                template="""Explain this equation from a research paper.

Equation: {equation}
Context: {context}

Provide:
1. A plain English explanation of what this equation does
2. Definition of each variable/symbol
3. Step-by-step breakdown

Format as:
EXPLANATION: [1-2 sentence explanation]
VARIABLES:
- [variable]: [meaning]
STEPS:
1. [step]
2. [step]
"""
            )

            response = llm.invoke(prompt.format(equation=equation, context=context[:500]))
            content = response.content.strip()

            # Parse response
            result = {
                'explanation': '',
                'variables': [],
                'steps': []
            }

            lines = content.split('\n')
            current_section = None

            for line in lines:
                line = line.strip()
                if line.startswith('EXPLANATION:'):
                    current_section = 'explanation'
                    result['explanation'] = line.replace('EXPLANATION:', '').strip()
                elif line.startswith('VARIABLES:'):
                    current_section = 'variables'
                elif line.startswith('STEPS:'):
                    current_section = 'steps'
                elif line.startswith('- ') and current_section == 'variables':
                    result['variables'].append(line[2:])
                elif re.match(r'^\d+\.', line) and current_section == 'steps':
                    result['steps'].append(re.sub(r'^\d+\.\s*', '', line))

            return result

        except Exception as e:
            logger.error(f"Failed to explain equation: {e}")
            return {
                'explanation': 'Failed to generate explanation.',
                'variables': [],
                'steps': []
            }

    def generate_section_summary(self, section: Section, level: str = 'detailed') -> str:
        """
        Generate a summary of a section at specified detail level.

        Args:
            section: The section to summarize.
            level: 'brief', 'detailed', or 'expert'

        Returns:
            Summary string.
        """
        try:
            llm = self._get_llm()

            level_instructions = {
                'brief': 'Provide a 1-sentence summary suitable for quick skimming.',
                'detailed': 'Provide a 2-3 sentence summary covering the main points.',
                'expert': 'Provide a detailed technical summary with key findings and implications.'
            }

            prompt = PromptTemplate(
                input_variables=["section_title", "content", "instruction"],
                template="""Summarize this section from a research paper.

Section: {section_title}
Content: {content}

{instruction}

Summary:"""
            )

            response = llm.invoke(prompt.format(
                section_title=section.title,
                content=section.content[:3000],
                instruction=level_instructions.get(level, level_instructions['detailed'])
            ))
            return response.content.strip()

        except Exception as e:
            logger.error(f"Failed to generate section summary: {e}")
            return "Summary generation failed."

    def get_prerequisites(self, text: str) -> List[str]:
        """
        Identify prerequisite knowledge needed to understand the paper.

        Args:
            text: The document text.

        Returns:
            List of prerequisite topics.
        """
        try:
            llm = self._get_llm()

            prompt = PromptTemplate(
                input_variables=["text"],
                template="""Based on this research paper excerpt, identify the prerequisite knowledge a reader should have to fully understand it.

Paper excerpt:
{text}

List 5-7 prerequisite topics or concepts (one per line, no numbering):"""
            )

            response = llm.invoke(prompt.format(text=text[:3000]))
            prerequisites = response.content.strip().split('\n')
            prerequisites = [p.strip().lstrip('•-123456789.') .strip() for p in prerequisites if p.strip()]

            return prerequisites[:7]

        except Exception as e:
            logger.error(f"Failed to get prerequisites: {e}")
            return ['Basic understanding of the domain', 'Familiarity with research methodology']

    def get_key_takeaways(self, text: str) -> List[str]:
        """
        Extract key takeaways from the document.

        Args:
            text: The document text.

        Returns:
            List of key takeaways.
        """
        try:
            llm = self._get_llm()

            prompt = PromptTemplate(
                input_variables=["text"],
                template="""Extract the key takeaways from this research paper.

Paper excerpt:
{text}

List 5 key takeaways or main findings (one per line, no numbering):"""
            )

            response = llm.invoke(prompt.format(text=text[:4000]))
            takeaways = response.content.strip().split('\n')
            takeaways = [t.strip().lstrip('•-123456789.') .strip() for t in takeaways if t.strip()]

            return takeaways[:5]

        except Exception as e:
            logger.error(f"Failed to get takeaways: {e}")
            return ['Unable to extract key takeaways.']

    def analyze_paper(self, text: str) -> Dict:
        """
        Perform comprehensive paper analysis.

        Args:
            text: The document text.

        Returns:
            Dict with all analysis results.
        """
        return {
            'sections': self.extract_sections(text),
            'terms': self.extract_technical_terms(text),
            'figures': self.extract_figures_tables_equations(text),
            'citations': self.extract_citations(text),
        }
