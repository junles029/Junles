# video-kb-tool

一个面向**已获授权内容**的 Python 工具：

1. 下载指定视频链接的**最高可用画质**到本地
2. 优先复用字幕，否则自动转写
3. 对视频内容做总结提炼
4. 生成 Markdown 笔记与 Mermaid/JSON 图谱
5. 放入本地知识库目录（默认是文件系统知识库，兼容 Obsidian 风格）

## 合规边界

本工具仅适用于以下场景：

- 你拥有该视频的下载/归档权利
- 平台条款明确允许下载、备份或离线保存
- 内容是你自己上传、自己持有、或已获书面授权的材料

**不适用于**：

- DRM/加密流媒体绕过
- 付费内容、会员专享内容的破解下载
- 登录态抓包、签名伪造、反爬绕过
- 任何违反网站服务条款或版权规则的用途

运行时需要显式传入 `--confirm-rights` 才会继续。

## 目录结构

```text
video_kb_tool/
  README.md
  requirements.txt
  src/video_kb_tool/
    __init__.py
    cli.py
    downloader.py
    media.py
    transcriber.py
    summarizer.py
    graph_builder.py
    kb_store.py
    utils.py
```

## 环境准备

### 1) Python

建议 Python 3.10+

### 2) ffmpeg

必须安装 `ffmpeg` 并确保命令行可用。

macOS:

```bash
brew install ffmpeg
```

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

Windows:

- 使用 `winget install Gyan.FFmpeg`
- 或手动安装并加入 PATH

### 3) 安装依赖

```bash
cd video_kb_tool
python -m venv .venv
source .venv/bin/activate   # Windows 用 .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

### 4) 可选：启用更强总结能力

如需用 OpenAI 做高质量总结：

```bash
export OPENAI_API_KEY="你的 key"
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="你的 key"
```

## 使用方式

### 基础用法

```bash
PYTHONPATH=src python -m video_kb_tool.cli ingest \
  --url "https://example.com/video/123" \
  --workdir ./runs \
  --kb-root ./knowledge_base \
  --summary-provider extractive \
  --confirm-rights
```

### 使用 OpenAI 总结

```bash
PYTHONPATH=src python -m video_kb_tool.cli ingest \
  --url "https://example.com/video/123" \
  --workdir ./runs \
  --kb-root ./knowledge_base \
  --summary-provider openai \
  --openai-model gpt-4.1-mini \
  --confirm-rights
```

### 指定语言和 Whisper 模型

```bash
PYTHONPATH=src python -m video_kb_tool.cli ingest \
  --url "https://example.com/video/123" \
  --workdir ./runs \
  --kb-root ./knowledge_base \
  --language zh \
  --whisper-model medium \
  --device cpu \
  --confirm-rights
```




## 桌面版使用

如果你更希望直接使用桌面 GUI，而不是浏览器界面或命令行，可以运行 Tkinter 桌面版：

```bash
cd video_kb_tool
python -m venv .venv
source .venv/bin/activate   # Windows 用 .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt

python run_desktop.py
```

桌面版支持：

- 填写视频 URL 并选择工作目录/知识库目录
- 一键执行完整流水线
- 实时查看日志与处理进度
- 预览 summary / transcript / Markdown / Mermaid 图谱
- 直接打开知识库目录、工作目录、最后生成的笔记


### 一键启动桌面版

如果你本机还没准备虚拟环境，但已经装了 Python，可以直接：

- Windows: 双击 `launch_desktop.bat`
- macOS / Linux: 执行 `./launch_desktop.sh`

它会自动：

1. 创建 `.venv`
2. 安装依赖
3. 启动桌面 GUI

第一次启动会比较慢，因为需要下载 Python 依赖；之后再次启动会快很多。

### 打包为独立桌面应用

如果你要给没有 Python 环境的机器使用，建议在**目标操作系统上**打包：

- Windows: 双击 `build_windows.bat`
- 通用命令: `python build_desktop.py`

> 说明：PyInstaller 需要在目标系统上打包目标系统的可执行文件。例如 Windows 的 `.exe` 需要在 Windows 上构建。

## 图形界面校验

如果你希望先用界面做人工校验，而不是直接走命令行，可以使用 Streamlit：

```bash
cd video_kb_tool
python -m venv .venv
source .venv/bin/activate   # Windows 用 .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt

