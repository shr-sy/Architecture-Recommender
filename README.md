# Cloud Architecture Recommender

A Python Streamlit application for non-technical users to describe frontend, backend, database, and deployment preferences. The app uses an AI model to recommend cloud deployment architecture for AWS and Azure, generate an architecture diagram, and estimate costs.

## Features

- User-friendly form for application details
- Structured JSON architecture recommendation output
- Mermaid architecture diagram generation
- Basic cost estimation guidance

## Phase 1 MVP

This project implements the Phase 1 flow:

- User Requirements → AI Recommendation → JSON Output → Architecture Diagram

Future phases planned:

- Phase 2: AWS cost estimation
- Phase 3: Terraform code generation
- Phase 4: Manager-ready PDF report
- Phase 5: Interactive polished UI

## Setup

1. Install Python 3.10+.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set your Gemini API key in an environment variable:
   ```bash
   set STREAMLIT_GEMINI_API_KEY=your_api_key_here
   ```
5. Run the app:
   ```bash
   streamlit run app.py
   ```

## Notes

- This app is client-side in the sense that it runs locally with Streamlit.
- The app uses Google's `gemini-2.5-flash` model through the Gemini API.
