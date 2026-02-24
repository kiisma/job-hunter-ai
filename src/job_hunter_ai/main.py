from __future__ import annotations

import argparse
from pathlib import Path

from .config import CandidateProfile, RunConfig, SearchConfig
from .workflow import JobHunterWorkflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automated job hunt assistant")
    parser.add_argument("--name", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--skills", required=True, help="comma-separated")
    parser.add_argument("--experience", required=True, help="comma-separated")
    parser.add_argument("--resume", required=True, type=Path)
    parser.add_argument("--query", required=True)
    parser.add_argument("--area", default="1", help="hh.ru area code")
    parser.add_argument("--per-page", type=int, default=30)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--min-score", type=float, default=0.25)
    parser.add_argument("--max-targets", type=int, default=10)
    parser.add_argument("--output-dir", default="output", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    profile = CandidateProfile(
        name=args.name,
        target_role=args.role,
        skills=[x.strip() for x in args.skills.split(",") if x.strip()],
        core_experience=[x.strip() for x in args.experience.split(",") if x.strip()],
        base_resume_path=args.resume,
    )
    config = RunConfig(
        search=SearchConfig(
            query=args.query,
            area=args.area,
            per_page=args.per_page,
            pages=args.pages,
        ),
        profile=profile,
        min_score=args.min_score,
        max_targets=args.max_targets,
        output_dir=args.output_dir,
    )

    queue = JobHunterWorkflow(config).run()
    print(f"Prepared {len(queue)} targeted applications. See {args.output_dir}/application_queue.json")


if __name__ == "__main__":
    main()
