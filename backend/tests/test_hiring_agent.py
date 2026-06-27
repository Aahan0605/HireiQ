import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from hiring_agent.prompts.template_manager import TemplateManager
from hiring_agent.transform import to_hireiq_features
from hiring_agent.pdf_extractor import PDFHandler
from hiring_agent.evaluator import ResumeEvaluator
from hiring_agent.models import (
    JSONResume,
    Basics,
    Location,
    Profile,
    Work,
    Education,
    Skill,
    Project,
    Certificate,
    EvaluationData,
)

def test_template_manager():
    """Verify TemplateManager can load and render templates."""
    tm = TemplateManager()
    sections = tm.get_available_sections()
    assert "basics" in sections
    assert "system_message" in sections
    
    # Test rendering system message
    sys_msg = tm.render_template("system_message", section_name_param="basics")
    assert sys_msg is not None
    assert "basics" in sys_msg

def test_to_hireiq_features():
    """Verify JSONResume parses correctly into HireIQ features."""
    resume = JSONResume(
        basics=Basics(
            name="John Doe",
            email="john@example.com",
            phone="1234567890",
            location=Location(city="New York", countryCode="US"),
            profiles=[
                Profile(network="GitHub", url="https://github.com/johndoe"),
                Profile(network="LinkedIn", url="https://linkedin.com/in/johndoe"),
            ]
        ),
        skills=[
            Skill(name="Python", keywords=["django", "fastapi"]),
            Skill(name="JavaScript", keywords=["react"]),
        ],
        work=[
            Work(
                name="Acme Corp",
                position="Software Engineer",
                startDate="2020-01",
                endDate="2023-01",
                summary="Developed stuff",
            )
        ],
        education=[
            Education(
                institution="State University",
                studyType="Bachelor of Science",
                area="Computer Science",
            )
        ],
        certificates=[
            Certificate(name="AWS Certified Solutions Architect")
        ],
        projects=[
            Project(name="Awesome Web App")
        ]
    )

    features = to_hireiq_features(resume)
    assert features["name"] == "John Doe"
    assert features["email"] == "john@example.com"
    assert features["phone"] == "1234567890"
    assert "New York" in features["location"]
    assert "US" in features["location"]
    assert "Python" in features["skills"]
    assert "react" in features["skills"]
    assert features["experience"] == 3.0
    assert "Bachelor of Science Computer Science at State University" in features["education"]
    assert "AWS Certified Solutions Architect" in features["certifications"]
    assert "Awesome Web App" in features["projects"]
    assert features["github"] == "johndoe"
    assert features["linkedin"] == "https://linkedin.com/in/johndoe"

@pytest.mark.asyncio
@patch("hiring_agent.pdf_extractor.call_llm", new_callable=AsyncMock)
async def test_pdf_handler(mock_call_llm):
    """Verify PDFHandler extracts resume sections asynchronously using call_llm."""
    # Mock call_llm response to return mock JSONResume section data
    mock_call_llm.side_effect = [
        '{"basics": {"name": "Jane Doe", "email": "jane@example.com"}}',  # basics
        '{"work": []}',                                                    # work
        '{"education": []}',                                               # education
        '{"skills": []}',                                                  # skills
        '{"projects": []}',                                                # projects
        '{"awards": []}',                                                  # awards
    ]

    handler = PDFHandler()
    
    # Mock to_markdown and pymupdf.open calls to avoid actual file read
    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_doc.__enter__.return_value = mock_doc
    with patch("pymupdf.open", return_value=mock_doc):
        with patch("hiring_agent.pdf_extractor.to_markdown", return_value="Dummy Resume Text"):
            with patch("os.path.exists", return_value=True):
                resume = await handler.extract_json_from_pdf("dummy.pdf")
                assert resume is not None
                assert resume.basics.name == "Jane Doe"
                assert resume.basics.email == "jane@example.com"
                assert mock_call_llm.call_count == 6

@pytest.mark.asyncio
@patch("hiring_agent.evaluator.call_llm", new_callable=AsyncMock)
async def test_resume_evaluator(mock_call_llm):
    """Verify ResumeEvaluator gets fairness-constrained score evaluation."""
    mock_response = """
    {
        "scores": {
            "open_source": {"score": 25, "max": 35, "evidence": "Good open source work"},
            "self_projects": {"score": 20, "max": 30, "evidence": "Multiple web projects"},
            "production": {"score": 15, "max": 25, "evidence": "1 internship"},
            "technical_skills": {"score": 8, "max": 10, "evidence": "Strong Python/JS"}
        },
        "bonus_points": {"total": 5, "breakdown": "+5 GSoC"},
        "deductions": {"total": 2, "reasons": "-2 tutorial projects"},
        "key_strengths": ["Python expertise"],
        "areas_for_improvement": ["more testing"]
    }
    """
    mock_call_llm.return_value = mock_response

    evaluator = ResumeEvaluator()
    evaluation = await evaluator.evaluate_resume("Dummy Resume Text", "Looking for Python Engineer")
    
    assert evaluation is not None
    assert evaluation.scores.open_source.score == 25
    assert evaluation.scores.technical_skills.score == 8
    assert evaluation.bonus_points.total == 5
    assert evaluation.deductions.total == 2
    assert "Python expertise" in evaluation.key_strengths
    assert "more testing" in evaluation.areas_for_improvement
