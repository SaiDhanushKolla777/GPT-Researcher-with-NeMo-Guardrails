from dotenv import load_dotenv
import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from multi_agents.agents import ChiefEditorAgent
from multi_agents.guardrails.guardrails_manager import GuardrailsManager
import asyncio
import json
from gpt_researcher.utils.enum import Tone
from loguru import logger

# Run with LangSmith if API key is set
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
load_dotenv()

def open_task():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to task.json
    task_json_path = os.path.join(current_dir, 'task.json')
    
    with open(task_json_path, 'r') as f:
        task = json.load(f)

    if not task:
        raise Exception("No task found. Please ensure a valid task.json file is present in the multi_agents directory and contains the necessary task information.")

    # Override model with STRATEGIC_LLM if defined in environment
    strategic_llm = os.environ.get("STRATEGIC_LLM")
    if strategic_llm and ":" in strategic_llm:
        # Extract the model name (part after the colon)
        model_name = strategic_llm.split(":")[-1]
        task["model"] = model_name
    elif strategic_llm:
        task["model"] = strategic_llm

    return task

def initialize_guardrails():
    """Initialize the guardrails system"""
    try:
        # Check if guardrails config exists
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "config", 
            "config.yml"
        )
        
        if not os.path.exists(config_path):
            logger.warning(f"NeMo Guardrails config not found at {config_path}. Guardrails will be disabled.")
            return None
            
        return GuardrailsManager(config_path)
    except Exception as e:
        logger.error(f"Failed to initialize guardrails: {e}")
        return None

async def run_research_task(query, websocket=None, stream_output=None, tone=Tone.Objective, headers=None):
    task = open_task()
    task["query"] = query
    
    # Initialize guardrails
    guardrails_manager = initialize_guardrails()
    if guardrails_manager:
        logger.info("NeMo Guardrails initialized successfully")
        
        # Pre-check query with guardrails
        try:
            safe_query = await guardrails_manager.apply_guardrails(
                query, 
                agent_type="chief_editor",
                is_input=True
            )
            
            # Check if query was blocked
            if "cannot assist" in safe_query.lower() or "violated guidelines" in safe_query.lower():
                logger.warning("Research query blocked by guardrails")
                if websocket and stream_output:
                    await stream_output("logs", "guardrails", 
                                      "This research query violates our guidelines.", 
                                      websocket)
                return {"error": "Research query violated guidelines"}
                
            # Use the safe query
            task["query"] = safe_query
        except Exception as e:
            logger.error(f"Error applying guardrails to query: {e}")
    
    # Initialize the chief editor with guardrails
    chief_editor = ChiefEditorAgent(task, websocket, stream_output, tone, headers, guardrails_manager)
    research_report = await chief_editor.run_research_task()

    if websocket and stream_output:
        await stream_output("logs", "research_report", research_report, websocket)

    return research_report

async def main():
    task = open_task()
    
    # Initialize guardrails
    guardrails_manager = initialize_guardrails()
    if guardrails_manager:
        logger.info("NeMo Guardrails initialized successfully")
    
    # Initialize the chief editor with guardrails
    chief_editor = ChiefEditorAgent(task, guardrails_manager=guardrails_manager)
    research_report = await chief_editor.run_research_task(task_id=uuid.uuid4())

    return research_report

if __name__ == "__main__":
    asyncio.run(main())
