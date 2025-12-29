"""
Summarization and Compression Module: Automatic text compression and fact extraction.
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import re


class BaseSummarizer(ABC):
    """Abstract base class for summarization strategies."""
    
    @abstractmethod
    def summarize(self, text: str, max_length: int, min_length: int = 50) -> str:
        """Generate summary of text."""
        pass
    
    @abstractmethod
    def batch_summarize(self, texts: List[str], max_length: int) -> List[str]:
        """Summarize multiple texts."""
        pass


class ExtractiveSummarizer(BaseSummarizer):
    """
    Extractive summarization: Select most important sentences.
    
    Fast, preserves original wording, good for factual content.
    """
    
    def __init__(self):
        self.sentence_delimiters = r'[.!?]\s+'
    
    def summarize(self, text: str, max_length: int, min_length: int = 50) -> str:
        """Generate extractive summary."""
        if len(text) <= max_length:
            return text
        
        # Split into sentences
        sentences = re.split(self.sentence_delimiters, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return text[:max_length]
        
        # Score sentences
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = self._score_sentence(sentence, i, len(sentences))
            scored_sentences.append((sentence, score))
        
        # Sort by score
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Select sentences until max_length
        selected = []
        current_length = 0
        
        for sentence, score in scored_sentences:
            sentence_len = len(sentence)
            if current_length + sentence_len <= max_length:
                selected.append(sentence)
                current_length += sentence_len
            elif current_length < min_length:
                # Must include at least one sentence
                selected.append(sentence[:max_length - current_length])
                break
        
        # Reorder by original position
        selected_set = set(selected)
        ordered = [s for s in sentences if s in selected_set]
        
        return ' '.join(ordered)
    
    def _score_sentence(self, sentence: str, position: int, total: int) -> float:
        """Score sentence importance."""
        score = 0.0
        
        # Length preference (not too short, not too long)
        length = len(sentence.split())
        if 5 <= length <= 30:
            score += 0.3
        
        # Position preference (first and last sentences often important)
        if position == 0:
            score += 0.4
        elif position == total - 1:
            score += 0.2
        
        # Keyword presence
        important_words = ['important', 'critical', 'must', 'always', 'never', 
                          'key', 'essential', 'required', 'should', 'note']
        if any(word in sentence.lower() for word in important_words):
            score += 0.3
        
        # Numbers and specifics
        if any(char.isdigit() for char in sentence):
            score += 0.2
        
        return score
    
    def batch_summarize(self, texts: List[str], max_length: int) -> List[str]:
        """Summarize multiple texts."""
        return [self.summarize(text, max_length) for text in texts]


class AbstractiveSummarizer(BaseSummarizer):
    """
    Abstractive summarization: Generate new text (requires LLM).
    
    More flexible, can rephrase, but slower and requires API calls.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
    
    def summarize(self, text: str, max_length: int, min_length: int = 50) -> str:
        """Generate abstractive summary using LLM."""
        if len(text) <= max_length:
            return text
        
        if not self.llm_client:
            # Fallback to extractive
            fallback = ExtractiveSummarizer()
            return fallback.summarize(text, max_length, min_length)
        
        # Use LLM to generate summary
        prompt = f"""Summarize the following text in approximately {max_length} characters.
Preserve key facts and important details.

Text:
{text}

Summary:"""
        
        try:
            # This would call the actual LLM
            # For now, fallback to extractive
            fallback = ExtractiveSummarizer()
            return fallback.summarize(text, max_length, min_length)
        except Exception as e:
            print(f"Abstractive summarization failed: {e}")
            fallback = ExtractiveSummarizer()
            return fallback.summarize(text, max_length, min_length)
    
    def batch_summarize(self, texts: List[str], max_length: int) -> List[str]:
        """Summarize multiple texts."""
        # Could batch the LLM calls for efficiency
        return [self.summarize(text, max_length) for text in texts]


