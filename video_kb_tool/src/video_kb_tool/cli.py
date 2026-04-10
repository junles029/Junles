from __future__ import annotations

import argparse
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
except Exception:  # pragma: no cover
    Console = None
    Table = None

from .pipeline import IngestOptions, ingest_video


console = Console() if Console else None



def cprint(message: str) -> None:
    if console:
        console.print(message)
    else:
        print(message)



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='video-kb',
        description='下载授权视频、生成总结与图谱，并入本地知识库。',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    ingest = sub.add_parser('ingest', help='执行完整流水线')
    ingest.add_argument('--url', required=True, help='视频地址')
    ingest.add_argument('--workdir', default='./runs', help='中间产物目录')
    ingest.add_argument('--kb-root', default='./knowledge_base', help='知识库根目录')
    ingest.add_argument('--title', default=None, help='手动覆盖标题')
    ingest.add_argument('--summary-provider', choices=['extractive', 'openai'], default='extractive')
    ingest.add_argument('--openai-model', default='gpt-4.1-mini')
    ingest.add_argument('--whisper-model', default='small')
    ingest.add_argument('--language', default=None, help='如 zh / en，默认自动检测')
    ingest.add_argument('--device', default='cpu', choices=['cpu', 'cuda'])
    ingest.add_argument('--compute-type', default='int8')
    ingest.add_argument('--prefer-subs', action='store_true', default=True, help='优先使用字幕文件')
    ingest.add_argument('--no-prefer-subs', action='store_false', dest='prefer_subs')
    ingest.add_argument('--confirm-rights', action='store_true', help='确认你有权下载该视频或平台允许下载')
    ingest.add_argument('--keep-video', action='store_true', help='默认保留视频文件到工作目录；此参数仅用于语义明确')

    return parser



def _display_summary(title: str, note_path: Path, summary_path: Path, graph_path: Path) -> None:
    if Table and console:
        table = Table(title='处理完成')
        table.add_column('项目')
        table.add_column('输出')
        table.add_row('标题', title)
        table.add_row('笔记', str(note_path))
        table.add_row('总结 JSON', str(summary_path))
        table.add_row('图谱 Mermaid', str(graph_path))
        console.print(table)
        return
    print('处理完成')
    print(f'标题: {title}')
    print(f'笔记: {note_path}')
    print(f'总结 JSON: {summary_path}')
    print(f'图谱 Mermaid: {graph_path}')



def run_ingest(args: argparse.Namespace) -> int:
    def progress(step: int, total: int, message: str) -> None:
        label = f'{step}/{total} {message}'
        cprint(f'[cyan]{label}[/cyan]' if console else label)

    result = ingest_video(
        IngestOptions(
            url=args.url,
            workdir=Path(args.workdir),
            kb_root=Path(args.kb_root),
            title=args.title,
            summary_provider=args.summary_provider,
            openai_model=args.openai_model,
            whisper_model=args.whisper_model,
            language=args.language,
            device=args.device,
            compute_type=args.compute_type,
            prefer_subs=args.prefer_subs,
            confirm_rights=args.confirm_rights,
            keep_video=True,
        ),
        progress_callback=progress,
    )
    _display_summary(
        title=result.title,
        note_path=result.note_path,
        summary_path=result.summary_path,
        graph_path=result.graph_mermaid_path,
    )
    return 0



def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == 'ingest':
        return run_ingest(args)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
