from __future__ import annotations

import argparse
from pathlib import Path

from .apply import save_application
from .config import settings
from .resume import tailor_resume
from .search import RemoteOKProvider, RemotiveProvider, fetch_from_providers, rank_jobs
from .storage import ApplicationStore


def providers_for(sources: str):
    mapping = {
        "remoteok": RemoteOKProvider,
        "remotive": RemotiveProvider,
    }
    result = []
    for name in [s.strip().lower() for s in sources.split(",") if s.strip()]:
        if name in mapping:
            result.append(mapping[name]())
    return result or [RemoteOKProvider(), RemotiveProvider()]


def cmd_search(args: argparse.Namespace) -> int:
    keys = [k.strip() for k in args.keywords.split(",") if k.strip()]
    jobs = fetch_from_providers(keys, args.limit, providers_for(args.sources))
    ranked = rank_jobs(jobs, keys)
    print("score\tsource\ttitle\tcompany\tlocation\turl")
    for score, job in ranked:
        print(f"{score:.1f}\t{job.source}\t{job.title}\t{job.company}\t{job.location}\t{job.url}")
    return 0


def cmd_pipeline(args: argparse.Namespace) -> int:
    base_resume = Path(args.resume_file).read_text(encoding="utf-8")
    keys = [k.strip() for k in args.keywords.split(",") if k.strip()]
    store = ApplicationStore(Path(args.store_path))

    jobs = fetch_from_providers(keys, args.limit, providers_for(args.sources))
    ranked = rank_jobs(jobs, keys)

    prepared = 0
    skipped = 0
    for score, job in ranked:
        if store.contains_job(job.source, job.id):
            skipped += 1
            continue

        tailored = tailor_resume(base_resume, job)
        artifact = save_application(job, tailored, Path(args.output_dir))
        store.save(store.make_record(job, tailored))
        prepared += 1
        print(f"Prepared {job.title} @ {job.company} ({job.source}, score={score:.1f}) -> {artifact}")

    print(f"Done. Prepared {prepared}, skipped duplicates {skipped}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job-hunter", description="Find jobs and prepare tailored applications")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search matched jobs")
    search.add_argument("--keywords", required=True, help="Comma-separated keywords")
    search.add_argument("--limit", type=int, default=settings.default_limit)
    search.add_argument("--sources", default="remoteok,remotive", help="Comma-separated list: remoteok,remotive")
    search.set_defaults(func=cmd_search)

    pipeline = subparsers.add_parser("pipeline", help="End-to-end preparation")
    pipeline.add_argument("--resume-file", required=True)
    pipeline.add_argument("--keywords", required=True)
    pipeline.add_argument("--limit", type=int, default=15)
    pipeline.add_argument("--sources", default="remoteok,remotive")
    pipeline.add_argument("--output-dir", default="applications")
    pipeline.add_argument("--store-path", default=str(settings.store_path), help="Path to local JSON store")
    pipeline.set_defaults(func=cmd_pipeline)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
