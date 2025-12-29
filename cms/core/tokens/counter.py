"""
Token Accounting Module: Model-specific token counting and budget enforcement.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import tiktoken


class TokenCounter(ABC):
    """Abstract base class for token counters."""
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass
    
    @abstractmethod
    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in message list."""
        pass


class TiktokenCounter(TokenCounter):
    """Token counter using tiktoken library (for OpenAI models)."""
    
    MODELS_TO_ENCODING = {
        "gpt-4": "cl100k_base",
        "gpt-4-32k": "cl100k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-4-turbo-preview": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "gpt-3.5-turbo-16k": "cl100k_base",
        "text-embedding-ada-002": "cl100k_base",
        "text-davinci-003": "p50k_base",
        "text-davinci-002": "p50k_base",
    }
    
    # Token overhead for message formatting
    TOKENS_PER_MESSAGE = 3
    TOKENS_PER_NAME = 1
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.encoding_name = self.MODELS_TO_ENCODING.get(model, "cl100k_base")
        
        try:
            self.encoding = tiktoken.get_encoding(self.encoding_name)
        except Exception as e:
            # Fallback to cl100k_base
            print(f"Warning: Could not load encoding {self.encoding_name}, using cl100k_base: {e}")
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if not text:
            return 0
        
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            # Fallback to word count * 1.3
            print(f"Warning: Token counting failed, using word count: {e}")
            return int(len(text.split()) * 1.3)
    
    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in message list (for chat APIs)."""
        num_tokens = 0
        
        for message in messages:
            # Every message follows <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += self.TOKENS_PER_MESSAGE
            
            for key, value in message.items():
                num_tokens += self.count_tokens(value)
                if key == "name":
                    num_tokens += self.TOKENS_PER_NAME
        
        # Every reply is primed with <im_start>assistant
        num_tokens += 3
        
        return num_tokens


class SimpleTokenCounter(TokenCounter):
    """Simple token counter using word count approximation."""
    
    WORDS_PER_TOKEN = 0.75  # Approximation: 1 token ≈ 0.75 words
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using word count approximation."""
        if not text:
            return 0
        
        word_count = len(text.split())
        return int(word_count / self.WORDS_PER_TOKEN)
    
    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in message list."""
        total = 0
        for message in messages:
            for value in message.values():
                total += self.count_tokens(value)
            # Add overhead per message
            total += 4
        return total


class TokenBudget:
    """
    Token budget manager for context assembly.
    
    Manages token allocation across different sections of the prompt
    and enforces strict budget limits.
    """
    
    def __init__(self, total_budget: int, allocations: Dict[str, float]):
        """
        Initialize token budget.
        
        Args:
            total_budget: Total token budget available
            allocations: Dictionary of section -> percentage (0.0 to 1.0)
        """
        self.total_budget = total_budget
        self.allocations = allocations
        
        # Validate allocations sum to <= 1.0
        total_alloc = sum(allocations.values())
        if total_alloc > 1.0:
            raise ValueError(f"Total allocation {total_alloc} exceeds 1.0")
        
        # Calculate section budgets
        self.section_budgets = {
            section: int(total_budget * percentage)
            for section, percentage in allocations.items()
        }
        
        # Track usage
        self.section_usage: Dict[str, int] = {section: 0 for section in allocations}
        self.total_usage = 0
    
    def get_budget(self, section: str) -> int:
        """Get token budget for a section."""
        return self.section_budgets.get(section, 0)
    
    def get_remaining(self, section: str) -> int:
        """Get remaining tokens for a section."""
        budget = self.get_budget(section)
        used = self.section_usage.get(section, 0)
        return max(0, budget - used)
    
    def get_total_remaining(self) -> int:
        """Get total remaining tokens."""
        return max(0, self.total_budget - self.total_usage)
    
    def allocate(self, section: str, tokens: int) -> bool:
        """
        Try to allocate tokens to a section.
        
        Returns True if allocation successful, False if exceeds budget.
        """
        remaining = self.get_remaining(section)
        
        if tokens > remaining:
            return False
        
        self.section_usage[section] = self.section_usage.get(section, 0) + tokens
        self.total_usage += tokens
        return True
    
    def force_allocate(self, section: str, tokens: int):
        """Force allocate tokens even if exceeds budget."""
        self.section_usage[section] = self.section_usage.get(section, 0) + tokens
        self.total_usage += tokens
    
    def can_allocate(self, section: str, tokens: int) -> bool:
        """Check if tokens can be allocated to section."""
        return tokens <= self.get_remaining(section)
    
    def reset(self):
        """Reset all usage counters."""
        self.section_usage = {section: 0 for section in self.allocations}
        self.total_usage = 0
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get detailed usage report."""
        report = {
            "total_budget": self.total_budget,
            "total_used": self.total_usage,
            "total_remaining": self.get_total_remaining(),
            "utilization": self.total_usage / self.total_budget if self.total_budget > 0 else 0,
            "sections": {},
        }
        
        for section in self.allocations:
            budget = self.get_budget(section)
            used = self.section_usage.get(section, 0)
            report["sections"][section] = {
                "budget": budget,
                "used": used,
                "remaining": budget - used,
                "utilization": used / budget if budget > 0 else 0,
                "percentage": self.allocations[section],
            }
        
        return report
    
    def rebalance(self, allow_overflow: bool = False):
        """
        Rebalance budgets based on actual usage.
        
        If allow_overflow is True, can exceed section budgets using reserve.
        """
        if not allow_overflow:
            return
        
        # Calculate total used and available reserve
        total_allocated = sum(self.section_budgets.values())
        reserve = self.total_budget - total_allocated
        
        # Find sections that need more
        deficit_sections = []
        for section, used in self.section_usage.items():
            budget = self.section_budgets[section]
            if used > budget:
                deficit = used - budget
                deficit_sections.append((section, deficit))
        
        # Allocate from reserve
        for section, deficit in deficit_sections:
            if deficit <= reserve:
                self.section_budgets[section] += deficit
                reserve -= deficit
            else:
                self.section_budgets[section] += reserve
                reserve = 0
                break


