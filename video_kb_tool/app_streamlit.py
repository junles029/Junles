from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from video_kb_tool.cli import run_ingest  # noqa: E402
from video_kb_tool.utils import ensure_dir  # noqa: E402


st.set_page_config(page_title='Video KB Tool', page_icon='🎬', layout='wide')


def _build_args(
    url: str,
    workdir: str,
    kb_root: str,
    title: str,
    summary_provider: str,
    openai_model: str,
    whisper_model: str,
    language: str,
    device: str,
    compute_type: str,
    prefer_subs: bool,
    confirm_rights: bool,
):
    return argparse.Namespace(
        command='ingest',
        url=url,
        workdir=workdir,
        kb_root=kb_root,
        title=title or None,
        summary_provider=summary_provider,
        openai_model=openai_model,
        whisper_model=whisper_model,
        language=language or None,
        device=device,
        compute_type=compute_type,
        prefer_subs=prefer_subs,
        confirm_rights=confirm_rights,
        keep_video=True,
    )


@st.cache_data(show_spinner=False)
def _read_text(path: str) -> str:
    return Path(path).read_text(encoding='utf-8', errors='ignore')


def _read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def _latest_manifest(workdir: Path) -> Path | None:
    manifests = sorted(workdir.glob('*/*manifest.json'))
    return manifests[-1] if manifests else None


def _render_result_from_manifest(manifest_path: Path):
    manifest = _read_json(manifest_path)
    if not manifest:
        st.warning('未找到 manifest.json，无法展示结果。')
        return

    job_dir = Path(manifest['job_dir'])
    note_path = Path(manifest['note_path'])
    summary_path = job_dir / 'summary.json'
    graph_json_path = job_dir / 'knowledge_graph.json'
    graph_mermaid_path = job_dir / 'knowledge_graph.mmd'
    transcript_path = job_dir / 'transcript.txt'

    summary = _read_json(summary_path) or {}
    graph = _read_json(graph_json_path) or {}

    st.success('处理完成')
    col1, col2, col3 = st.columns(3)
    col1.metric('标题', manifest.get('title', ''))
    col2.metric('任务目录', job_dir.name)
    col3.metric('创建时间', manifest.get('created_at', ''))

    st.markdown('### 输出位置')
    st.code(
        '\n'.join([
            f"job_dir: {job_dir}",
            f"note.md: {note_path}",
            f"summary.json: {summary_path}",
            f"knowledge_graph.mmd: {graph_mermaid_path}",
        ]),
        language='text',
    )

    tabs = st.tabs(['概览', '关键要点', '行动项', '章节', '转写预览', '图谱', 'Markdown'])

    with tabs[0]:
        st.write(summary.get('executive_summary') or '暂无')
        tags = summary.get('tags') or []
        if tags:
            st.caption('标签: ' + ' / '.join(map(str, tags)))

    with tabs[1]:
        key_points = summary.get('key_points') or []
        if key_points:
            for idx, item in enumerate(key_points, start=1):
                st.markdown(f'{idx}. {item}')
        else:
            st.info('暂无关键要点')

    with tabs[2]:
        actions = summary.get('action_items') or []
        if actions:
            for idx, item in enumerate(actions, start=1):
                st.markdown(f'{idx}. {item}')
        else:
            st.info('暂无行动项')

    with tabs[3]:
        chapters = summary.get('chapters') or []
        if chapters:
            for chapter in chapters:
                st.markdown(f"#### {chapter.get('heading', '未命名章节')}")
                st.write(chapter.get('summary', ''))
        else:
            st.info('暂无章节信息')

    with tabs[4]:
        if transcript_path.exists():
            transcript = _read_text(str(transcript_path))
            st.text_area('transcript.txt', transcript[:20000], height=420)
        else:
            st.warning('未找到 transcript.txt')

    with tabs[5]:
        nodes = graph.get('nodes') or []
        edges = graph.get('edges') or []
        st.write(f'节点数: {len(nodes)} | 边数: {len(edges)}')
        if graph_mermaid_path.exists():
            st.text_area('Mermaid', _read_text(str(graph_mermaid_path)), height=300)
        if graph_json_path.exists():
            st.json(graph)

    with tabs[6]:
        if note_path.exists():
            st.text_area('note.md', _read_text(str(note_path)), height=420)
        else:
            st.warning('未找到 note.md')


st.title('🎬 Video KB Tool 校验界面')
st.caption('用于处理你有权下载、归档或平台允许离线保存的视频内容。')

with st.sidebar:
    st.markdown('### 运行参数')
    workdir = st.text_input('工作目录', value=str(PROJECT_ROOT / 'runs'))
    kb_root = st.text_input('知识库目录', value=str(PROJECT_ROOT / 'knowledge_base'))
    summary_provider = st.selectbox('总结方式', ['extractive', 'openai'], index=0)
    openai_model = st.text_input('OpenAI 模型', value='gpt-4.1-mini')
    whisper_model = st.selectbox('Whisper 模型', ['tiny', 'base', 'small', 'medium', 'large-v3'], index=2)
    language = st.text_input('语言', value='zh')
    device = st.selectbox('设备', ['cpu', 'cuda'], index=0)
    compute_type = st.selectbox('计算精度', ['int8', 'float16', 'float32'], index=0)
    prefer_subs = st.checkbox('优先使用字幕', value=True)
    confirm_rights = st.checkbox('我确认拥有下载/归档权限', value=False)

url = st.text_input('视频链接', placeholder='https://example.com/watch?v=...')
title = st.text_input('手动覆盖标题（可选）', value='')

c1, c2 = st.columns([1, 1])
run_clicked = c1.button('开始处理', type='primary', use_container_width=True)
show_latest = c2.button('查看最近一次结果', use_container_width=True)

if run_clicked:
    if not url.strip():
        st.error('请先输入视频链接。')
        st.stop()
    if not confirm_rights:
        st.error('请先确认你有权下载或平台允许下载/归档。')
        st.stop()

    ensure_dir(Path(workdir))
    ensure_dir(Path(kb_root))

    if summary_provider == 'openai' and not os.getenv('OPENAI_API_KEY'):
        st.warning('你选择了 openai 总结，但当前环境未检测到 OPENAI_API_KEY；失败时会自动回退到 extractive。')

    args = _build_args(
        url=url.strip(),
        workdir=workdir,
        kb_root=kb_root,
        title=title.strip(),
        summary_provider=summary_provider,
        openai_model=openai_model.strip(),
        whisper_model=whisper_model,
        language=language.strip(),
        device=device,
        compute_type=compute_type,
        prefer_subs=prefer_subs,
        confirm_rights=confirm_rights,
    )

    with st.spinner('正在执行下载、转写、总结和入库...'):
        code = run_ingest(args)

    if code != 0:
        st.error(f'处理失败，返回码: {code}')
    else:
        manifest_path = _latest_manifest(Path(workdir))
        if manifest_path:
            _render_result_from_manifest(manifest_path)
        else:
            st.warning('流程已完成，但未找到最新 manifest。')

if show_latest:
    manifest_path = _latest_manifest(Path(workdir))
    if manifest_path:
        _render_result_from_manifest(manifest_path)
    else:
        st.info('当前工作目录下还没有结果。先跑一次再看。')
