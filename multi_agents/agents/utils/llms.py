import json_repair
from langchain_community.adapters.openai import convert_openai_messages
from langchain_core.utils.json import parse_json_markdown
from loguru import logger

from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion

# Import GuardrailsManager
from multi_agents.guardrails.guardrails_manager import GuardrailsManager

# Singleton instance for guardrails manager
_guardrails_manager = None

def get_guardrails_manager():
    """Get or initialize the guardrails manager singleton"""
    global _guardrails_manager
    if _guardrails_manager is None:
        try:
            _guardrails_manager = GuardrailsManager()
        except Exception as e:
            logger.error(f"Failed to initialize guardrails manager: {e}")
            _guardrails_manager = None
    return _guardrails_manager


async def call_model(
    prompt: list,
    model: str,
    response_format: str | None = None,
    agent_type: str | None = None,
):
    """
    Call LLM with NeMo Guardrails protection
    
    Args:
        prompt: The prompt messages to send to the LLM
        model: The model to use
        response_format: Format for response (e.g., "json")
        agent_type: Type of agent making the call (for specialized guardrails)
    """
    cfg = Config()
    lc_messages = convert_openai_messages(prompt)
    
    # Get content for guardrails check
    content = prompt[-1]["content"] if isinstance(prompt, list) and prompt else ""
    
    # Apply input guardrails if available
    guardrails = get_guardrails_manager()
    if guardrails:
        try:
            safe_content = await guardrails.apply_guardrails(content, agent_type=agent_type, is_input=True)
            
            # Check if content was blocked by guardrails
            if "cannot assist" in safe_content.lower() or "violated guidelines" in safe_content.lower():
                return safe_content
                
            # If content was modified, update the prompt
            if safe_content != content:
                if isinstance(prompt, list) and prompt:
                    prompt[-1]["content"] = safe_content
                    lc_messages = convert_openai_messages(prompt)
        except Exception as e:
            logger.error(f"Error applying input guardrails: {e}")
            # Continue with original content if guardrails fail

    try:
        # Call the model with potentially modified content
        response = await create_chat_completion(
            model=model,
            messages=lc_messages,
            temperature=0,
            llm_provider=cfg.smart_llm_provider,
            llm_kwargs=cfg.llm_kwargs,
            # cost_callback=cost_callback,
        )
        
        # Apply output guardrails to the response if available
        if guardrails:
            try:
                safe_response = await guardrails.apply_guardrails(
                    response, 
                    agent_type=agent_type, 
                    is_input=False
                )
                # Use the guardrailed response
                response = safe_response
            except Exception as e:
                logger.error(f"Error applying output guardrails: {e}")
                # Continue with original response if guardrails fail
        
        # For JSON responses, parse after guardrails are applied
        if response_format == "json":
            try:
                return parse_json_markdown(response, parser=json_repair.loads)
            except Exception as e:
                logger.error(f"Error parsing JSON response: {e}")
                return response
                
        return response

    except Exception as e:
        print("⚠️ Error in calling model")
        logger.error(f"Error in calling model: {e}")
        return f"Error: {str(e)}"
