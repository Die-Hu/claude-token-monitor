# Claude Token Monitor

Cross-platform system tray app for monitoring Claude token usage in real-time.

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)
![macOS](https://img.shields.io/badge/macOS-supported-brightgreen)
![Windows](https://img.shields.io/badge/Windows-supported-brightgreen)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)

## Features

- Real-time usage monitoring via claude.ai API (session 5h, weekly all models, weekly Sonnet)
- Color-coded progress bars (green / yellow / red)
- Live countdown timer for session reset
- Local Claude Code stats (tokens, cache, sessions)
- Subscription & tier display
- System tray icon with dynamic color based on usage level
- Bilingual UI (English / Chinese), auto-detected from system locale
- Cross-platform: macOS and Windows

## Requirements

- Python 3.10+
- Google Chrome with an active claude.ai login session
- Claude Code CLI installed (for subscription info)

## Quick Start

### macOS / Linux

```bash
git clone https://github.com/your-repo/claude-token-monitor.git
cd claude-token-monitor
./scripts/start.sh
```

### Windows

```cmd
git clone https://github.com/your-repo/claude-token-monitor.git
cd claude-token-monitor
scripts\start.bat
```

### Manual Install

```bash
cd claude-token-monitor
pip install -r requirements.txt
cd src
python -m claude_token_monitor
```

## Configuration

| Env Variable | Description | Default |
|---|---|---|
| `CTM_LANG` | UI language (`en` or `zh`) | Auto-detect from system locale |

## Building Standalone App

### macOS

```bash
pip install pyinstaller
pyinstaller build/build_macos.spec
# Output: dist/Claude Token Monitor.app
```

### Windows

```cmd
pip install pyinstaller
pyinstaller build/build_windows.spec
# Output: dist/Claude Token Monitor.exe
```

## How It Works

1. Reads `sessionKey` cookie from Chrome to authenticate with claude.ai
2. Fetches real usage percentages from `/api/organizations/{uuid}/usage`
3. Parses local Claude Code JSONL logs for token statistics
4. Reads Claude Code OAuth credentials for subscription info
5. Displays everything in a system tray icon + detail window

---

# 中文说明

跨平台系统托盘应用，实时监控 Claude token 用量。

## 功能

- 通过 claude.ai API 实时监控用量（5小时会话、每周全模型、每周 Sonnet）
- 彩色进度条（绿色 / 黄色 / 红色）
- 会话重置实时倒计时
- 本地 Claude Code 统计（token、缓存、会话数）
- 订阅与速率等级显示
- 系统托盘图标颜色随用量变化
- 双语界面（中文 / 英文），自动检测系统语言
- 跨平台：macOS 和 Windows

## 环境要求

- Python 3.10+
- Google Chrome 已登录 claude.ai
- 已安装 Claude Code CLI（用于订阅信息）

## 快速开始

```bash
git clone https://github.com/your-repo/claude-token-monitor.git
cd claude-token-monitor
./scripts/start.sh        # macOS/Linux
scripts\start.bat         # Windows
```

## 配置

| 环境变量 | 说明 | 默认值 |
|---|---|---|
| `CTM_LANG` | 界面语言（`en` 英文，`zh` 中文） | 自动检测系统语言 |

## License

MIT
