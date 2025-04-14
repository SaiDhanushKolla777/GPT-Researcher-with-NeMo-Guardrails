import os
import time
import datetime
from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.memory import MemorySaver
from .utils.views import print_agent_output
from ..memory.research import ResearchState
from .utils.utils import sanitize_filename
from multi_agents.guardrails.guardrails_manager import GuardrailsManager
from loguru import logger

# Import agent classes
from . import \
    WriterAgent, \
    EditorAgent, \
    PublisherAgent, \
    ResearchAgent, \
    HumanAgent, \
    ReviewerAgent, \
    ReviserAgent


class ChiefEditorAgent:
    """Agent responsible for managing and coordinating editing tasks."""

    def __init__(self, task: dict, websocket=None, stream_output=None, tone=None, headers=None, guardrails_manager=None):
        self.task = task
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.tone = tone
        self.task_id = self._generate_task_id()
        self.output_dir = self._create_output_directory()
        
        # Initialize guardrails
        self.guardrails_manager = guardrails_manager or GuardrailsManager()

    def _generate_task_id(self):
        # Currently time based, but can be any unique identifier
        return int(time.time())

    def _create_output_directory(self):
        output_dir = "./outputs/" + \
            sanitize_filename(
                f"run_{self.task_id}_{self.task.get('query')[0:40]}")

        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def _initialize_agents(self):
        return {
            "writer": WriterAgent(self.websocket, self.stream_output, self.headers, guardrails=self.guardrails_manager),
            "editor": EditorAgent(self.websocket, self.stream_output, self.headers, guardrails=self.guardrails_manager),
            "research": ResearchAgent(self.websocket, self.stream_output, self.tone, self.headers, guardrails=self.guardrails_manager),
            "publisher": PublisherAgent(self.output_dir, self.websocket, self.stream_output, self.headers, guardrails=self.guardrails_manager),
            "human": HumanAgent(self.websocket, self.stream_output, self.headers),
            "reviewer": ReviewerAgent(self.websocket, self.stream_output, self.headers, guardrails=self.guardrails_manager),
            "reviser": ReviserAgent(self.websocket, self.stream_output, self.headers, guardrails=self.guardrails_manager)
        }

    def _create_workflow(self, agents):
        workflow = StateGraph(ResearchState)

        # Add nodes for each agent
        workflow.add_node("browser", agents["research"].run_initial_research)
        workflow.add_node("planner", agents["editor"].plan_research)
        workflow.add_node("researcher", agents["editor"].run_parallel_research)
        workflow.add_node("writer", agents["writer"].run)
        workflow.add_node("publisher", agents["publisher"].run)
        workflow.add_node("human", agents["human"].review_plan)
        
        # Add reviewer and reviser nodes if they exist in the workflow
        if "reviewer" in agents and "reviser" in agents:
            workflow.add_node("reviewer", agents["reviewer"].run)
            workflow.add_node("reviser", agents["reviser"].run)

        # Add edges
        self._add_workflow_edges(workflow)

        return workflow

    def _add_workflow_edges(self, workflow):
        workflow.add_edge('browser', 'planner')
        workflow.add_edge('planner', 'human')
        workflow.add_edge('researcher', 'writer')
        workflow.add_edge('writer', 'publisher')
        workflow.set_entry_point("browser")
        workflow.add_edge('publisher', END)

        # Add human in the loop
        workflow.add_conditional_edges(
            'human',
            lambda review: "accept" if review['human_feedback'] is None else "revise",
            {"accept": "researcher", "revise": "planner"}
        )

    def init_research_team(self):
        """Initialize and create a workflow for the research team."""
        agents = self._initialize_agents()
        return self._create_workflow(agents)

    async def _log_research_start(self):
        message = f"Starting the research process for query '{self.task.get('query')}'..."
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "starting_research", message, self.websocket)
        else:
            print_agent_output(message, "MASTER")

    async def run_research_task(self, task_id=None):
        """
        Run a research task with the initialized research team.

        Args:
            task_id (optional): The ID of the task to run.

        Returns:
            The result of the research task.
        """
        try:
            # Apply guardrails to the initial query
            if self.guardrails_manager:
                try:
                    original_query = self.task.get("query", "")
                    safe_query = await self.guardrails_manager.apply_guardrails(
                        original_query, 
                        agent_type="chief_editor",
                        is_input=True
                    )
                    
                    # Check if query was blocked
                    if isinstance(safe_query, str) and ("cannot assist" in safe_query.lower() or "violated guidelines" in safe_query.lower()):
                        logger.warning("Research query blocked by guardrails")
                        message = "This research query violates our guidelines."
                        if self.websocket and self.stream_output:
                            await self.stream_output("logs", "guardrails", message, self.websocket)
                        else:
                            print_agent_output(message, "GUARDRAILS")
                        return {"error": "Research query violated guidelines", "report": message}
                        
                    # Update query with guardrailed version if changed
                    if original_query != safe_query:
                        self.task["query"] = safe_query
                        logger.info("Query modified by guardrails")
                        
                except Exception as e:
                    logger.error(f"Error applying guardrails to query: {e}")
            
            # Initialize the research team and workflow
            research_team = self.init_research_team()
            chain = research_team.compile()

            await self._log_research_start()

            config = {
                "configurable": {
                    "thread_id": task_id,
                    "thread_ts": datetime.datetime.utcnow()
                }
            }

            # Run the research workflow
            result = await chain.ainvoke({"task": self.task}, config=config)
            
            # Handle string result (common when guardrails block content)
            if isinstance(result, str):
                logger.info("Received string result, wrapping in dictionary")
                result = {"report": result}
            
            # Apply guardrails to the final result if needed
            if self.guardrails_manager and isinstance(result, dict) and "report" in result:
                try:
                    report_content = result.get("report", "")
                    if report_content:
                        result["report"] = await self.guardrails_manager.apply_guardrails(
                            report_content,
                            agent_type="chief_editor",
                            is_input=False
                        )
                except Exception as e:
                    logger.error(f"Error applying guardrails to final report: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in research task: {e}")
            if self.websocket and self.stream_output:
                await self.stream_output("logs", "error", f"Research error: {str(e)}", self.websocket)
            else:
                print_agent_output(f"Research error: {str(e)}", "ERROR")
            return {"error": str(e), "report": f"An error occurred: {str(e)}"}
