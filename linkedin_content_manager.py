#!/usr/bin/env python3
"""
Autonomous LinkedIn Content Manager
===================================
Sequential CrewAI pipeline:

    Research → Write → Critique → Optimize → Schedule

Five specialized agents produce a publish-ready LinkedIn post plus a
scheduling brief. Requires OPENAI_API_KEY and SERPER_API_KEY in .env.

Usage:
    python linkedin_content_manager.py
    python linkedin_content_manager.py --topic "AI in healthcare"
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()

REQUIRED_KEYS = ("OPENAI_API_KEY", "SERPER_API_KEY")


def require_env() -> None:
    """Exit early if required API keys are missing."""
    missing = [k for k in REQUIRED_KEYS if not os.getenv(k)]
    if missing:
        print("Missing environment variables:", ", ".join(missing))
        print("Copy .env.example to .env and fill in your keys.")
        sys.exit(1)


def banner(title: str) -> None:
    """Print a visual stage separator in the console."""
    line = "=" * 72
    print(f"\n{line}\n  {title}\n{line}\n")


def task_text(task) -> str:
    """Extract readable output from a completed CrewAI task."""
    output = getattr(task, "output", None)
    if output is None:
        return "(no output)"
    return getattr(output, "raw", None) or str(output)


# ---------------------------------------------------------------------------
# Crew factory
# ---------------------------------------------------------------------------
def build_crew(topic: str):
    """
    Create the 5-agent sequential crew.

    Imports live here so --help / missing-env checks do not require
    crewai to initialize LLM clients at module load time.
    """
    from crewai import Agent, Crew, Process, Task
    from crewai_tools import ScrapeWebsiteTool, SerperDevTool

    search = SerperDevTool()
    scrape = ScrapeWebsiteTool()
    llm = os.getenv("OPENAI_MODEL", "gpt-4o")

    # --- Agents -----------------------------------------------------------
    researcher = Agent(
        role="LinkedIn Trend Researcher",
        goal="Research latest trending topics, hashtags, and content themes for a given niche",
        backstory=(
            "Expert social media researcher who monitors LinkedIn trends, viral posts, "
            "and industry news; knows what drives engagement on LinkedIn."
        ),
        tools=[search, scrape],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    writer = Agent(
        role="LinkedIn Content Writer",
        goal="Write engaging, high-quality LinkedIn posts based on research provided",
        backstory=(
            "Seasoned LinkedIn ghostwriter for industry leaders; expert in LinkedIn "
            "algorithm, hook writing, storytelling, CTA placement, and conversational "
            "professional tone."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    critic = Agent(
        role="Content Quality Critic",
        goal=(
            "Review LinkedIn posts and provide detailed constructive feedback on "
            "engagement potential, tone, structure, clarity, hook strength, and CTA effectiveness"
        ),
        backstory=(
            "Harsh but fair editor with thousands of LinkedIn post reviews; distinguishes "
            "posts that get 10 likes from those with 10k+ impressions; delivers specific, "
            "actionable feedback."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    optimizer = Agent(
        role="LinkedIn Post Optimizer",
        goal="Rewrite posts incorporating critic feedback to maximize LinkedIn engagement",
        backstory=(
            "LinkedIn growth expert and copywriter; master of formatting (short lines, "
            "strategic breaks, emoji usage, hashtag optimization, hook patterns, mobile readability)."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    scheduler = Agent(
        role="LinkedIn Publishing Strategist",
        goal=(
            "Determine optimal posting time, finalize formatting with hashtags, and create "
            "publishing-ready output with scheduling recommendations"
        ),
        backstory=(
            "LinkedIn analytics expert; understands optimal posting times by industry, "
            "audience timezone, and day of week."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # --- Tasks (strict order; later tasks receive prior outputs as context) --
    research_task = Task(
        description=(
            "Research latest trends, viral content patterns, and hot topics on LinkedIn "
            "for the niche: {topic}. Identify 3–5 trending angles, relevant hashtags, "
            "and content hooks currently performing well."
        ),
        expected_output=(
            "Structured research brief with trending topics, suggested angles, "
            "top-performing hashtags, and content hook ideas."
        ),
        agent=researcher,
    )

    writing_task = Task(
        description=(
            "Using the research brief, write a compelling LinkedIn post about {topic}. "
            "Include a strong hook (first 2 lines), storytelling or value-driven body, "
            "clear CTA, and 150–300 words. Use trending angles and hooks from research."
        ),
        expected_output="Complete LinkedIn post draft with hook, body, CTA, and suggested hashtags.",
        agent=writer,
        context=[research_task],
    )

    critique_task = Task(
        description=(
            "Critically review the LinkedIn post draft. Evaluate hook strength "
            '(will people click "see more"?), storytelling quality, engagement potential, '
            "CTA effectiveness, tone consistency, LinkedIn formatting, and viral potential. "
            "Provide a score out of 10 and specific improvement suggestions."
        ),
        expected_output=(
            "Detailed critique with scores, strengths, weaknesses, and specific "
            "actionable improvement suggestions."
        ),
        agent=critic,
        context=[writing_task],
    )

    optimization_task = Task(
        description=(
            "Take the original LinkedIn post and critic's feedback. Rewrite incorporating "
            "all feedback. Improve the hook, tighten copy, optimize formatting (short lines, "
            "line breaks, strategic emoji), strengthen CTA, and optimize hashtags. Produce "
            "final publish-ready version."
        ),
        expected_output=(
            "Final, polished, publish-ready LinkedIn post with optimized formatting, "
            "hashtags, and CTA."
        ),
        agent=optimizer,
        context=[writing_task, critique_task],
    )

    scheduling_task = Task(
        description=(
            "Analyze final post content and target audience for {topic}. Recommend best "
            "day and time to publish (with timezone), provide final formatted post ready "
            "for LinkedIn copy-paste, and include brief with hashtag strategy and first-hour "
            "engagement tips."
        ),
        expected_output=(
            "Complete publishing brief with recommended posting time, final formatted post, "
            "hashtag list, and first-hour engagement strategy."
        ),
        agent=scheduler,
        context=[optimization_task],
    )

    crew = Crew(
        agents=[researcher, writer, critic, optimizer, scheduler],
        tasks=[
            research_task,
            writing_task,
            critique_task,
            optimization_task,
            scheduling_task,
        ],
        process=Process.sequential,
        verbose=True,
        memory=True,
    )
    return crew, [
        ("RESEARCH", research_task),
        ("WRITING", writing_task),
        ("CRITIQUE", critique_task),
        ("OPTIMIZATION", optimization_task),
        ("SCHEDULING", scheduling_task),
    ]


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
def run(topic: str) -> None:
    banner(f"LINKEDIN CONTENT CREW  |  topic: {topic}")
    try:
        crew, stages = build_crew(topic)
        result = crew.kickoff(inputs={"topic": topic})
    except Exception as exc:
        print(f"\nCrew run failed: {exc}")
        sys.exit(1)

    for name, task in stages:
        banner(name)
        print(task_text(task))

    banner("FINAL PUBLISHING BRIEF")
    print(result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autonomous LinkedIn Content Manager (CrewAI)")
    parser.add_argument("--topic", "-t", help="Niche or topic for the LinkedIn post")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    require_env()
    topic = (args.topic or input("Enter LinkedIn topic/niche: ")).strip()
    if not topic:
        print("A topic is required.")
        sys.exit(1)
    run(topic)


if __name__ == "__main__":
    main()