class HybridSummarizer(BaseSummarizer):
    """
    Hybrid summarization: Combines extractive and abstractive approaches.
    
    Uses extractive first for speed, then abstractive for quality.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.extractive = ExtractiveSummarizer()
        self.abstractive = AbstractiveSummarizer(llm_client)
    
    def summarize(self, text: str, max_length: int, min_length: int = 50) -> str:
        """Generate hybrid summary."""
        if len(text) <= max_length:
            return text
        
        # First pass: extractive (fast)
        intermediate_length = int(max_length * 1.5)
        extracted = self.extractive.summarize(text, intermediate_length, min_length)
        
        # Second pass: abstractive (quality)
        if len(extracted) > max_length:
            return self.abstractive.summarize(extracted, max_length, min_length)
        
        return extracted
    
    def batch_summarize(self, texts: List[str], max_length: int) -> List[str]:
        """Summarize multiple texts."""
        return [self.summarize(text, max_length) for text in texts]


class FactExtractor:
    """
    Extract structured facts from text.
    
    Identifies entities, relationships, and key information.
    """
    
    def __init__(self):
        # Simple patterns for fact extraction
        self.entity_patterns = [
            r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\b',  # Proper nouns
        ]
        
        self.relation_patterns = [
            r'(.+?) is (.+)',
            r'(.+?) has (.+)',
            r'(.+?) can (.+)',
            r'(.+?) should (.+)',
            r'(.+?) must (.+)',
        ]
    
    def extract_facts(self, text: str) -> List[Dict[str, Any]]:
        """Extract facts from text."""
        facts = []
        
        # Extract entities
        entities = self._extract_entities(text)
        
        # Extract relationships
        relations = self._extract_relations(text)
        
        # Extract key statements
        statements = self._extract_statements(text)
        
        # Combine into fact structures
        for entity in entities:
            facts.append({
                "type": "entity",
                "content": entity,
                "confidence": 0.7,
            })
        
        for relation in relations:
            facts.append({
                "type": "relation",
                "subject": relation[0],
                "predicate": relation[1],
                "object": relation[2],
                "confidence": 0.8,
            })
        
        for statement in statements:
            facts.append({
                "type": "statement",
                "content": statement,
                "confidence": 0.6,
            })
        
        return facts
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities."""
        entities = set()
        
        for pattern in self.entity_patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)
        
        return list(entities)
    
    def _extract_relations(self, text: str) -> List[tuple]:
        """Extract relationships between entities."""
        relations = []
        
        for pattern in self.relation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    subject = match[0].strip()
                    predicate_object = match[1].strip()
                    relations.append((subject, "is/has/can", predicate_object))
        
        return relations
    
    def _extract_statements(self, text: str) -> List[str]:
        """Extract key statements."""
        # Split into sentences
        sentences = re.split(r'[.!?]\s+', text)
        statements = []
        
        keywords = ['important', 'critical', 'must', 'should', 'always', 
                   'never', 'key', 'note', 'required', 'essential']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                statements.append(sentence.strip())
        
        return statements


class CompressionEngine:
    """
    Main compression engine that orchestrates summarization and fact extraction.
    """
    
    def __init__(self, strategy: str = "extractive", llm_client: Optional[Any] = None):
        self.strategy = strategy
        
        # Initialize summarizer
        if strategy == "extractive":
            self.summarizer = ExtractiveSummarizer()
        elif strategy == "abstractive":
            self.summarizer = AbstractiveSummarizer(llm_client)
        elif strategy == "hybrid":
            self.summarizer = HybridSummarizer(llm_client)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Initialize fact extractor
        self.fact_extractor = FactExtractor()
    
    def compress(self, text: str, target_length: int, 
                extract_facts: bool = False) -> Dict[str, Any]:
        """
        Compress text to target length.
        
        Returns:
            Dictionary with compressed text and optional facts
        """
        result = {
            "original_length": len(text),
            "target_length": target_length,
            "compressed": "",
            "compression_ratio": 0.0,
            "facts": [],
        }
        
        # Summarize
        summary = self.summarizer.summarize(text, target_length)
        result["compressed"] = summary
        result["actual_length"] = len(summary)
        result["compression_ratio"] = len(summary) / len(text) if len(text) > 0 else 1.0
        
        # Extract facts if requested
        if extract_facts:
            result["facts"] = self.fact_extractor.extract_facts(text)
        
        return result
    
    def batch_compress(self, texts: List[str], target_length: int) -> List[Dict[str, Any]]:
        """Compress multiple texts."""
        return [self.compress(text, target_length) for text in texts]
    
    def multi_level_summarize(self, texts: List[str], 
                             levels: List[int]) -> Dict[str, Any]:
        """
        Create multi-level summaries (turn -> phase -> session).
        
        Args:
            texts: List of texts to summarize
            levels: List of target lengths for each level
        
        Returns:
            Dictionary with summaries at each level
        """
        if not texts:
            return {"levels": []}
        
        result = {
            "original_count": len(texts),
            "levels": [],
        }
        
        # Combine all texts
        combined = " ".join(texts)
        
        # Generate summaries at each level
        for level_idx, target_length in enumerate(levels):
            summary = self.summarizer.summarize(combined, target_length)
            result["levels"].append({
                "level": level_idx + 1,
                "target_length": target_length,
                "summary": summary,
                "actual_length": len(summary),
            })
            
            # Use this summary as input for next level
            combined = summary
        
        return result
    
    def adaptive_compress(self, text: str, token_budget: int,
                         chars_per_token: float = 4.0) -> str:
        """
        Adaptively compress text to fit token budget.
        
        Args:
            text: Text to compress
            token_budget: Target token count
            chars_per_token: Character to token ratio (default 4.0)
        """
        target_chars = int(token_budget * chars_per_token)
        
        if len(text) <= target_chars:
            return text
        
        return self.summarizer.summarize(text, target_chars)
