from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from video_kb_tool.env_check import collect_env_status, format_env_status
from video_kb_tool.pipeline import IngestOptions, IngestResult, ingest_video
from video_kb_tool.runtime import extend_process_path, resolve_paths
from video_kb_tool.settings import DesktopSettings, load_settings, save_settings


class DesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title('Video KB Desktop')
        self.root.geometry('1220x860')
        self.root.minsize(1080, 760)

        self.paths = resolve_paths()
        extend_process_path(self.paths)
        self.queue: queue.Queue = queue.Queue()
        self.worker: threading.Thread | None = None
        self.last_result: IngestResult | None = None
        self.settings = load_settings()

        self._build_vars()
        self._build_ui()
        self.root.after(150, self._poll_queue)
        self.run_env_check(log_to_output=False)

    def _build_vars(self) -> None:
        default_workdir = self.settings.workdir or str(self.paths.runs_dir.resolve())
        default_kbroot = self.settings.kb_root or str(self.paths.knowledge_base_dir.resolve())
        self.url_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.workdir_var = tk.StringVar(value=default_workdir)
        self.kbroot_var = tk.StringVar(value=default_kbroot)
        self.summary_provider_var = tk.StringVar(value=self.settings.summary_provider)
        self.openai_model_var = tk.StringVar(value=self.settings.openai_model)
        self.whisper_model_var = tk.StringVar(value=self.settings.whisper_model)
        self.language_var = tk.StringVar(value=self.settings.language)
        self.device_var = tk.StringVar(value=self.settings.device)
        self.compute_type_var = tk.StringVar(value=self.settings.compute_type)
        self.prefer_subs_var = tk.BooleanVar(value=self.settings.prefer_subs)
        self.confirm_rights_var = tk.BooleanVar(value=False)
        self.keep_video_var = tk.BooleanVar(value=self.settings.keep_video)
        self.status_var = tk.StringVar(value='就绪')
        self.progress_var = tk.DoubleVar(value=0.0)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        form = ttk.LabelFrame(outer, text='任务参数', padding=10)
        form.grid(row=0, column=0, sticky='nsew')
        for i in range(8):
            form.columnconfigure(i, weight=1)

        ttk.Label(form, text='视频 URL').grid(row=0, column=0, sticky='w', pady=4)
        ttk.Entry(form, textvariable=self.url_var).grid(row=0, column=1, columnspan=7, sticky='ew', pady=4)

        ttk.Label(form, text='自定义标题').grid(row=1, column=0, sticky='w', pady=4)
        ttk.Entry(form, textvariable=self.title_var).grid(row=1, column=1, columnspan=3, sticky='ew', pady=4)
        ttk.Label(form, text='总结方式').grid(row=1, column=4, sticky='w', pady=4)
        ttk.Combobox(form, textvariable=self.summary_provider_var, values=['extractive', 'openai'], state='readonly').grid(row=1, column=5, sticky='ew', pady=4)
        ttk.Label(form, text='OpenAI 模型').grid(row=1, column=6, sticky='w', pady=4)
        ttk.Entry(form, textvariable=self.openai_model_var).grid(row=1, column=7, sticky='ew', pady=4)

        ttk.Label(form, text='工作目录').grid(row=2, column=0, sticky='w', pady=4)
        ttk.Entry(form, textvariable=self.workdir_var).grid(row=2, column=1, columnspan=6, sticky='ew', pady=4)
        ttk.Button(form, text='选择', command=lambda: self._choose_dir(self.workdir_var)).grid(row=2, column=7, sticky='ew', pady=4)

        ttk.Label(form, text='知识库目录').grid(row=3, column=0, sticky='w', pady=4)
        ttk.Entry(form, textvariable=self.kbroot_var).grid(row=3, column=1, columnspan=6, sticky='ew', pady=4)
        ttk.Button(form, text='选择', command=lambda: self._choose_dir(self.kbroot_var)).grid(row=3, column=7, sticky='ew', pady=4)

        ttk.Label(form, text='Whisper 模型').grid(row=4, column=0, sticky='w', pady=4)
        ttk.Combobox(form, textvariable=self.whisper_model_var, values=['tiny', 'base', 'small', 'medium', 'large-v3'], state='readonly').grid(row=4, column=1, sticky='ew', pady=4)
        ttk.Label(form, text='语言').grid(row=4, column=2, sticky='w', pady=4)
        ttk.Entry(form, textvariable=self.language_var).grid(row=4, column=3, sticky='ew', pady=4)
        ttk.Label(form, text='设备').grid(row=4, column=4, sticky='w', pady=4)
        ttk.Combobox(form, textvariable=self.device_var, values=['cpu', 'cuda'], state='readonly').grid(row=4, column=5, sticky='ew', pady=4)
        ttk.Label(form, text='计算精度').grid(row=4, column=6, sticky='w', pady=4)
        ttk.Combobox(form, textvariable=self.compute_type_var, values=['int8', 'float16', 'float32'], state='readonly').grid(row=4, column=7, sticky='ew', pady=4)

        ttk.Checkbutton(form, text='优先使用字幕', variable=self.prefer_subs_var).grid(row=5, column=0, columnspan=2, sticky='w', pady=4)
        ttk.Checkbutton(form, text='保留原始视频', variable=self.keep_video_var).grid(row=5, column=2, columnspan=2, sticky='w', pady=4)
        ttk.Checkbutton(form, text='我确认拥有下载/归档权限', variable=self.confirm_rights_var).grid(row=5, column=4, columnspan=4, sticky='w', pady=4)

        controls = ttk.Frame(form)
        controls.grid(row=6, column=0, columnspan=8, sticky='ew', pady=(8, 0))
        controls.columnconfigure(7, weight=1)
        ttk.Button(controls, text='环境自检', command=lambda: self.run_env_check(log_to_output=True)).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(controls, text='保存配置', command=self._save_current_settings).grid(row=0, column=1, padx=8)
        ttk.Button(controls, text='开始处理', command=self.start_run).grid(row=0, column=2, padx=8)
        ttk.Button(controls, text='打开知识库目录', command=lambda: self._open_path(self.kbroot_var.get())).grid(row=0, column=3, padx=8)
        ttk.Button(controls, text='打开工作目录', command=lambda: self._open_path(self.workdir_var.get())).grid(row=0, column=4, padx=8)
        ttk.Button(controls, text='打开最后笔记', command=self._open_last_note).grid(row=0, column=5, padx=8)
        ttk.Button(controls, text='清空日志', command=self._clear_log).grid(row=0, column=6, padx=8)
        ttk.Label(controls, textvariable=self.status_var).grid(row=0, column=7, sticky='e')

        progress = ttk.Progressbar(form, maximum=100, variable=self.progress_var)
        progress.grid(row=7, column=0, columnspan=8, sticky='ew', pady=(10, 0))

        paned = ttk.Panedwindow(outer, orient=tk.VERTICAL)
        paned.grid(row=1, column=0, sticky='nsew', pady=(10, 0))

        top_frame = ttk.LabelFrame(paned, text='执行日志', padding=8)
        self.log_text = ScrolledText(top_frame, wrap=tk.WORD, height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        paned.add(top_frame, weight=1)

        bottom = ttk.LabelFrame(paned, text='结果预览', padding=8)
        bottom.columnconfigure(0, weight=1)
        bottom.rowconfigure(0, weight=1)
        self.tabs = ttk.Notebook(bottom)
        self.tabs.grid(row=0, column=0, sticky='nsew')
        paned.add(bottom, weight=2)

        self.summary_text = self._make_tab('总结')
        self.transcript_text = self._make_tab('转写')
        self.note_text = self._make_tab('Markdown')
        self.graph_text = self._make_tab('图谱')
        self.meta_text = self._make_tab('环境/元数据')

        self._append_log('桌面版已就绪。请填写 URL 并勾选权限确认。')
        self._append_log(f'应用数据目录: {self.paths.user_data_dir}')
        self._append_log('推荐先点一次“环境自检”，确认 ffmpeg 和依赖已就绪。')
        self._append_log('如已打包为 exe，可把 ffmpeg 解压到 tools/ffmpeg/bin/ 目录下。')
        self._append_log('OpenAI 总结前，请先在系统环境变量中设置 OPENAI_API_KEY。')

    def _snapshot_settings(self) -> DesktopSettings:
        return DesktopSettings(
            workdir=self.workdir_var.get().strip(),
            kb_root=self.kbroot_var.get().strip(),
            summary_provider=self.summary_provider_var.get().strip(),
            openai_model=self.openai_model_var.get().strip() or 'gpt-4.1-mini',
            whisper_model=self.whisper_model_var.get().strip() or 'small',
            language=self.language_var.get().strip() or 'zh',
            device=self.device_var.get().strip() or 'cpu',
            compute_type=self.compute_type_var.get().strip() or 'int8',
            prefer_subs=self.prefer_subs_var.get(),
            keep_video=self.keep_video_var.get(),
        )

    def _save_current_settings(self) -> None:
        path = save_settings(self._snapshot_settings())
        self._append_log(f'配置已保存: {path}')
        self.status_var.set('配置已保存')

    def _make_tab(self, title: str) -> ScrolledText:
        frame = ttk.Frame(self.tabs)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text = ScrolledText(frame, wrap=tk.WORD)
        text.grid(row=0, column=0, sticky='nsew')
        self.tabs.add(frame, text=title)
        return text

    def _choose_dir(self, var: tk.StringVar) -> None:
        selected = filedialog.askdirectory(initialdir=var.get() or str(self.paths.user_data_dir))
        if selected:
            var.set(selected)

    def _open_path(self, path: str | os.PathLike[str]) -> None:
        target = Path(path)
        if not target.exists():
            messagebox.showwarning('路径不存在', f'未找到路径: {target}')
            return
        try:
            if sys.platform.startswith('win'):
                os.startfile(str(target))
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(target)])
            else:
                subprocess.Popen(['xdg-open', str(target)])
        except Exception as exc:
            messagebox.showerror('打开失败', str(exc))

    def _open_last_note(self) -> None:
        if not self.last_result:
            messagebox.showinfo('暂无结果', '请先执行一次处理。')
            return
        self._open_path(self.last_result.note_path)

    def _clear_log(self) -> None:
        self.log_text.delete('1.0', tk.END)

    def _append_log(self, message: str) -> None:
        self.log_text.insert(tk.END, message.rstrip() + '\n')
        self.log_text.see(tk.END)

    def _set_text(self, widget: ScrolledText, content: str) -> None:
        widget.delete('1.0', tk.END)
        widget.insert('1.0', content)

    def run_env_check(self, log_to_output: bool = True) -> None:
        status = collect_env_status()
        content = format_env_status(status)
        if log_to_output:
            self._append_log(content)
            self._set_text(self.meta_text, json.dumps(status, ensure_ascii=False, indent=2))
            self.tabs.select(self.tabs.tabs()[-1])
        ffmpeg_ok = status['ffmpeg']['status'] == 'ok'
        required_ok = all(item['status'] == 'ok' for item in status['modules'] if item['required'] == 'yes')
        self.status_var.set('环境就绪' if ffmpeg_ok and required_ok else '缺少依赖')

    def start_run(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo('处理中', '当前已有任务在运行。')
            return
        if not self.url_var.get().strip():
            messagebox.showwarning('参数不完整', '请先填写视频 URL。')
            return
        if not self.confirm_rights_var.get():
            messagebox.showwarning('需要确认', '请勾选“我确认拥有下载/归档权限”。')
            return

        save_settings(self._snapshot_settings())
        self.progress_var.set(0)
        self.status_var.set('准备开始')
        self._append_log('-' * 70)
        self._append_log(f'URL: {self.url_var.get().strip()}')
        self._append_log(f'工作目录: {self.workdir_var.get().strip()}')
        self._append_log(f'知识库目录: {self.kbroot_var.get().strip()}')

        self.worker = threading.Thread(target=self._run_worker, daemon=True)
        self.worker.start()

    def _run_worker(self) -> None:
        try:
            options = IngestOptions(
                url=self.url_var.get().strip(),
                workdir=Path(self.workdir_var.get().strip()),
                kb_root=Path(self.kbroot_var.get().strip()),
                title=self.title_var.get().strip() or None,
                summary_provider=self.summary_provider_var.get().strip(),
                openai_model=self.openai_model_var.get().strip() or 'gpt-4.1-mini',
                whisper_model=self.whisper_model_var.get().strip() or 'small',
                language=self.language_var.get().strip() or None,
                device=self.device_var.get().strip() or 'cpu',
                compute_type=self.compute_type_var.get().strip() or 'int8',
                prefer_subs=self.prefer_subs_var.get(),
                confirm_rights=self.confirm_rights_var.get(),
                keep_video=self.keep_video_var.get(),
            )

            def progress(step: int, total: int, message: str) -> None:
                self.queue.put(('progress', step, total, message))

            result = ingest_video(options, progress_callback=progress)
            self.queue.put(('done', result))
        except Exception as exc:
            self.queue.put(('error', str(exc), traceback.format_exc()))

    def _poll_queue(self) -> None:
        try:
            while True:
                item = self.queue.get_nowait()
                kind = item[0]
                if kind == 'progress':
                    _, step, total, message = item
                    percent = max(0, min(100, int(step * 100 / total)))
                    self.progress_var.set(percent)
                    self.status_var.set(f'{step}/{total} {message}')
                    self._append_log(f'[{step}/{total}] {message}')
                elif kind == 'done':
                    _, result = item
                    self._handle_done(result)
                elif kind == 'error':
                    _, message, detail = item
                    self._handle_error(message, detail)
        except queue.Empty:
            pass
        finally:
            self.root.after(150, self._poll_queue)

    def _handle_done(self, result: IngestResult) -> None:
        self.last_result = result
        self.progress_var.set(100)
        self.status_var.set('完成')
        self._append_log(f'处理完成: {result.title}')
        self._append_log(f'笔记输出: {result.note_path}')

        summary_text = self._safe_read_json(result.summary_path)
        transcript_text = self._safe_read_text(result.transcript_path)
        note_text = self._safe_read_text(result.note_path)
        graph_text = self._safe_read_text(result.graph_mermaid_path)
        meta_payload = {
            'title': result.title,
            'job_dir': str(result.job_dir),
            'assets_dir': str(result.assets_dir),
            'video_path': str(result.video_path),
            'subtitle_path': str(result.subtitle_path) if result.subtitle_path else None,
            'summary_path': str(result.summary_path),
            'graph_json_path': str(result.graph_json_path),
            'graph_mermaid_path': str(result.graph_mermaid_path),
            'note_path': str(result.note_path),
            'manifest_path': str(result.manifest_path),
        }
        self._set_text(self.summary_text, summary_text)
        self._set_text(self.transcript_text, transcript_text)
        self._set_text(self.note_text, note_text)
        self._set_text(self.graph_text, graph_text)
        self._set_text(self.meta_text, json.dumps(meta_payload, ensure_ascii=False, indent=2))
        self.tabs.select(0)
        messagebox.showinfo('处理完成', f'已完成: {result.title}')

    def _handle_error(self, message: str, detail: str) -> None:
        self.status_var.set('失败')
        self.progress_var.set(0)
        self._append_log('处理失败: ' + message)
        self._append_log(detail)
        messagebox.showerror('处理失败', message)

    def _safe_read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding='utf-8', errors='ignore')
        except Exception as exc:
            return f'读取失败: {exc}'

    def _safe_read_json(self, path: Path) -> str:
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
            return json.dumps(payload, ensure_ascii=False, indent=2)
        except Exception as exc:
            return f'读取 JSON 失败: {exc}'



def main() -> int:
    root = tk.Tk()
    try:
        ttk.Style().theme_use('clam')
    except Exception:
        pass
    DesktopApp(root)
    root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