streamlit run app_streamlit.py
```

启动后浏览器会打开本地地址，通常是：

```text
http://localhost:8501
```

界面里可以：

- 输入视频 URL
- 勾选下载权限确认
- 选择总结方式、Whisper 模型、语言和设备
- 一键执行完整流水线
- 在线查看 summary、transcript、Markdown 笔记和 Mermaid 图谱

## 输出结果

执行成功后会产生两类目录：

### 1) 工作目录 `runs/...`

保存中间产物：

- `transcript.txt`
- `segments.json`
- `transcription_info.json`
- `summary.json`
- `knowledge_graph.json`
- `knowledge_graph.mmd`
- `manifest.json`
- `assets/` 下的原视频、字幕、元数据

### 2) 知识库目录 `knowledge_base/...`

最终知识库条目位于：

```text
knowledge_base/
  index.jsonl
  videos/
    YYYY-MM/
      your-video-slug/
        note.md
        transcript.txt
        summary.json
        knowledge_graph.json
        knowledge_graph.mmd
        video_metadata.json
        原始视频文件
        字幕文件(如有)
```

其中 `note.md` 是可直接纳入 Obsidian / Markdown 知识库的笔记文件。

## 设计说明

### 下载策略

- 通过 `yt-dlp` 选择 `bv*+ba/b`
- 优先获取最佳视频流 + 最佳音频流并合并为 MP4
- 优先尝试下载字幕/自动字幕

### 转写策略

- 若检测到字幕，优先用字幕生成转写
- 否则提取音频并用 `faster-whisper` 做本地转写

### 总结策略

- `extractive`: 本地抽取式总结，无需云 API
- `openai`: 调用 OpenAI 生成结构化 JSON 总结；失败时自动回退到抽取式总结

### 图谱策略

当前版本生成：

- `knowledge_graph.json`
- `knowledge_graph.mmd`

Mermaid 可在多数 Markdown 知识库中直接渲染。

## 后续你可能会想加的能力

- 接入 Neo4j / ArangoDB / NebulaGraph
- 接入向量库（FAISS / Chroma / Milvus）
- 做定时采集与批量入库
- 为字幕与章节加时间戳回链
- 自动生成标签体系与专题索引页
- Web UI / FastAPI 服务化

## 注意事项

1. 某些视频网站没有可用字幕，转写耗时会明显增加。
2. `faster-whisper` 在 CPU 下可运行，但速度取决于机器性能。
3. 某些站点即便 `yt-dlp` 技术上支持，也不代表你有法律或条款层面的下载权限。
4. 如果要处理大批量视频，建议把原视频存储和知识库存储拆开。


## Windows 免环境发布工程

本项目已经补齐 Windows 发布工程骨架，适合做成无需预装 Python 的桌面软件。

关键文件：

- `video_kb_tool.spec`：PyInstaller 打包配置
- `requirements-packaging.txt`：打包依赖
- `build_windows.bat`：Windows 一键构建
- `packaging/windows/README-WINDOWS.md`：Windows 构建说明
- `packaging/windows/installer.iss`：Inno Setup 安装脚本
- `.github/workflows/build-windows.yml`：GitHub Actions 自动构建

### Windows 本地构建

```bat
build_windows.bat
```

### GitHub Actions 自动构建

将代码推到 GitHub 后，可直接触发 `build-windows` 工作流构建 Windows artifact。

### 应用数据目录

打包后，默认将数据写入：

```text
%LOCALAPPDATA%\VideoKBDesktop\
```

其中包含：

- `runs/`
- `knowledge_base/`
- `config/desktop_settings.json`
- `logs/`

### 打包版 ffmpeg

如果你不想依赖系统环境变量，可将 ffmpeg 放到：

```text
tools\ffmpeg\bin\ffmpeg.exe
```

桌面版会优先使用这个位置的 ffmpeg。
