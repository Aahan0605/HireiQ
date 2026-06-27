from typing import Dict, List, Optional, Tuple, Any
import logging
import json
import re

from hiring_agent.models import JSONResume, EvaluationData
from hiring_agent.llm_utils import call_llm, extract_json_from_response, DEFAULT_MODEL
from hiring_agent.prompts.template_manager import TemplateManager

logger = logging.getLogger(__name__)

MAX_BONUS_POINTS = 20
MIN_FINAL_SCORE = -20
MAX_FINAL_SCORE = 120

class ResumeEvaluator:
    def __init__(self, model_name: str = DEFAULT_MODEL, model_params: dict = None):
        if not model_name:
            raise ValueError("Model name cannot be empty")

        self.model_name = model_name
        self.model_params = model_params or {"temperature": 0.5, "top_p": 0.9}
        self.template_manager = TemplateManager()

    def _load_evaluation_prompt(self, resume_text: str) -> str:
        criteria_template = self.template_manager.render_template(
            "resume_evaluation_criteria", text_content=resume_text
        )
        if criteria_template is None:
            raise ValueError("Failed to load resume evaluation criteria template")
        return criteria_template

    async def evaluate_resume(self, resume_text: str, job_description: str = None) -> EvaluationData:
        self._last_resume_text = resume_text
        full_prompt = self._load_evaluation_prompt(resume_text)
        
        if job_description:
            full_prompt += (
                f"\n\n=== JOB DESCRIPTION ===\n"
                f"{job_description}\n\n"
                f"Analyze the candidate's alignment and assign scores considering the specific job description requirements above."
            )
            
        try:
            system_message = self.template_manager.render_template(
                "resume_evaluation_system_message"
            )
            if system_message is None:
                raise ValueError(
                    "Failed to load resume evaluation system message template"
                )

            response_text = await call_llm(
                system_prompt=system_message,
                user_prompt=full_prompt,
                response_model=EvaluationData,
                model_name=self.model_name,
                temperature=self.model_params.get("temperature", 0.5),
                top_p=self.model_params.get("top_p", 0.9),
            )

            response_text = extract_json_from_response(response_text)
            logger.debug(f"🔤 Prompt response: {response_text}")

            evaluation_dict = json.loads(response_text)
            evaluation_data = EvaluationData(**evaluation_dict)

            return evaluation_data

        except Exception as e:
            logger.error(f"Error evaluating resume: {str(e)}")
            raise

    # Alias to match prompt instructions (e.g. evaluate)
    async def evaluate(self, resume_text: str, job_description: str = None) -> EvaluationData:
        return await self.evaluate_resume(resume_text, job_description)