class TokenAccountant:
    """
    Central token accounting system.
    
    Manages token counting and budget enforcement for the entire CMS.
    """
    
    def __init__(self, model: str = "gpt-4", max_tokens: int = 8192,
                 counter: Optional[TokenCounter] = None):
        self.model = model
        self.max_tokens = max_tokens
        
        # Initialize token counter
        if counter:
            self.counter = counter
        else:
            try:
                self.counter = TiktokenCounter(model)
            except Exception as e:
                print(f"Warning: Failed to initialize tiktoken, using simple counter: {e}")
                self.counter = SimpleTokenCounter()
        
        # Token budget (will be set by policy)
        self.budget: Optional[TokenBudget] = None
    
    def count(self, text: str) -> int:
        """Count tokens in text."""
        return self.counter.count_tokens(text)
    
    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in messages."""
        return self.counter.count_messages(messages)
    
    def set_budget(self, allocations: Dict[str, float]):
        """Set token budget with section allocations."""
        self.budget = TokenBudget(self.max_tokens, allocations)
    
    def get_budget(self) -> Optional[TokenBudget]:
        """Get current token budget."""
        return self.budget
    
    def estimate_completion_tokens(self, prompt_tokens: int, 
                                   completion_ratio: float = 0.5) -> int:
        """
        Estimate completion tokens based on prompt.
        
        Args:
            prompt_tokens: Number of tokens in prompt
            completion_ratio: Ratio of completion to prompt (default 0.5)
        """
        return int(prompt_tokens * completion_ratio)
    
    def check_limits(self, prompt_tokens: int, 
                    max_completion_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Check if prompt + completion will exceed model limits.
        
        Returns:
            Dictionary with status and details
        """
        if max_completion_tokens is None:
            max_completion_tokens = self.estimate_completion_tokens(prompt_tokens)
        
        total_tokens = prompt_tokens + max_completion_tokens
        
        return {
            "within_limit": total_tokens <= self.max_tokens,
            "prompt_tokens": prompt_tokens,
            "max_completion_tokens": max_completion_tokens,
            "total_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "overflow": max(0, total_tokens - self.max_tokens),
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "counter_type": type(self.counter).__name__,
            "encoding": getattr(self.counter, "encoding_name", "unknown"),
        }
