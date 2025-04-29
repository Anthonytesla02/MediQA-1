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
    """Search for chunks similar to the query using enhanced keyword matching."""
    if not document_chunks:
        logger.error("Document chunks not initialized")
        return []
    
    try:
        # Preprocess query to extract important terms
        query_lower = query.lower()
        
        # Check for common patterns in medical queries
        treatment_phrases = ['treatment for', 'treatment of', 'how to treat', 'medicine for', 'drug for', 'therapy for', 'exact treatment']
        diagnosis_phrases = ['diagnosis of', 'symptoms of', 'signs of', 'diagnosing', 'diagnostic criteria', 'what is', 'what diagnosis']
        
        is_treatment_query = any(phrase in query_lower for phrase in treatment_phrases)
        is_diagnosis_query = any(phrase in query_lower for phrase in diagnosis_phrases)
        
        # Extract keywords - give more importance to multi-word phrases
        keywords = re.findall(r'\b\w+\b', query_lower)
        phrases = re.findall(r'\b\w+(?:\s+\w+){1,3}\b', query_lower)  # Match 2-4 word phrases
        
        # Score chunks based on keyword and phrase matches with enhanced weighting
        chunk_scores = []
        for chunk in document_chunks:
            chunk_lower = chunk.lower()
            score = 0
            
            # Score individual keywords
            for keyword in keywords:
                if keyword in chunk_lower:
                    # Skip common words that add noise
                    if len(keyword) <= 3 or keyword in ['and', 'the', 'for', 'with', 'what', 'this', 'that']:
                        continue
                    
                    # Higher score for exact matches (with word boundaries)
                    if re.search(r'\b' + re.escape(keyword) + r'\b', chunk_lower):
                        score += 2
                    else:
                        score += 1
            
            # Score multi-word phrases - these get higher weights
            for phrase in phrases:
                if phrase in chunk_lower:
                    # Higher score for longer phrases and key medical terms
                    phrase_len = len(phrase.split())
                    score += 3 * phrase_len
            
            # Boost score for chunks containing treatment info in treatment queries
            if is_treatment_query and any(word in chunk_lower for word in ['treatment', 'therapy', 'drug', 'medication', 'dose', 'regimen', 'management']):
                score *= 1.5
            
            # Boost score for chunks containing diagnosis info in diagnosis queries
            if is_diagnosis_query and any(word in chunk_lower for word in ['symptom', 'diagnosis', 'sign', 'diagnostic', 'indication', 'criterion', 'criteria']):
                score *= 1.5
            
            # Only include chunks with meaningful score
            if score > 2:  # Threshold to filter out weak matches
                chunk_scores.append({"content": chunk, "score": score})
        
        # Sort by score and return top k
        sorted_chunks = sorted(chunk_scores, key=lambda x: x["score"], reverse=True)
        return sorted_chunks[:k]
    except Exception as e:
        logger.error(f"Error searching document chunks: {e}")
        return []

def generate_context_for_query(query):
    """Generate a context for the given query by combining relevant chunks and structure the information."""
    # Increase result count to get more potentially relevant chunks
    chunks = search_similar_chunks(query, k=5)
    
    # Extract key medical terms that might be mentioned in document headers
    medical_terms = re.findall(r'\b[A-Z][a-z]{3,}(?:\s+[A-Z][a-z]{3,}){0,3}\b', query)
    disease_mentions = [term for term in medical_terms if len(term) > 5]  # Likely disease names are longer
    
    if not chunks or len(''.join([chunk["content"] for chunk in chunks])) < 200:  # If content is too short
        # Enhanced fallback to section-based search 
        try:
            sections = get_document_sections()
            relevant_sections = []
            
            # Check for disease/treatment terms in chapter and section names
            for chapter_name, chapter_data in sections.items():
                # More sophisticated chapter name matching
                chapter_match_score = 0
                
                # Check for whole query matches
                if query.lower() in chapter_name.lower():
                    chapter_match_score += 10
                
                # Check for disease name matches in chapter titles
                for term in disease_mentions:
                    if term.lower() in chapter_name.lower():
                        chapter_match_score += 5
                
                # Check for individual word matches
                for word in query.lower().split():
                    if len(word) > 3 and word in chapter_name.lower():
                        chapter_match_score += 1
                
                if chapter_match_score > 0:
                    relevant_sections.append(("\n".join(chapter_data["content"]), chapter_match_score))
                
                # Search section names similarly
                for section_name, section_content in chapter_data["sections"].items():
                    section_match_score = 0
                    
                    if query.lower() in section_name.lower():
                        section_match_score += 10
                    
                    for term in disease_mentions:
                        if term.lower() in section_name.lower():
                            section_match_score += 5
                    
                    for word in query.lower().split():
                        if len(word) > 3 and word in section_name.lower():
                            section_match_score += 1
                    
                    if section_match_score > 0:
                        relevant_sections.append(("\n".join(section_content), section_match_score))
            
            if relevant_sections:
                # Sort by relevance score
                relevant_sections.sort(key=lambda x: x[1], reverse=True)
                # Take top 3 most relevant sections
                top_sections = [section[0] for section in relevant_sections[:3]]
                return "\n\n".join(top_sections)
        except Exception as e:
            logger.error(f"Error in fallback section search: {e}")
        
        return "The guidelines do not appear to contain specific information about this query."
    
    # Structure the context with any section/chapter headings when available
    structured_context = []
    
    for chunk in chunks:
        content = chunk["content"]
        # Try to identify if this chunk has a heading/title line
        lines = content.split('\n')
        
        if len(lines) > 1 and len(lines[0]) < 100 and any(char.isupper() for char in lines[0]):
            # Likely a heading - format it more prominently
            heading = lines[0].strip()
            content_body = '\n'.join(lines[1:]).strip()
            
            structured_chunk = f"## {heading} ##\n{content_body}"
            structured_context.append(structured_chunk)
        else:
            structured_context.append(content)
    
    # Combine chunks into a well-structured context
    context = "\n\n".join(structured_context)
    return context
