from datetime import datetime
import json5 as json
from .utils.views import print_agent_output
from .utils.llms import call_model
from loguru import logger

sample_json = """
{
  "table_of_contents": A table of contents in markdown syntax (using '-') based on the research headers and subheaders,
  "introduction": An indepth introduction to the topic in markdown syntax and hyperlink references to relevant sources,
  "conclusion": A conclusion to the entire research based on all research data in markdown syntax and hyperlink references to relevant sources,
  "sources": A list with strings of all used source links in the entire research data in markdown syntax and apa citation format. For example: ['-  Title, year, Author [source url](source)', ...]
}
"""


class WriterAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None, guardrails=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers
        self.guardrails = guardrails

    def get_headers(self, research_state: dict):
        return {
            "title": research_state.get("title"),
            "date": "Date",
            "introduction": "Introduction",
            "table_of_contents": "Table of Contents",
            "conclusion": "Conclusion",
            "references": "References",
        }

    async def write_sections(self, research_state: dict):
        query = research_state.get("title")
        data = research_state.get("research_data")
        task = research_state.get("task")
        follow_guidelines = task.get("follow_guidelines")
        guidelines = task.get("guidelines")

        prompt = [
            {
                "role": "system",
                "content": "You are a research writer. Your sole purpose is to write a well-written "
                "research reports about a "
                "topic based on research findings and information.\n ",
            },
            {
                "role": "user",
                "content": f"Today's date is {datetime.now().strftime('%d/%m/%Y')}\n."
                f"Query or Topic: {query}\n"
                f"Research data: {str(data)}\n"
                f"Your task is to write an in depth, well written and detailed "
                f"introduction and conclusion to the research report based on the provided research data. "
                f"Do not include headers in the results.\n"
                f"You MUST include any relevant sources to the introduction and conclusion as markdown hyperlinks -"
                f"For example: 'This is a sample text. ([url website](url))'\n\n"
                f"{f'You must follow the guidelines provided: {guidelines}' if follow_guidelines else ''}\n"
                f"You MUST return nothing but a JSON in the following format (without json markdown):\n"
                f"{sample_json}\n\n",
            },
        ]

        # Apply guardrails to the writing prompt if available
        if self.guardrails:
            try:
                writing_content = prompt[1]["content"]
                safe_content = await self.guardrails.apply_guardrails(
                    writing_content,
                    agent_type="writer",
                    is_input=True
                )
                prompt[1]["content"] = safe_content
            except Exception as e:
                logger.error(f"Error applying guardrails to writing input: {e}")

        response = await call_model(
            prompt,
            task.get("model"),
            response_format="json",
            agent_type="writer"
        )
        
        # Handle case where response is a string (could happen after guardrails processing)
        if isinstance(response, str):
            try:
                # Try to parse the string as JSON
                logger.info("Attempting to parse string response as JSON")
                try:
                    response = json.loads(response)
                except:
                    # Try with json5 which is more forgiving
                    response = json.loads(response)
            except Exception as e:
                logger.error(f"Failed to parse response as JSON: {e}")
                # Create a minimum valid structure to prevent downstream errors
                response = {
                    "table_of_contents": "Error generating table of contents",
                    "introduction": "Error generating introduction",
                    "conclusion": "Error generating conclusion",
                    "sources": ["Error retrieving sources"]
                }
        
        # Apply guardrails to individual sections if needed
        if self.guardrails and isinstance(response, dict):
            try:
                for key in ["introduction", "conclusion"]:
                    if key in response and response[key]:
                        safe_text = await self.guardrails.apply_guardrails(
                            response[key],
                            agent_type="writer",
                            is_input=False
                        )
                        response[key] = safe_text
            except Exception as e:
                logger.error(f"Error applying guardrails to written sections: {e}")
                
        # Ensure required keys exist
        required_keys = ["table_of_contents", "introduction", "conclusion", "sources"]
        for key in required_keys:
            if key not in response:
                logger.warning(f"Missing required key in response: {key}")
                response[key] = f"Error generating {key}"
                
        return response

    async def revise_headers(self, task: dict, headers: dict):
        prompt = [
            {
                "role": "system",
                "content": """You are a research writer. 
Your sole purpose is to revise the headers data based on the given guidelines.""",
            },
            {
                "role": "user",
                "content": f"""Your task is to revise the given headers JSON based on the guidelines given.
You are to follow the guidelines but the values should be in simple strings, ignoring all markdown syntax.
You must return nothing but a JSON in the same format as given in headers data.
Guidelines: {task.get("guidelines")}\n
Headers Data: {headers}\n
""",
            },
        ]

        # Apply guardrails to headers prompt if available
        if self.guardrails:
            try:
                headers_content = prompt[1]["content"]
                safe_content = await self.guardrails.apply_guardrails(
                    headers_content,
                    agent_type="writer",
                    is_input=True
                )
                prompt[1]["content"] = safe_content
            except Exception as e:
                logger.error(f"Error applying guardrails to headers input: {e}")

        response = await call_model(
            prompt,
            task.get("model"),
            response_format="json",
            agent_type="writer"
        )
        
        # Handle string response (could happen after guardrails processing)
        if isinstance(response, str):
            try:
                logger.info("Attempting to parse headers string response as JSON")
                try:
                    response = json.loads(response)
                except:
                    response = json.loads(response)
            except Exception as e:
                logger.error(f"Failed to parse headers response as JSON: {e}")
                # Use original headers as fallback
                response = headers
        
        # Apply guardrails to headers response
        if self.guardrails and isinstance(response, dict):
            try:
                for key, value in response.items():
                    if isinstance(value, str) and value:
                        response[key] = await self.guardrails.apply_guardrails(
                            value,
                            agent_type="writer",
                            is_input=False
                        )
            except Exception as e:
                logger.error(f"Error applying guardrails to headers: {e}")
                
        return {"headers": response}

    async def run(self, research_state: dict):
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "writing_report",
                f"Writing final research report based on research data...",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Writing final research report based on research data...",
                agent="WRITER",
            )

        try:
            research_layout_content = await self.write_sections(research_state)

            if research_state.get("task", {}).get("verbose", False):
                if self.websocket and self.stream_output:
                    research_layout_content_str = json.dumps(
                        research_layout_content, indent=2
                    )
                    await self.stream_output(
                        "logs",
                        "research_layout_content",
                        research_layout_content_str,
                        self.websocket,
                    )
                else:
                    print_agent_output(research_layout_content, agent="WRITER")

            headers = self.get_headers(research_state)
            if research_state.get("task", {}).get("follow_guidelines", False):
                if self.websocket and self.stream_output:
                    await self.stream_output(
                        "logs",
                        "rewriting_layout",
                        "Rewriting layout based on guidelines...",
                        self.websocket,
                    )
                else:
                    print_agent_output(
                        "Rewriting layout based on guidelines...", agent="WRITER"
                    )
                headers_result = await self.revise_headers(
                    task=research_state.get("task"), headers=headers
                )
                
                # Ensure we properly handle the headers result
                if isinstance(headers_result, dict) and "headers" in headers_result:
                    headers = headers_result.get("headers")
                else:
                    logger.warning("Headers revise did not return expected format")

            # Ensure research_layout_content is a dictionary
            if not isinstance(research_layout_content, dict):
                logger.error(f"research_layout_content is not a dictionary: {type(research_layout_content)}")
                research_layout_content = {
                    "table_of_contents": "Error generating content",
                    "introduction": "Error generating content",
                    "conclusion": "Error generating content",
                    "sources": ["Error retrieving sources"]
                }

            result = {**research_layout_content, "headers": headers}
            return result
            
        except Exception as e:
            logger.error(f"Error in WriterAgent.run: {e}")
            # Return a minimal valid structure to prevent downstream errors
            return {
                "table_of_contents": "Error generating report",
                "introduction": "Error generating report",
                "conclusion": "Error generating report",
                "sources": ["Error retrieving sources"],
                "headers": self.get_headers(research_state),
                "error": str(e)
            }
