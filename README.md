# Autonomous LinkedIn Content Manager

Sequential CrewAI pipeline that researches, drafts, critiques, optimizes, and schedules LinkedIn posts.

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

Fill `.env` with:

- `OPENAI_API_KEY` — GPT-4 / GPT-4o
- `SERPER_API_KEY` — [Serper](https://serper.dev) web search

## Run

```bash
python linkedin_content_manager.py
python linkedin_content_manager.py --topic "AI in healthcare"
```

You will get console sections for each stage and a final copy-paste publishing brief (post, hashtags, recommended time, first-hour engagement tips).

## Agents

| Stage | Agent | Tools |
| --- | --- | --- |
| Research | LinkedIn Trend Researcher | SerperDevTool, ScrapeWebsiteTool |
| Writing | LinkedIn Content Writer | LLM only |
| Critique | Content Quality Critic | LLM only |
| Optimization | LinkedIn Post Optimizer | LLM only |
| Scheduling | LinkedIn Publishing Strategist | LLM only |

The crew uses `Process.sequential`, `verbose=True`, and `memory=True`. Each task receives the previous task output as context.
