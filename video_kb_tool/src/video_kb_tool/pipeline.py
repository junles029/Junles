from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .downloader import DownloadResult, download_video
from .graph_builder import build_graph
from .kb_store import ingest_to_kb
from .media import extract_audio
from .summarizer import summarize_text
from .transcriber import pick_best_subtitle, save_subtitle_transcript, transcribe_audio
from .utils import ensure_dir, safe_slug, sha1_text, write_json, write_text


ProgressCallback = Callable[[int, int, str], None]


@dataclass
class IngestOptions:
    url: str
    workdir: Path
    kb_root: Path
    title: Optional[str] = None
    summary_provider: str = 'extractive'
    openai_model: str = 'gpt-4.1-mini'
    whisper_model: str = 'small'
    language: Optional[str] = None
    device: str = 'cpu'
    compute_type: str = 'int8'
    prefer_subs: bool = True
    confirm_rights: bool = False
    keep_video: bool = True


@dataclass
class IngestResult:
    title: str
    slug: str
    source_url: str
    job_dir: Path
    assets_dir: Path
    note_path: Path
    summary_path: Path
    graph_json_path: Path
    graph_mermaid_path: Path
    transcript_path: Path
    segments_path: Path
    transcription_info_path: Path
    metadata_path: Path
    subtitle_path: Optional[Path]
    video_path: Path
    manifest_path: Path


TOTAL_STEPS = 5



def make_job_dir(workdir: Path, url: str) -> Path:
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    digest = sha1_text(url)[:10]
    return ensure_dir(workdir / f'{ts}-{digest}')



def _notify(callback: Optional[ProgressCallback], step: int, message: str) -> None:
    if callback:
        callback(step, TOTAL_STEPS, message)



def ingest_video(options: IngestOptions, progress_callback: Optional[ProgressCallback] = None) -> IngestResult:
    workdir = ensure_dir(Path(options.workdir).resolve())
    kb_root = ensure_dir(Path(options.kb_root).resolve())
    job_dir = make_job_dir(workdir, options.url)
    assets_dir = ensure_dir(job_dir / 'assets')

    _notify(progress_callback, 1, '下载视频')
    download: DownloadResult = download_video(
        url=options.url,
        work_dir=assets_dir,
        confirm_rights=options.confirm_rights,
    )

    title = options.title or str(download.metadata.get('title') or download.video_path.stem)
    slug = safe_slug(title, fallback=sha1_text(options.url)[:12])

    _notify(progress_callback, 2, '获取转写')
    transcript = ''
    subtitle_path = pick_best_subtitle(download.subtitle_paths) if options.prefer_subs else None
    if subtitle_path and subtitle_path.exists():
        transcript = save_subtitle_transcript(subtitle_path, job_dir)
    else:
        audio_path = extract_audio(download.video_path, assets_dir)
        transcript, _, _ = transcribe_audio(
            audio_path=audio_path,
            output_dir=job_dir,
            model_size=options.whisper_model,
            language=options.language,
            device=options.device,
            compute_type=options.compute_type,
        )

    if not transcript.strip():
        raise RuntimeError('未获取到有效转写，流程终止。')

    _notify(progress_callback, 3, '生成总结')
    summary = summarize_text(
        text=transcript,
        title=title,
        provider=options.summary_provider,
        openai_model=options.openai_model,
    )
    summary_path = job_dir / 'summary.json'
    write_json(summary_path, summary)

    _notify(progress_callback, 4, '生成知识图谱')
    graph_json, mermaid = build_graph(title=title, summary=summary)
    graph_json_path = job_dir / 'knowledge_graph.json'
    graph_mermaid_path = job_dir / 'knowledge_graph.mmd'
    write_json(graph_json_path, graph_json)
    write_text(graph_mermaid_path, mermaid)

    _notify(progress_callback, 5, '入库')
    transcript_path = job_dir / 'transcript.txt'
    segments_path = job_dir / 'segments.json'
    transcription_info_path = job_dir / 'transcription_info.json'
    work_files: List[Path] = [
        transcript_path,
        segments_path,
        transcription_info_path,
        summary_path,
        graph_json_path,
        graph_mermaid_path,
        download.metadata_path,
    ]
    if download.video_path.exists() and options.keep_video:
        work_files.append(download.video_path)
    if subtitle_path and subtitle_path.exists():
        work_files.append(subtitle_path)

    note_path = ingest_to_kb(
        kb_root=kb_root,
        slug=slug,
        title=title,
        source_url=options.url,
        metadata=download.metadata,
        summary=summary,
        work_files=work_files,
    )

    manifest = {
        'title': title,
        'slug': slug,
        'source_url': options.url,
        'job_dir': str(job_dir),
        'note_path': str(note_path),
        'created_at': datetime.now().isoformat(timespec='seconds'),
    }
    manifest_path = job_dir / 'manifest.json'
    write_json(manifest_path, manifest)

    return IngestResult(
        title=title,
        slug=slug,
        source_url=options.url,
        job_dir=job_dir,
        assets_dir=assets_dir,
        note_path=note_path,
        summary_path=summary_path,
        graph_json_path=graph_json_path,
        graph_mermaid_path=graph_mermaid_path,
        transcript_path=transcript_path,
        segments_path=segments_path,
        transcription_info_path=transcription_info_path,
        metadata_path=download.metadata_path,
        subtitle_path=subtitle_path,
        video_path=download.video_path,
        manifest_path=manifest_path,
    )
