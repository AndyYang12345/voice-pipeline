# voice-pipeline

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Shell](https://img.shields.io/badge/Shell-bash-4EAA25?logo=gnu-bash&logoColor=white)](https://www.gnu.org/software/bash/)
[![Platform](https://img.shields.io/badge/platform-Linux%20|%20macOS-lightgrey)](https://github.com/AndyYang12345/voice-pipeline)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![GPT-SoVITS](https://img.shields.io/badge/GPT--SoVITS-submodule-8A2BE2)](https://github.com/RVC-Boss/GPT-SoVITS)

基于 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 的本地 TTS 语音合成命令行工具链。

## 功能

| 工具 | 用途 |
|------|------|
| `tts-speak` | 合成文本为语音并自动播放（支持流式/非流式） |
| `tts-config` | 交互式/命令行配置管理（客户端 + 推理） |
| `tts-server` | API 服务生命周期管理（启动/停止/状态） |

## 快速开始

### 场景 A：新用户（使用 submodule）

```bash
# 1. 克隆（含 GPT-SoVITS submodule）
git clone --recurse-submodules https://github.com/<your-username>/voice-pipeline.git
cd voice-pipeline

# 2. 安装
bash install.sh

# 3. 放置模型权重和参考音频
#   models/gpt_weights/xxx.ckpt
#   models/sovits_weights/xxx.pth
#   ref_audio/reference.wav

# 4. 自动配置推理参数（一键检测模型、设备、路径）
tts-config --infer-auto

# 5. 配置参考音频
tts-config --ref-dir ./ref_audio
tts-config --ref-audio reference.wav
tts-config --prompt "参考音频对应的文本" ja

# 6. 启动服务并合成
tts-server
tts-speak "こんにちは。" ja
```

### 场景 B：已有 GPT-SoVITS 安装（客户端模式）

如果你已经有运行中的 GPT-SoVITS 服务，只需要客户端工具：

```bash
# 不需要 submodule
git clone https://github.com/<your-username>/voice-pipeline.git
cd voice-pipeline && bash install.sh

# 指向你的服务器
tts-config --server 192.168.1.100:9880

# 直接使用
tts-speak "こんにちは。" ja
```

### 场景 C：已有 GPT-SoVITS 安装（需要服务管理）

用环境变量指向你已有的 GPT-SoVITS 目录：

```bash
git clone https://github.com/<your-username>/voice-pipeline.git
cd voice-pipeline && bash install.sh

# 通过环境变量指定 GPT-SoVITS 路径
export VOICE_PIPELINE_PROJECT_DIR=/path/to/your/GPT-SoVITS
export VOICE_PIPELINE_CONFIG=/path/to/your/tts_infer.yaml

tts-server  # 使用你已有的安装启动服务
```

## 依赖

- Python 3.8+ / PyYAML
- conda 环境（GPT-SoVITS 推理环境）
- ffmpeg（音频播放）
- GPT-SoVITS（作为 git submodule 包含）

## 配置

### 客户端配置 (`~/.voice_pipeline/config.json`)

```json
{
  "server": {"host": "127.0.0.1", "port": 9880},
  "stream_mode": 2,
  "reference": {
    "audio_dir": "/path/to/ref_audio",
    "default_audio": "reference.wav",
    "default_prompt_text": "参考音频对应文本",
    "default_prompt_lang": "ja"
  }
}
```

可通过 `tts-config` 交互式菜单或命令行参数管理：

```bash
tts-config                  # 交互式菜单
tts-config --show           # 查看当前配置
tts-config --server 192.168.1.100:9880
tts-config --mode 2
tts-config --ref-audio reference.wav
tts-config --ref-dir /path/to/ref_audio
tts-config --prompt "参考テキスト" ja
tts-config --toggle on|off  # 语音播报开关
```

### 推理配置 (`tts_infer.yaml`)

GPT-SoVITS 服务端的模型配置文件。**无需手动编辑**，通过 `tts-config` 管理：

```bash
tts-config --infer-auto              # 一键自动检测模型并配置（推荐）
tts-config --infer-show              # 查看当前推理配置
tts-config --infer-device cuda       # 设置推理设备 (cuda/cpu)
tts-config --infer-half on           # 切换半精度 (on/off)
tts-config --infer-version v2ProPlus # 设置模型版本
tts-config --infer-gpt-weights PATH  # 设置 GPT 权重路径
tts-config --infer-sovits-weights PATH # 设置 SoVITS 权重路径
tts-config --infer-init              # 从模板初始化配置文件
```

也可以在 `tts-config` 交互式菜单中选择 `[7] 配置推理参数` 进入子菜单逐项设置。

`--infer-auto` 的自动检测逻辑：
1. 扫描 `models/gpt_weights/` 下的 `.ckpt` 文件
2. 扫描 `models/sovits_weights/` 下的 `.pth` 文件
3. 通过 `nvidia-smi` / `torch.cuda` 检测最佳设备
4. 从目录名/文件名推断模型版本
5. 自动生成相对于 GPT-SoVITS 的正确路径

## 环境变量

`tts-server` 支持以下环境变量，用于适配不同部署环境：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `VOICE_PIPELINE_PROJECT_DIR` | `./GPT-SoVITS` | GPT-SoVITS 项目根目录 |
| `VOICE_PIPELINE_PORT` | 9880 | 服务端口 |
| `VOICE_PIPELINE_CONDA` | GPTSoVits | conda 环境名 |
| `VOICE_PIPELINE_CONFIG` | `./tts_infer.yaml` | 推理配置文件路径 |

`tts-speak` 和 `tts-config` 不依赖本地 GPT-SoVITS，只通过 HTTP API 交互。
服务器地址通过 `~/.voice_pipeline/config.json` 配置。

## 相关项目

- [voice-assistant](https://github.com/AndyYang12345/voice-assistant) — Claude Code 语音助手插件，基于 voice-pipeline 提供 TTS 语音交互集成

## 许可证

MIT License — 参见 [LICENSE](LICENSE)

本项目包含 GPT-SoVITS 作为 git submodule，GPT-SoVITS 使用 MIT License。
