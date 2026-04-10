# VideoKB Desktop - Windows 发布与构建指南

这份指南用于把当前工程产出为 Windows 可执行版，并给团队一个统一的发布目录规范。

## 1. 推荐发布策略

建议同时维护两种发布形态：

1. **Portable 便携版**
   - 目录：`dist/VideoKBDesktop/`
   - 适合内部测试、快速分发、U 盘拷贝
2. **Installer 安装版**
   - 通过 Inno Setup 生成安装程序
   - 适合正式发布

## 2. 最低要求

### 本地 Windows 构建

- Windows 10 或 Windows 11
- Python 3.11+
- PowerShell 5+
- 可选：Inno Setup 6（如果要出安装包）

### GitHub Actions 构建

- 一个 GitHub 仓库
- 仓库启用 Actions

## 3. 目录规范

### 仓库内关键目录

- `src/video_kb_tool/`：核心业务逻辑
- `tools/ffmpeg/bin/`：内置 ffmpeg 放置目录
- `packaging/windows/installer.iss`：安装包脚本
- `.github/workflows/build-windows.yml`：CI 构建脚本
- `video_kb_tool.spec`：PyInstaller 入口

### 程序运行时目录

打包后，程序默认把用户数据写到：

```text
%LOCALAPPDATA%\VideoKBDesktop\
```

建议目录结构：

```text
%LOCALAPPDATA%\VideoKBDesktop\
  config\
    desktop_settings.json
  knowledge_base\
  logs\
  runs\
```

## 4. ffmpeg 放置方式

优先把 ffmpeg 放到：

```text
tools\ffmpeg\bin\
```

至少包含：

- `ffmpeg.exe`
- `ffprobe.exe`

程序会按这个顺序查找：

1. 应用自带 `tools\ffmpeg\bin`
2. 系统 PATH

## 5. 本地构建步骤

### Step 1: 准备环境

在项目根目录执行：

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
pip install -r requirements-packaging.txt
```

### Step 2: 放入 ffmpeg

把 `ffmpeg.exe` 和 `ffprobe.exe` 放入：

```text
tools\ffmpeg\bin\
```

### Step 3: 生成便携版

执行：

```bat
build_windows.bat
```

成功后产物通常位于：

```text
dist\VideoKBDesktop\
```

## 6. GitHub Actions 自动构建

### 推荐做法

把工程推送到 GitHub 后，直接使用仓库内工作流：

```text
.github/workflows/build-windows.yml
```

### 建议的仓库操作流程

1. 新建仓库
2. 上传当前工程
3. 确保以下文件存在：
   - `video_kb_tool.spec`
   - `requirements-packaging.txt`
   - `.github/workflows/build-windows.yml`
4. 推送到 `main`
5. 在 GitHub Actions 页面查看构建
6. 下载 artifact

### 构建完成后建议检查

- 是否生成 `VideoKBDesktop.exe`
- `tools/ffmpeg/bin/` 是否被带入产物
- 首次启动是否能创建 `%LOCALAPPDATA%\VideoKBDesktop\`
- 环境自检是否通过

## 7. 生成安装包

如果需要正式交付给非技术用户，建议再封装安装包。

### Step 1: 安装 Inno Setup

安装 Inno Setup 6。

### Step 2: 打开脚本

脚本位置：

```text
packaging\windows\installer.iss
```

### Step 3: 修改发布信息

至少检查这些参数：

- `MyAppName`
- `MyAppVersion`
- `MyAppPublisher`
- `MyAppExeName`

### Step 4: 编译安装包

在 Inno Setup 中编译后，会生成 Windows 安装程序。

## 8. 建议的发布产物规范

建议统一以下命名：

### Portable

```text
VideoKBDesktop-portable-v0.1.0-win64.zip
```

### Installer

```text
VideoKBDesktop-setup-v0.1.0-win64.exe
```

### Source

```text
video_kb_tool_windows_release_v0.1.0.zip
```

## 9. 建议的版本节奏

- `0.1.x`：内部验证
- `0.2.x`：小范围试用
- `1.0.0`：正式版

## 10. 首次启动验收清单

建议按下面顺序验收：

1. 双击 exe 能否启动
2. 环境自检是否正常
3. ffmpeg 是否识别成功
4. 选择一个明确有权下载的公开视频测试
5. 是否成功生成：
   - `note.md`
   - `summary.json`
   - `knowledge_graph.json`
   - `knowledge_graph.mmd`
   - `transcript.txt`
6. 知识库目录是否写入成功
7. 设置是否在重启后保留

## 11. 如果你本机没有环境，最省事的路径

如果你现在的机器没有 Python、没有 ffmpeg，也不想本地折腾，最实际的方法是：

1. 把这个工程推到 GitHub
2. 用 GitHub Actions 构建 Windows artifact
3. 下载产物到 Windows 机器
4. 再决定是否用 Inno Setup 生成安装包

## 12. 下一步建议

如果继续推进，建议优先做这三项：

1. 应用图标、版本信息、签名信息
2. 自动更新机制
3. 适配目标知识库（如 Obsidian / Neo4j / Notion / 飞书）
