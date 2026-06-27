import os
import json
import time
import logging
import pymupdf
from typing import List, Optional, Dict, Any

from hiring_agent.models import (
    JSONResume,
    Basics,
    Work,
    Education,
    Skill,
    Project,
    Award,
    BasicsSection,
    WorkSection,
    EducationSection,
    SkillsSection,
    ProjectsSection,
    AwardsSection,
)
from hiring_agent.llm_utils import call_llm, extract_json_from_response
from hiring_agent.pymupdf_rag import to_markdown
from hiring_agent.prompts.template_manager import TemplateManager
from hiring_agent.transform import transform_parsed_data

logger = logging.getLogger(__name__)

class PDFHandler:
    def __init__(self):
        self.template_manager = TemplateManager()

    async def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            # PyMuPDF opening is quick, but we can offload to thread pool to be fully async-safe
            import asyncio
            loop = asyncio.get_running_loop()
            
            def _read_pdf():
                with pymupdf.open(pdf_path) as doc:
                    pages = list(range(doc.page_count))
                    return to_markdown(doc, pages=pages)

            resume_text = await loop.run_in_executor(None, _read_pdf)
            logger.debug(
                f"Extracted text from PDF: {len(resume_text) if resume_text else 0} characters"
            )
            return resume_text
        except Exception as e:
            logger.error(f"An error occurred while reading the PDF: {e}")
            return None

    async def _call_llm_for_section(
        self, section_name: str, text_content: str, prompt: str, return_model=None
    ) -> Optional[Dict]:
        try:
            start_time = time.time()
            logger.debug(
                f"🔄 Extracting {section_name} section using Gemini..."
            )

            section_system_message = self.template_manager.render_template(
                "system_message", section_name_param=section_name
            )
            if not section_system_message:
                logger.error(
                    f"❌ Failed to render system message template for {section_name}"
                )
                return None

            response_text = await call_llm(
                system_prompt=section_system_message,
                user_prompt=prompt,
                response_model=return_model
            )

            try:
                response_text = extract_json_from_response(response_text)
                json_start = response_text.find("{")
                json_end = response_text.rfind("}")
                if json_start != -1 and json_end != -1:
                    response_text = response_text[json_start : json_end + 1]
                parsed_data = json.loads(response_text)
                logger.debug(f"✅ Successfully extracted {section_name} section")

                transformed_data = transform_parsed_data(parsed_data)
                end_time = time.time()
                total_time = end_time - start_time
                logger.debug(
                    f"⏱️ Total time for separate section extraction ({section_name}): {total_time:.2f} seconds"
                )

                return transformed_data
            except json.JSONDecodeError as e:
                logger.error(f"❌ Error parsing JSON for {section_name} section: {e}")
                logger.error(f"Raw response: {response_text}")
                return None

        except Exception as e:
            logger.error(f"❌ Error calling LLM for {section_name} section: {e}")
            return None

    async def extract_basics_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template(
            "basics", text_content=resume_text
        )
        if not prompt:
            logger.error("❌ Failed to render basics template")
            return None
        return await self._call_llm_for_section("basics", resume_text, prompt, BasicsSection)

    async def extract_work_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template("work", text_content=resume_text)
        if not prompt:
            logger.error("❌ Failed to render work template")
            return None
        return await self._call_llm_for_section("work", resume_text, prompt, WorkSection)

    async def extract_education_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template(
            "education", text_content=resume_text
        )
        if not prompt:
            logger.error("❌ Failed to render education template")
            return None
        return await self._call_llm_for_section(
            "education", resume_text, prompt, EducationSection
        )

    async def extract_skills_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template(
            "skills", text_content=resume_text
        )
        if not prompt:
            logger.error("❌ Failed to render skills template")
            return None
        return await self._call_llm_for_section("skills", resume_text, prompt, SkillsSection)

    async def extract_projects_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template(
            "projects", text_content=resume_text
        )
        if not prompt:
            logger.error("❌ Failed to render projects template")
            return None
        return await self._call_llm_for_section(
            "projects", resume_text, prompt, ProjectsSection
        )

    async def extract_awards_section(self, resume_text: str) -> Optional[Dict]:
        prompt = self.template_manager.render_template(
            "awards", text_content=resume_text
        )
        if not prompt:
            logger.error("❌ Failed to render awards template")
            return None
        return await self._call_llm_for_section("awards", resume_text, prompt, AwardsSection)

    async def extract_json_from_text(self, resume_text: str) -> Optional[JSONResume]:
        try:
            return await self._extract_all_sections_separately(resume_text)
        except Exception as e:
            logger.error(f"Error calling LLM parser: {e}")
            return None

    async def extract_json_from_pdf(self, pdf_path: str) -> Optional[JSONResume]:
        try:
            logger.debug(f"📄 Extracting text from PDF: {pdf_path}")
            text_content = await self.extract_text_from_pdf(pdf_path)

            if not text_content:
                logger.error("❌ Failed to extract text from PDF")
                return None

            logger.debug(
                f"✅ Successfully extracted {len(text_content)} characters from PDF"
            )

            logger.debug("🔄 Extracting all sections separately...")
            return await self._extract_all_sections_separately(text_content)

        except Exception as e:
            logger.error(f"❌ Error during PDF to JSON extraction: {e}")
            return None

    async def _extract_section_data(
        self, text_content: str, section_name: str
    ) -> Optional[Dict]:
        section_extractors = {
            "basics": self.extract_basics_section,
            "work": self.extract_work_section,
            "education": self.extract_education_section,
            "skills": self.extract_skills_section,
            "projects": self.extract_projects_section,
            "awards": self.extract_awards_section,
        }

        if section_name not in section_extractors:
            logger.error(f"❌ Invalid section name: {section_name}")
            return None

        return await section_extractors[section_name](text_content)

    async def _extract_all_sections_separately(
        self, text_content: str
    ) -> Optional[JSONResume]:
        start_time = time.time()

        sections = ["basics", "work", "education", "skills", "projects", "awards"]

        complete_resume = {
            "basics": None,
            "work": None,
            "volunteer": None,
            "education": None,
            "awards": None,
            "certificates": None,
            "publications": None,
            "skills": None,
            "languages": None,
            "interests": None,
            "references": None,
            "projects": None,
            "meta": None,
        }

        for section_name in sections:
            section_data = await self._extract_section_data(text_content, section_name)

            if section_data:
                complete_resume.update(section_data)
                logger.debug(f"✅ Successfully extracted {section_name} section")
            else:
                logger.error(
                    f"⚠️ Failed to extract {section_name} section. Aborting extraction to prevent partial/invalid resume data."
                )
                return None

        try:
            if complete_resume.get("basics") and isinstance(
                complete_resume["basics"], dict
            ):
                try:
                    complete_resume["basics"] = Basics(**complete_resume["basics"])
                except Exception as e:
                    logger.error(f"❌ Error creating Basics object: {e}")
                    complete_resume["basics"] = None

            json_resume = JSONResume(**complete_resume)

            end_time = time.time()
            total_time = end_time - start_time
            logger.info(
                f"⏱️ Total time for separate section extraction: {total_time:.2f} seconds"
            )

            return json_resume

        except Exception as e:
            logger.error(f"❌ Error creating JSONResume object: {e}")
            return None

    # Convenience API aliases
    async def extract_all_from_pdf(self, filepath: str) -> Optional[JSONResume]:
        return await self.extract_json_from_pdf(filepath)

    async def extract_all_from_text(self, text: str) -> Optional[JSONResume]:
        return await self.extract_json_from_text(text)
