#!/usr/bin/env python3
"""
Autonomous LinkedIn Content Manager
===================================
Sequential CrewAI pipeline (LLM-only, no Serper / web-search tools):

    Research → Write → Critique → Optimize → Schedule

Requires OPENAI_API_KEY in .env.

CLI:
    python linkedin_content_manager.py --topic "AI in healthcare" --audience "CTOs"
    python linkedin_content_manager.py  # prompts for topic + audience

UI:
    streamlit run app.py
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys

from dotenv import load_dotenv

load_dotenv()

REQUIRED_KEYS = ("OPENAI_API_KEY",)

STAGES = (
    ("research", "Research", "Trend Researcher"),
    ("writing", "Writing", "Content Writer"),
    ("critique", "Critique", "Content Critic"),
    ("optimization", "Optimization", "Post Optimizer"),
    ("scheduling", "Scheduling", "Publishing Strategist"),
)


def require_env() -> None:
    """Raise if OPENAI_API_KEY is missing (UI-friendly; CLI exits)."""
    missing = [k for k in REQUIRED_KEYS if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and set OPENAI_API_KEY."
        )


def task_text(task) -> str:
    output = getattr(task, "output", None)
    if output is None:
        return "(no output)"
    return getattr(output, "raw", None) or str(output)


def banner(title: str) -> None:
    line = "=" * 72
    print(f"\n{line}\n  {title}\n{line}\n")


def _llm() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o")


def build_agents(verbose: bool):
    """Five specialized agents. Researcher is LLM-only (no Serper)."""
    from crewai import Agent

    llm = _llm()
    common = dict(llm=llm, verbose=verbose, allow_delegation=False)

    researcher = Agent(
        role="LinkedIn Trend Researcher",
        goal="Research latest trending topics, hashtags, and content themes for a given niche",
        backstory=(
            "Expert social media researcher who monitors LinkedIn trends, viral posts, "
            "and industry news; knows what drives engagement on LinkedIn. Works from "
            "deep knowledge of LinkedIn algorithms, B2B content patterns, and hashtag "
            "practice — no live web search."
        ),
        **common,
    )
    writer = Agent(
        role="LinkedIn Content Writer",
        goal="Write engaging, high-quality LinkedIn posts based on research provided",
        backstory=(
            "Seasoned LinkedIn ghostwriter for industry leaders; expert in LinkedIn "
            "algorithm, hook writing, storytelling, CTA placement, conversational professional tone."
        ),
        **common,
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
        **common,
    )
    optimizer = Agent(
        role="LinkedIn Post Optimizer",
        goal="Rewrite posts incorporating critic feedback to maximize LinkedIn engagement",
        backstory=(
            "LinkedIn growth expert and copywriter; master of formatting (short lines, "
            "strategic breaks, emoji usage, hashtag optimization, hook patterns, mobile readability)."
        ),
        **common,
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
        **common,
    )
    return {
        "research": researcher,
        "writing": writer,
        "critique": critic,
        "optimization": optimizer,
        "scheduling": scheduler,
    }


def build_tasks(agents: dict):
    """Five sequential tasks. Placeholders: topic, audience, plus prior-stage outputs."""
    from crewai import Task

    research_task = Task(
        description=(
            "You have no live web search. Using expert knowledge of LinkedIn content "
            "patterns, produce a research brief for niche `{topic}` aimed at `{audience}`. "
            "Identify 3–5 trending angles, relevant hashtags, and content hooks that "
            "typically perform well for this audience on LinkedIn."
        ),
        expected_output=(
            "Structured research brief with trending topics, suggested angles, "
            "top-performing hashtags, and content hook ideas."
        ),
        agent=agents["research"],
    )
    writing_task = Task(
        description=(
            "Using the research brief below, write a compelling LinkedIn post about `{topic}` "
            "for `{audience}`. Include a strong hook (first 2 lines), storytelling or "
            "value-driven body, clear CTA, and 150–300 words. Use trending angles and hooks "
            "from research.\n\nRESEARCH BRIEF:\n{research}"
        ),
        expected_output="Complete LinkedIn post draft with hook, body, CTA, and suggested hashtags.",
        agent=agents["writing"],
    )
    critique_task = Task(
        description=(
            "Critically review the LinkedIn post draft written for `{audience}` on `{topic}`. "
            "Evaluate hook strength (will people click \"see more\"?), storytelling quality, "
            "engagement potential, CTA effectiveness, tone consistency, LinkedIn formatting, "
            "and viral potential. Provide a score out of 10 and specific improvement suggestions.\n\n"
            "DRAFT:\n{writing}"
        ),
        expected_output=(
            "Detailed critique with scores, strengths, weaknesses, and specific "
            "actionable improvement suggestions."
        ),
        agent=agents["critique"],
    )
    optimization_task = Task(
        description=(
            "Take the original LinkedIn post and critic's feedback. Rewrite incorporating "
            "all feedback for `{audience}` on `{topic}`. Improve the hook, tighten copy, "
            "optimize formatting (short lines, line breaks, strategic emoji), strengthen CTA, "
            "and optimize hashtags. Produce final publish-ready version.\n\n"
            "DRAFT:\n{writing}\n\nCRITIQUE:\n{critique}"
        ),
        expected_output=(
            "Final, polished, publish-ready LinkedIn post with optimized formatting, "
            "hashtags, and CTA."
        ),
        agent=agents["optimization"],
    )
    scheduling_task = Task(
        description=(
            "Analyze the final post and target audience `{audience}` for `{topic}`. "
            "Recommend best day and time to publish (with timezone), provide the final "
            "formatted post ready for LinkedIn copy-paste, and include a brief with hashtag "
            "strategy and first-hour engagement tips.\n\nFINAL POST:\n{optimization}"
        ),
        expected_output=(
            "Complete publishing brief with recommended posting time, final formatted post, "
            "hashtag list, and first-hour engagement strategy."
        ),
        agent=agents["scheduling"],
    )
    return {
        "research": research_task,
        "writing": writing_task,
        "critique": critique_task,
        "optimization": optimization_task,
        "scheduling": scheduling_task,
    }


def run_stage(
    stage_key: str,
    agents: dict,
    tasks: dict,
    inputs: dict,
    verbose: bool,
) -> tuple[str, str]:
    """Run one pipeline stage. Returns (output_text, captured_stdout)."""
    from crewai import Crew, Process

    buf = io.StringIO()
    task = tasks[stage_key]
    crew = Crew(
        agents=[agents[stage_key]],
        tasks=[task],
        process=Process.sequential,
        verbose=verbose,
        memory=False,
        tracing=False,
    )
    with contextlib.redirect_stdout(buf):
        try:
            crew.kickoff(inputs=inputs)
        except Exception as exc:
            text = str(exc)
            if "insufficient_quota" in text or "credit_balance_exhausted" in text:
                raise RuntimeError(
                    "OpenAI API has no remaining credits. Add billing or set a billed OPENAI_API_KEY in .env."
                ) from exc
            raise
    logs = buf.getvalue()
    return task_text(task), logs


def run_pipeline(
    topic: str,
    audience: str,
    verbose: bool = False,
    on_stage=None,
) -> dict:
    """
    Execute the 5-stage crew sequentially.

    on_stage(event, stage_key, payload) is called with:
      event='start'  payload=None
      event='done'   payload={'text': str, 'logs': str}
    """
    require_env()
    agents = build_agents(verbose=verbose)
    tasks = build_tasks(agents)
    inputs = {"topic": topic, "audience": audience}
    results = {}

    for key, _label, _role in STAGES:
        if on_stage:
            on_stage("start", key, None)
        text, logs = run_stage(key, agents, tasks, inputs, verbose)
        results[key] = {"text": text, "logs": logs}
        inputs[key] = text
        if on_stage:
            on_stage("done", key, results[key])

    return results


def run(topic: str, audience: str, verbose: bool = True) -> None:
    banner(f"LINKEDIN CONTENT CREW  |  topic: {topic}  |  audience: {audience}")

    def _print(event, key, payload):
        label = next(s[1] for s in STAGES if s[0] == key)
        if event == "start":
            banner(label.upper())
        elif event == "done":
            if verbose and payload.get("logs"):
                print(payload["logs"])
            print(payload["text"])

    try:
        results = run_pipeline(topic, audience, verbose=verbose, on_stage=_print)
    except Exception as exc:
        print(f"\nCrew run failed: {exc}")
        sys.exit(1)

    banner("FINAL PUBLISHING BRIEF")
    print(results["scheduling"]["text"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autonomous LinkedIn Content Manager (CrewAI)")
    parser.add_argument("--topic", "-t", help="Niche or topic for the LinkedIn post")
    parser.add_argument("--audience", "-a", help="Target audience for the post")
    parser.add_argument("--verbose", "-v", action="store_true", default=True)
    parser.add_argument("--quiet", "-q", action="store_true", help="Disable verbose agent logs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        require_env()
    except RuntimeError as exc:
        print(exc)
        sys.exit(1)

    topic = (args.topic or input("Enter LinkedIn topic/niche: ")).strip()
    audience = (args.audience or input("Enter target audience: ")).strip()
    if not topic:
        print("A topic is required.")
        sys.exit(1)
    if not audience:
        print("An audience is required.")
        sys.exit(1)
    run(topic, audience, verbose=not args.quiet)


if __name__ == "__main__":
    main()
