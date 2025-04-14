from nemoguardrails import RailsConfig, LLMRails
import os
from loguru import logger

class GuardrailsManager:
    """Centralized manager for NeMo Guardrails in the multi-agent system"""
    
    def __init__(self, config_path=None):
        """Initialize the guardrails manager with a config path.
        
        Args:
            config_path (str, optional): Path to the guardrails config. 
                Defaults to config/config.yml in the parent directory.
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "config/config.yml"
            )
        self.config_path = config_path
        self.config = self._load_config()
        self.rails = None if self.config is None else LLMRails(self.config)
        
    def _load_config(self):
        """Load the guardrails configuration from the config path.
        
        Returns:
            RailsConfig or None: The loaded configuration or None if loading failed.
        """
        try:
            return RailsConfig.from_path(self.config_path)
        except Exception as e:
            logger.error(f"Error loading guardrails configuration: {e}")
            return None
            
    async def apply_guardrails(self, text, agent_type=None, is_input=True):
        """Apply guardrails to text based on agent type.
        
        Args:
            text (str or dict): The text or data to apply guardrails to.
            agent_type (str, optional): The type of agent (e.g., "researcher", "editor").
            is_input (bool): Whether this is input text (True) or output text (False).
            
        Returns:
            str: The processed text after applying guardrails.
        """
        if self.rails is None:
            return text
            
        try:
            # Convert dict to string if necessary
            if isinstance(text, dict):
                text = str(text)
            
            # Skip empty or None values
            if not text:
                return text
                
            messages = []
            
            # Add agent-specific context
            if agent_type:
                messages.append({
                    "role": "system", 
                    "content": f"You are processing content for the {agent_type} agent."
                })
                
            # Add the actual content
            messages.append({
                "role": "user" if is_input else "assistant", 
                "content": text
            })
                
            # Apply rails
            result = await self.rails.generate_async(messages=messages)
            
            # Handle case where result might be a dictionary
            if isinstance(result, dict):
                if "content" in result:
                    return result["content"]
                return str(result)
                
            return result
        except Exception as e:
            logger.error(f"Error applying guardrails: {e}")
            return text
