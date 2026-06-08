import json
import os
import re
from dataclasses import dataclass

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types


@dataclass
class UserRequirements:
    frontend: str
    backend: str
    database: str
    extra_requirements: str
    provider: str


@dataclass
class AIRecommendation:
    parsed: dict | None
    raw_text: str | None


class AppConfig:
    api_key_names = ["STREAMLIT_GEMINI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"]
    gemini_model = "gemini-2.5-flash"

    def __init__(self):
        load_dotenv()

    def get_api_key(self):
        for key_name in self.api_key_names:
            api_key = os.getenv(key_name)
            if api_key:
                return api_key
        return None

    def api_key_error_message(self):
        return "Set STREAMLIT_GEMINI_API_KEY, GEMINI_API_KEY, or GOOGLE_API_KEY in your environment."


class PromptBuilder:
    def build(self, requirements: UserRequirements):
        return f"""
You are a cloud solutions architect assistant for a non-technical user.
The user provides the following application details:

Frontend: {requirements.frontend}
Backend: {requirements.backend}
Database: {requirements.database}
Additional requirements: {requirements.extra_requirements}

Generate a recommendation for {requirements.provider} cloud deployment.
Return only valid JSON in the response.
The JSON object must include these fields:
- architecture_summary: string
- services: object with frontend, backend, database, monitoring, security, ci_cd
- cost_estimate: object with monthly_estimate and notes
- mermaid_diagram: string containing Mermaid diagram code only
- raw_recommendation: string with a short user-friendly summary

Example response:
{{
  "architecture_summary": "...",
  "services": {{
    "frontend": "...",
    "backend": "...",
    "database": "...",
    "monitoring": "...",
    "security": "...",
    "ci_cd": "..."
  }},
  "cost_estimate": {{
    "monthly_estimate": "...",
    "notes": "..."
  }},
  "mermaid_diagram": "graph TD; ...",
  "raw_recommendation": "..."
}}
"""


class AIResponseParser:
    @staticmethod
    def extract_json(text):
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return text[start:end + 1]

    def parse(self, raw_text):
        json_text = self.extract_json(raw_text)
        if not json_text:
            return None
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            cleaned = json_text.replace("'", '"')
            cleaned = re.sub(r",\s*\}", "}", cleaned)
            cleaned = re.sub(r",\s*\]", "]", cleaned)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return None


class GeminiRecommendationClient:
    def __init__(self, config: AppConfig, prompt_builder: PromptBuilder, parser: AIResponseParser):
        self.config = config
        self.prompt_builder = prompt_builder
        self.parser = parser

    def get_recommendation(self, requirements: UserRequirements):
        api_key = self.config.get_api_key()
        if not api_key:
            st.error(self.config.api_key_error_message())
            return AIRecommendation(parsed=None, raw_text=None)

        client = genai.Client(api_key=api_key)
        prompt = self.prompt_builder.build(requirements)

        try:
            response = client.models.generate_content(
                model=self.config.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are a helpful cloud solutions architect assistant.",
                    temperature=0.4,
                    max_output_tokens=1000,
                    response_mime_type="application/json",
                ),
            )
            raw_text = (response.text or "").strip()
            parsed = self.parser.parse(raw_text)
            return AIRecommendation(parsed=parsed, raw_text=raw_text)
        except Exception as exc:
            st.error(f"AI request failed: {exc}")
            return AIRecommendation(parsed=None, raw_text=None)


class MermaidRenderer:
    @staticmethod
    def clean(diagram_text):
        cleaned = diagram_text.strip().strip("`\n")
        cleaned = re.sub(r"^```mermaid\s*", "", cleaned, flags=re.IGNORECASE)
        return re.sub(r"```$", "", cleaned)

    def render(self, diagram_text):
        cleaned = self.clean(diagram_text)
        if cleaned:
            st.markdown(f"```mermaid\n{cleaned}\n```")
        else:
            st.warning("No Mermaid diagram content found.")


class ArchitectureRecommenderApp:
    def __init__(self):
        config = AppConfig()
        parser = AIResponseParser()
        prompt_builder = PromptBuilder()
        self.ai_client = GeminiRecommendationClient(config, prompt_builder, parser)
        self.diagram_renderer = MermaidRenderer()

    def run(self):
        st.set_page_config(page_title="Cloud Architecture Recommender", layout="wide")
        st.title("Cloud Architecture Recommender")
        st.write("Phase 1 MVP: Get architecture recommendations as structured JSON, plus a rendered diagram.")

        requirements, submitted = self.render_form()
        if submitted:
            self.render_recommendation(requirements)

    def render_form(self):
        with st.form("architecture_form"):
            frontend = st.text_input("Frontend stack", "React, Next.js, Angular")
            backend = st.text_input("Backend stack", "Python Flask, Node.js Express, .NET, Java Spring")
            database = st.text_input("Database", "PostgreSQL, MySQL, MongoDB, DynamoDB")
            provider = st.selectbox("Preferred cloud provider", ["AWS", "Azure"])
            extra_requirements = st.text_area(
                "Additional requirements",
                "High availability, low cost, auto-scaling, CI/CD, security",
            )
            submitted = st.form_submit_button("Get Recommendation")

        requirements = UserRequirements(
            frontend=frontend,
            backend=backend,
            database=database,
            extra_requirements=extra_requirements,
            provider=provider,
        )
        return requirements, submitted

    def render_recommendation(self, requirements: UserRequirements):
        with st.spinner("Generating recommendation..."):
            recommendation = self.ai_client.get_recommendation(requirements)

        if recommendation.parsed:
            self.render_result(recommendation)
        else:
            st.error("Could not parse structured AI response. Check the raw output for details.")

    def render_result(self, recommendation: AIRecommendation):
        parsed = recommendation.parsed

        st.markdown("### Architecture Recommendation JSON")
        st.json(parsed)

        st.markdown("### Recommended Architecture")
        st.write(parsed.get("architecture_summary", "No summary returned."))

        st.markdown("### Key Services")
        services = parsed.get("services", {})
        for service_name, service_value in services.items():
            st.markdown(f"**{service_name.capitalize()}:** {service_value}")

        st.markdown("### Cost Estimate")
        cost = parsed.get("cost_estimate", {})
        st.markdown(f"**Monthly estimate:** {cost.get('monthly_estimate', 'N/A')}")
        st.write(cost.get("notes", ""))

        st.markdown("### Architecture Diagram")
        self.diagram_renderer.render(parsed.get("mermaid_diagram", ""))

        with st.expander("Raw AI response"):
            st.code(recommendation.raw_text, language="text")


if __name__ == "__main__":
    ArchitectureRecommenderApp().run()
