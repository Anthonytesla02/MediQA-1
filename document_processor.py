import os
import logging
import docx
from config import DOCUMENT_PATH

logger = logging.getLogger(__name__)

# Global variables to store document content
document_content = []
document_sections = {}

def extract_text_from_docx(docx_path):
    """Extract text from a .docx file."""
    try:
        doc = docx.Document(docx_path)
        text = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text.strip())
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from document: {e}")
        return []

def parse_document_structure(content):
    """Parse the document to identify chapters and sections."""
    sections = {}
    current_chapter = None
    current_section = None
    
    for line in content:
        # Check for chapter headings
        if line.startswith("Chapter "):
            parts = line.split(".")
            if len(parts) >= 2:
                current_chapter = parts[1].strip()
                current_section = None
                sections[current_chapter] = {"sections": {}, "content": []}
        # Check for section headings (non-chapter lines that aren't too long)
        elif current_chapter and len(line) < 100 and not line.startswith("Table of Contents") and not line.isdigit():
            current_section = line
            if current_section not in sections[current_chapter]["sections"]:
                sections[current_chapter]["sections"][current_section] = []
        # Add content to current section or chapter
        elif current_chapter:
            if current_section:
                sections[current_chapter]["sections"][current_section].append(line)
            else:
                sections[current_chapter]["content"].append(line)
    
    return sections

def initialize_document_processor():
    """Initialize the document processor by loading and parsing the document."""
    global document_content, document_sections
    
    if not os.path.exists(DOCUMENT_PATH):
        logger.error(f"Document not found at {DOCUMENT_PATH}")
        return False
    
    logger.info(f"Loading document from {DOCUMENT_PATH}")
    document_content = extract_text_from_docx(DOCUMENT_PATH)
    
    if not document_content:
        logger.error("Failed to extract content from document")
        return False
    
    logger.info(f"Successfully loaded document with {len(document_content)} lines")
    
    # Parse document structure
    document_sections = parse_document_structure(document_content)
    logger.info(f"Parsed document into {len(document_sections)} chapters")
    
    return True

def get_document_content():
    """Get the full document content."""
    return document_content

def get_document_sections():
    """Get the parsed document sections."""
    return document_sections

def get_section_content(chapter, section=None):
    """Get content for a specific chapter and section."""
    if chapter in document_sections:
        if section and section in document_sections[chapter]["sections"]:
            return document_sections[chapter]["sections"][section]
        else:
            return document_sections[chapter]["content"]
    return []

def search_document(query, max_results=5):
    """Simple search function to find relevant sections for a query."""
    results = []
    
    # Convert query to lowercase for case-insensitive search
    query_lower = query.lower()
    
    # Search through chapters and sections
    for chapter_name, chapter_data in document_sections.items():
        # Search in chapter content
        chapter_text = " ".join(chapter_data["content"])
        if query_lower in chapter_text.lower():
            results.append({
                "chapter": chapter_name,
                "section": None,
                "relevance": chapter_text.lower().count(query_lower)
            })
        
        # Search in sections
        for section_name, section_content in chapter_data["sections"].items():
            section_text = " ".join(section_content)
            if query_lower in section_text.lower():
                results.append({
                    "chapter": chapter_name,
                    "section": section_name,
                    "relevance": section_text.lower().count(query_lower)
                })
    
    # Sort by relevance and limit results
    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:max_results]
