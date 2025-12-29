"""
Research Agent for information gathering and analysis.
Uses RAG system to search documents and synthesize information.
"""

from typing import Dict, Any, Optional
from cms.agents.base_agent import BaseAgent
from cms.llm.groq_client import GroqClient
from cms.storage.sqlite import SQLiteStorage
from cms.rag.pipeline import RAGPipeline


class ResearchAgent(BaseAgent):
    """Agent specialized in research and information gathering."""
    
    def __init__(
        self,
        llm_client: GroqClient,
        storage: Optional[SQLiteStorage] = None,
        rag_pipeline: Optional[RAGPipeline] = None
    ):
        """Initialize research agent.
        
        Args:
            llm_client: LLM client
            storage: Optional storage backend
            rag_pipeline: Optional RAG pipeline for document search
        """
        super().__init__(
            name="ResearchAgent",
            llm_client=llm_client,
            storage=storage,
            system_prompt=self._research_system_prompt()
        )
        
        self.rag = rag_pipeline
        
        # Register research-specific tools
        if self.rag:
            self.register_tool("search_documents", self._tool_search_documents)
        self.register_tool("analyze", self._tool_analyze)
        self.register_tool("summarize", self._tool_summarize)
    
    def _research_system_prompt(self) -> str:
        """System prompt for research agent."""
        return """You are ResearchAgent, an AI specialized in information gathering and analysis.

Your capabilities:
- Search through documents to find relevant information
- Analyze and synthesize information from multiple sources
- Summarize findings concisely
- Think critically and identify knowledge gaps

Approach each research task systematically:
1. Understand the research question
2. Search for relevant information
3. Analyze and synthesize findings
4. Provide clear, well-supported conclusions
"""
    
    def _tool_search_documents(self, query: str) -> str:
        """Search documents using RAG system."""
        if not self.rag:
            return "RAG system not available"
        
        results = self.rag.retrieve(query, top_k=3)
        
        if not results:
            return f"No documents found for query: {query}"
        
        # Format results
        output = f"Found {len(results)} relevant documents for '{query}':\n\n"
        for i, doc in enumerate(results, 1):
            output += f"[{i}] (similarity: {doc.get('similarity', 0):.3f})\n"
            output += f"{doc['content'][:200]}...\n\n"
        
        return output
    
    def _tool_analyze(self, information: str) -> str:
        """Analyze information and extract insights."""
        prompt = f"""Analyze the following information and extract key insights:

{information}

Provide:
1. Main findings
2. Key patterns or trends
3. Potential implications

Analysis:"""
        
        analysis = self.llm.generate_text(prompt, max_tokens=512)
        return analysis
    
    def _tool_summarize(self, content: str) -> str:
        """Summarize content concisely."""
        summary = self.llm.summarize_text(content, max_length=100)
        return summary
    
    def research(self, question: str) -> Dict[str, Any]:
        """Conduct research on a question.
        
        Args:
            question: Research question
            
        Returns:
            Dict with research findings and analysis
        """
        # Use RAG if available
        if self.rag:
            rag_result = self.rag.answer_question(question, top_k=5)
            
            # Analyze findings
            analysis = self._tool_analyze(rag_result['context'])
            
            return {
                'question': question,
                'answer': rag_result['answer'],
                'analysis': analysis,
                'sources': rag_result['sources'],
                'method': 'RAG + Analysis'
            }
        else:
            # Fallback to agent reasoning
            result = self.run(f"Research this question: {question}")
            
            return {
                'question': question,
                'answer': result['result'],
                'analysis': "Agent-based research without document retrieval",
                'sources': [],
                'method': 'Agent Reasoning',
                'iterations': result['iterations']
            }
    
    def multi_query_research(self, queries: list) -> Dict[str, Any]:
        """Research multiple related queries.
        
        Args:
            queries: List of research questions
            
        Returns:
            Dict with combined findings
        """
        results = []
        
        for query in queries:
            result = self.research(query)
            results.append(result)
        
        # Synthesize findings
        all_answers = "\n\n".join([
            f"Q: {r['question']}\nA: {r['answer']}"
            for r in results
        ])
        
        synthesis_prompt = f"""Synthesize the following research findings into a coherent summary:

{all_answers}

Synthesis:"""
        
        synthesis = self.llm.generate_text(synthesis_prompt, max_tokens=1024)
        
        return {
            'queries': queries,
            'individual_results': results,
            'synthesis': synthesis,
            'total_sources': sum(len(r['sources']) for r in results)
        }
