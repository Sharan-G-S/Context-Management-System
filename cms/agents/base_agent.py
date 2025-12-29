"""
Base agent class for autonomous task execution.
Provides memory, tools, and decision-making capabilities.
"""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import uuid

from cms.llm.groq_client import GroqClient
from cms.storage.sqlite import SQLiteStorage


class BaseAgent:
    """Base class for autonomous agents."""
    
    def __init__(
        self,
        name: str,
        llm_client: GroqClient,
        storage: Optional[SQLiteStorage] = None,
        system_prompt: Optional[str] = None
    ):
        """Initialize agent.
        
        Args:
            name: Agent name
            llm_client: LLM client for reasoning
            storage: Optional storage for logging
            system_prompt: Optional system prompt
        """
        self.agent_id = str(uuid.uuid4())
        self.name = name
        self.llm = llm_client
        self.storage = storage
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        # Agent memory
        self.memory: List[Dict[str, Any]] = []
        self.tools: Dict[str, Callable] = {}
        self.max_iterations = 10
        
        # Register default tools
        self._register_default_tools()
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for agent."""
        return f"""You are {self.name}, an autonomous AI agent.
You can use tools to accomplish tasks.
Think step by step and explain your reasoning.
"""
    
    def _register_default_tools(self):
        """Register default tools available to agent."""
        self.register_tool("think", self._tool_think)
        self.register_tool("remember", self._tool_remember)
        self.register_tool("finish", self._tool_finish)
    
    def register_tool(self, name: str, func: Callable):
        """Register a tool for agent to use.
        
        Args:
            name: Tool name
            func: Tool function
        """
        self.tools[name] = func
    
    def _tool_think(self, thought: str) -> str:
        """Think about the problem."""
        self._add_to_memory("thought", thought)
        return f"Thought recorded: {thought}"
    
    def _tool_remember(self, query: str) -> str:
        """Retrieve from agent memory."""
        relevant = [
            m for m in self.memory
            if query.lower() in str(m).lower()
        ]
        return str(relevant[-5:]) if relevant else "No relevant memories found."
    
    def _tool_finish(self, result: str) -> str:
        """Mark task as complete with result."""
        self._add_to_memory("result", result)
        return f"Task completed: {result}"
    
    def _add_to_memory(self, type_: str, content: Any):
        """Add entry to agent memory."""
        entry = {
            'type': type_,
            'content': content,
            'timestamp': datetime.utcnow()
        }
        self.memory.append(entry)
        
        # Log to storage if available
        if self.storage:
            self.storage.log_agent_action(
                agent_id=self.agent_id,
                action=type_,
                result=content,
                metadata={'agent_name': self.name}
            )
    
    def _format_tools_description(self) -> str:
        """Format available tools for LLM."""
        tools_desc = "Available tools:\n"
        for tool_name in self.tools.keys():
            tools_desc += f"- {tool_name}\n"
        return tools_desc
    
    def _parse_action(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse action from LLM response.
        
        Expected format:
        Action: tool_name
        Input: tool_input
        """
        lines = response.strip().split('\n')
        action = None
        input_text = None
        
        for line in lines:
            if line.startswith('Action:'):
                action = line.replace('Action:', '').strip()
            elif line.startswith('Input:'):
                input_text = line.replace('Input:', '').strip()
        
        if action and action in self.tools:
            return {'action': action, 'input': input_text or ''}
        
        return None
    
    def run(self, task: str) -> Dict[str, Any]:
        """Execute task autonomously.
        
        Args:
            task: Task description
            
        Returns:
            Dict with 'success', 'result', 'iterations', 'memory'
        """
        self._add_to_memory("task", task)
        
        iteration = 0
        result = None
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Build prompt with memory
            recent_memory = self.memory[-10:]
            memory_str = "\n".join([
                f"{m['type']}: {m['content']}"
                for m in recent_memory
            ])
            
            prompt = f"""{self.system_prompt}

{self._format_tools_description()}

Task: {task}

Recent Memory:
{memory_str}

What is your next action? Format:
Action: <tool_name>
Input: <tool_input>

Response:"""
            
            # Get LLM decision
            response = self.llm.generate_text(
                prompt,
                temperature=0.7,
                max_tokens=512
            )
            
            self._add_to_memory("llm_response", response)
            
            # Parse and execute action
            action_dict = self._parse_action(response)
            
            if action_dict:
                action = action_dict['action']
                input_text = action_dict['input']
                
                # Execute tool
                tool_func = self.tools[action]
                tool_result = tool_func(input_text)
                
                self._add_to_memory("action_result", {
                    'action': action,
                    'input': input_text,
                    'result': tool_result
                })
                
                # Check if finished
                if action == "finish":
                    result = input_text
                    break
            else:
                # No valid action parsed
                self._add_to_memory("error", "Could not parse valid action")
        
        return {
            'success': result is not None,
            'result': result or "Task not completed within iteration limit",
            'iterations': iteration,
            'memory': self.memory
        }
    
    def get_memory(self) -> List[Dict[str, Any]]:
        """Get agent memory."""
        return self.memory
    
    def clear_memory(self):
        """Clear agent memory."""
        self.memory = []
