import os
import logging
import re
from document_processor import get_document_content, get_document_sections
from config import CHUNK_SIZE

logger = logging.getLogger(__name__)

# Global variables
document_chunks = []

def initialize_rag_engine():
    """Initialize the RAG engine with document content."""
    global document_chunks
    
    try:
        document_content = get_document_content()
        if not document_content:
            logger.error("Document content is empty, cannot create document chunks")
            return False
        
        # Combine content into a single text
        full_text = "\n".join(document_content)
        
        # Split text into simple chunks
        chunks = []
        words = full_text.split()
        
        # Create simple chunks based on word count (approximating character count)
        for i in range(0, len(words), CHUNK_SIZE // 5):  # Approximating 5 chars per word
            chunk = " ".join(words[i:i + CHUNK_SIZE // 5])
            chunks.append(chunk)
        
        document_chunks = chunks
        logger.info(f"Split document into {len(chunks)} chunks")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing RAG engine: {e}")
        return False

def search_similar_chunks(query, k=5):
    """Search for chunks similar to the query using simple keyword matching."""
    if not document_chunks:
        logger.error("Document chunks not initialized")
        return []
    
    try:
        # Simple keyword-based search
        keywords = re.findall(r'\b\w+\b', query.lower())
        
        # Score chunks based on keyword matches
        chunk_scores = []
        for chunk in document_chunks:
            chunk_lower = chunk.lower()
            score = 0
            for keyword in keywords:
                if keyword in chunk_lower:
                    score += 1
            
            # Only include chunks with at least one keyword match
            if score > 0:
                chunk_scores.append({"content": chunk, "score": score})
        
        # Sort by score and return top k
        sorted_chunks = sorted(chunk_scores, key=lambda x: x["score"], reverse=True)
        return sorted_chunks[:k]
    except Exception as e:
        logger.error(f"Error searching document chunks: {e}")
        return []

def generate_context_for_query(query):
    """Generate a context for the given query by combining relevant chunks."""
    chunks = search_similar_chunks(query, k=3)
    
    if not chunks:
        # Fallback to section-based search
        try:
            sections = get_document_sections()
            relevant_sections = []
            
            for chapter_name, chapter_data in sections.items():
                # Check if any query word is in chapter name
                if any(word.lower() in chapter_name.lower() for word in query.split()):
                    relevant_sections.append("\n".join(chapter_data["content"]))
                
                # Check section names
                for section_name, section_content in chapter_data["sections"].items():
                    if any(word.lower() in section_name.lower() for word in query.split()):
                        relevant_sections.append("\n".join(section_content))
            
            if relevant_sections:
                return "\n\n".join(relevant_sections[:3])  # Limit to first 3 sections
        except Exception as e:
            logger.error(f"Error in fallback section search: {e}")
        
        return ""
    
    # Combine chunks into a single context
    context = "\n\n".join([chunk["content"] for chunk in chunks])
    return context
