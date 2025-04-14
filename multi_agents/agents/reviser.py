from .utils.views import print_agent_output
from .utils.llms import call_model
import json
from loguru import logger

sample_revision_notes = """
{
  "draft": { 
    draft title: The revised draft that you are submitting for review 
  },
  "revision_notes": Your message to the reviewer about the changes you made to the draft based on their feedback
}
"""


class ReviserAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None, guardrails=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.guardrails = guardrails

    async def revise_draft(self, draft_state: dict):
        """
        Review a draft article
        :param draft_state:
        :return:
        """
        review = draft_state.get("review")
        task = draft_state.get("task")
        draft_report = draft_state.get("draft")
        
        revision_content = f"""Draft:\n{draft_report}" + "Reviewer's notes:\n{review}\n\n
You have been tasked by your reviewer with revising the following draft, which was written by a non-expert.
If you decide to follow the reviewer's notes, please write a new draft and make sure to address all of the points they raised.
Please keep all other aspects of the draft the same.
You MUST return nothing but a JSON in the following format:
{sample_revision_notes}
"""
        
        # Apply guardrails to revision input if available
        if self.guardrails:
            try:
                safe_content = await self.guardrails.apply_guardrails(
                    revision_content,
                    agent_type="reviser",
                    is_input=True
                )
                revision_content = safe_content
                logger.info("Applied guardrails to revision prompt")
            except Exception as e:
                logger.error(f"Error applying guardrails to revision prompt: {e}")
                
        prompt = [
            {
                "role": "system",
                "content": "You are an expert writer. Your goal is to revise drafts based on reviewer notes.",
            },
            {
                "role": "user",
                "content": revision_content,
            },
        ]

        response = await call_model(
            prompt,
            model=task.get("model"),
            response_format="json",
            agent_type="reviser"
        )
        
        # Apply guardrails to the revised content if available
        if self.guardrails and isinstance(response, dict) and "draft" in response:
            try:
                # Process the draft content with guardrails
                if isinstance(response["draft"], dict):
                    # If draft is a dictionary with nested content
                    for key, value in response["draft"].items():
                        if isinstance(value, str) and value:
                            safe_value = await self.guardrails.apply_guardrails(
                                value,
                                agent_type="reviser",
                                is_input=False
                            )
                            response["draft"][key] = safe_value
                elif isinstance(response["draft"], str):
                    # If draft is directly a string
                    response["draft"] = await self.guardrails.apply_guardrails(
                        response["draft"],
                        agent_type="reviser",
                        is_input=False
                    )
                
                # Also apply guardrails to revision notes
                if "revision_notes" in response and response["revision_notes"]:
                    response["revision_notes"] = await self.guardrails.apply_guardrails(
                        response["revision_notes"],
                        agent_type="reviser",
                        is_input=False
                    )
                    
                logger.info("Applied guardrails to revised draft")
            except Exception as e:
                logger.error(f"Error applying guardrails to revised draft: {e}")
        
        return response

    async def run(self, draft_state: dict):
        print_agent_output(f"Rewriting draft based on feedback...", agent="REVISOR")
        revision = await self.revise_draft(draft_state)

        if draft_state.get("task").get("verbose"):
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "revision_notes",
                    f"Revision notes: {revision.get('revision_notes')}",
                    self.websocket,
                )
            else:
                print_agent_output(
                    f"Revision notes: {revision.get('revision_notes')}", agent="REVISOR"
                )

        return {
            "draft": revision.get("draft"),
            "revision_notes": revision.get("revision_notes"),
        }
