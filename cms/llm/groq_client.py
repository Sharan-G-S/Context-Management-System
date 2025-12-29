"""
Groq API client for LLM operations.
Supports chat completion, embeddings, and text generation.
"""

import os
from typing import List, Dict, Optional, Any
import requests
import json


class GroqClient:
    """Client for Groq API operations."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Groq client.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("Groq API key not provided. Set GROQ_API_KEY environment variable.")
        
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (llama-3.3-70b-versatile, mixtral-8x7b-32768, etc.)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Enable streaming responses
            
        Returns:
            Response dict with 'choices' containing generated text
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def generate_text(
        self,
        prompt: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """Generate text completion from prompt.
        
        Args:
            prompt: Input prompt
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text string
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response['choices'][0]['message']['content']
    
    def summarize_text(
        self,
        text: str,
        max_length: int = 150,
        model: str = "llama-3.3-70b-versatile"
    ) -> str:
        """Summarize text using LLM.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            model: Model name
            
        Returns:
            Summary string
        """
        prompt = f"""Summarize the following text concisely in under {max_length} words:

{text}

Summary:"""
        
        return self.generate_text(prompt, model=model, max_tokens=max_length * 2)
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted entities
        """
        prompt = f"""Extract all named entities (people, organizations, locations, concepts) from this text.
Return only a JSON list of entities.

Text: {text}

Entities:"""
        
        response = self.generate_text(prompt, temperature=0.3, max_tokens=500)
        
        try:
            # Try to parse JSON response
            if '[' in response and ']' in response:
                start = response.index('[')
                end = response.rindex(']') + 1
                entities = json.loads(response[start:end])
                return entities
        except:
            pass
        
        # Fallback: split by newlines or commas
        entities = [e.strip() for e in response.replace('\n', ',').split(',')]
        return [e for e in entities if e and len(e) > 1]
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding (placeholder - uses simple hash).
        
        Note: Groq doesn't provide dedicated embedding API yet.
        This generates a simple deterministic vector for demonstration.
        For production, use sentence-transformers or OpenAI embeddings.
        
        Args:
            text: Input text
            
        Returns:
            384-dimensional embedding vector
        """
        # Simple deterministic embedding based on text characteristics
        import hashlib
        import numpy as np
        
        # Create hash-based seed
        hash_obj = hashlib.sha256(text.encode())
        seed = int(hash_obj.hexdigest(), 16) % (2**32)
        
        # Generate deterministic vector
        np.random.seed(seed)
        embedding = np.random.randn(384).astype(float)
        
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    def answer_question(
        self,
        question: str,
        context: str,
        model: str = "llama-3.3-70b-versatile"
    ) -> str:
        """Answer question based on provided context (RAG).
        
        Args:
            question: User question
            context: Retrieved context documents
            model: Model name
            
        Returns:
            Answer string
        """
        prompt = f"""Based on the following context, answer the question accurately and concisely.

Context:
{context}

Question: {question}

Answer:"""
        
        return self.generate_text(prompt, model=model, max_tokens=512)
    
    def classify_text(
        self,
        text: str,
        categories: List[str]
    ) -> str:
        """Classify text into one of the provided categories.
        
        Args:
            text: Text to classify
            categories: List of category names
            
        Returns:
            Selected category
        """
        categories_str = ", ".join(categories)
        
        prompt = f"""Classify the following text into exactly one of these categories: {categories_str}

Text: {text}

Category:"""
        
        response = self.generate_text(prompt, temperature=0.2, max_tokens=50)
        
        # Extract category from response
        for category in categories:
            if category.lower() in response.lower():
                return category
        
        return categories[0]  # Default to first category
