from gpt_researcher import GPTResearcher
from colorama import Fore, Style
from .utils.views import print_agent_output
from loguru import logger


class ResearchAgent:
    def __init__(self, websocket=None, stream_output=None, tone=None, headers=None, guardrails=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.tone = tone
        self.guardrails = guardrails

    async def research(self, query: str, research_report: str = "research_report",
                       parent_query: str = "", verbose=True, source="web", tone=None, headers=None):
        try:
            # Apply input guardrails if available
            if self.guardrails:
                try:
                    safe_query = await self.guardrails.apply_guardrails(
                        query, 
                        agent_type="researcher",
                        is_input=True
                    )
                    
                    # Check if query was blocked
                    if "cannot assist" in safe_query.lower() or "violated guidelines" in safe_query.lower():
                        logger.warning(f"Research query blocked by guardrails: {query}")
                        message = "This research query violates our guidelines."
                        if self.websocket and self.stream_output:
                            await self.stream_output("logs", "guardrails", message, self.websocket)
                        else:
                            print_agent_output(message, "GUARDRAILS")
                        return "This research query violates research guidelines."
                        
                    # Use the safe query
                    if safe_query != query:
                        logger.info(f"Query modified by guardrails: {query} -> {safe_query}")
                        query = safe_query
                except Exception as e:
                    logger.error(f"Error applying input guardrails: {e}")
            
            # Initialize the researcher
            researcher = GPTResearcher(query=query, report_type=research_report, parent_query=parent_query,
                                    verbose=verbose, report_source=source, tone=tone, websocket=self.websocket, headers=self.headers)
            # Conduct research on the given query
            await researcher.conduct_research()
            # Write the report
            report = await researcher.write_report()
            
            # Apply output guardrails if available
            if self.guardrails and report:
                try:
                    safe_report = await self.guardrails.apply_guardrails(
                        report, 
                        agent_type="researcher",
                        is_input=False
                    )
                    report = safe_report
                except Exception as e:
                    logger.error(f"Error applying output guardrails: {e}")
                    
            return report
        except Exception as e:
            logger.error(f"Error in research: {e}")
            return f"Error conducting research: {str(e)}"

    async def run_subtopic_research(self, parent_query: str, subtopic: str, verbose: bool = True, source="web", headers=None):
        try:
            report = await self.research(parent_query=parent_query, query=subtopic,
                                         research_report="subtopic_report", verbose=verbose, source=source, tone=self.tone, headers=None)
        except Exception as e:
            print(f"{Fore.RED}Error in researching topic {subtopic}: {e}{Style.RESET_ALL}")
            report = None
        return {subtopic: report}

    async def run_initial_research(self, research_state: dict):
        task = research_state.get("task")
        query = task.get("query")
        source = task.get("source", "web")

        if self.websocket and self.stream_output:
            await self.stream_output("logs", "initial_research", f"Running initial research on the following query: {query}", self.websocket)
        else:
            print_agent_output(f"Running initial research on the following query: {query}", agent="RESEARCHER")
        
        research_result = await self.research(query=query, verbose=task.get("verbose"),
                                              source=source, tone=self.tone, headers=self.headers)
        
        return {"task": task, "initial_research": research_result}

    async def run_depth_research(self, draft_state: dict):
        task = draft_state.get("task")
        topic = draft_state.get("topic")
        parent_query = task.get("query")
        source = task.get("source", "web")
        verbose = task.get("verbose")
        
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "depth_research", f"Running in depth research on the following report topic: {topic}", self.websocket)
        else:
            print_agent_output(f"Running in depth research on the following report topic: {topic}", agent="RESEARCHER")
        
        research_draft = await self.run_subtopic_research(parent_query=parent_query, subtopic=topic,
                                                          verbose=verbose, source=source, headers=self.headers)
        return {"draft": research_draft}
