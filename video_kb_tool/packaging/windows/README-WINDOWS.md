# Windows 发布说明

这套工程已经包含 Windows 桌面发布所需的关键骨架：

- `video_kb_tool.spec`: PyInstaller 打包配置
- `build_windows.bat`: 本地一键构建
- `build_desktop.py`: 通用打包入口
- `packaging/windows/installer.iss`: Inno Setup 安装脚本
- `.github/workflows/build-windows.yml`: GitHub Actions 自动构建
- `tools/ffmpeg/bin/`: 预留 ffmpeg 放置目录

## 产物形态

推荐提供两种分发形态：

1. 便携版目录：`dist/VideoKBDesktop/`
2. 安装版：基于 Inno Setup 生成 `.exe` 安装包

## 本地构建步骤

1. 在 Windows 10/11 安装 Python 3.11+
2. 解压工程
3. 将 ffmpeg 解压到 `tools/ffmpeg/bin/`，至少包含：
   - `ffmpeg.exe`
   - `ffprobe.exe`
4. 双击 `build_windows.bat`

构建成功后，便携版目录位于：

```text
dist\VideoKBDesktop\
```

## 生成安装包

1. 安装 Inno Setup 6
2. 打开 `packaging/windows/installer.iss`
3. 修改其中的 `MyAppVersion` 等参数
4. 编译脚本

## 无本机环境时的替代方案

如果本机没有 Python 环境，可以：

- 将本项目推到 GitHub
- 使用 `.github/workflows/build-windows.yml` 自动构建 Windows artifact
- 下载 artifact 后再使用 Inno Setup 进一步封装

## 首次运行目录

打包后的 exe 默认将数据写到：

```text
%LOCALAPPDATA%\VideoKBDesktop\
```

包括：

- `runs/`
- `knowledge_base/`
- `config/desktop_settings.json`
- `logs/`

## ffmpeg 放置约定

优先使用以下位置的 ffmpeg：

```text
VideoKBDesktop\tools\ffmpeg\bin\ffmpeg.exe
```

若不存在，则回退使用系统 PATH 中的 ffmpeg。
