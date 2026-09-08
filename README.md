# Autonomous LinkedIn Content Manager

Sequential CrewAI pipeline that researches, drafts, critiques, optimizes, and schedules LinkedIn posts. **No Serper API key** — the researcher uses the LLM only.

```
Research → Write → Critique → Optimize → Schedule
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env` (GPT-4 / GPT-4o). Optional: `OPENAI_MODEL`.

## Streamlit UI

```bash
streamlit run app.py
```

Enter a **topic**, an **audience**, optionally enable **verbose** agent logs, then generate. The five stages animate while each agent runs.

## CLI

```bash
python linkedin_content_manager.py --topic "AI in healthcare" --audience "hospital CIOs"
python linkedin_content_manager.py --quiet --topic "..." --audience "..."
```

## Agents

| Stage | Agent | Tools |
| --- | --- | --- |
| Research | LinkedIn Trend Researcher | LLM only |
| Writing | LinkedIn Content Writer | LLM only |
| Critique | Content Quality Critic | LLM only |
| Optimization | LinkedIn Post Optimizer | LLM only |
| Scheduling | LinkedIn Publishing Strategist | LLM only |
