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

> 💡 以下是最简上手流程，一条命令完成推理配置。如需微调各项参数，参见下方 [配置](#配置) 章节。

### 场景 A：完整安装（submodule，新手推荐）

```bash
# 1. 克隆并安装
git clone --recurse-submodules https://github.com/AndyYang12345/voice-pipeline.git
cd voice-pipeline
bash install.sh

# 2. 配置 GPT-SoVITS 环境
#    → 按照 GPT-SoVITS 官方文档创建 conda 环境（默认名 GPTSoVits）并安装依赖
#    → https://github.com/RVC-Boss/GPT-SoVITS

# 3. 放入你的模型文件和参考音频
mkdir -p models/gpt_weights models/sovits_weights ref_audio
#   → 将 .ckpt 放入 models/gpt_weights/
#   → 将 .pth  放入 models/sovits_weights/
#   → 将参考音频放入 ref_audio/

# 4. 一键配置（自动检测模型、设备、版本）
tts-config --infer-auto

# 5. 配置参考音频
tts-config --ref-dir ./ref_audio
tts-config --ref-audio reference.wav
tts-config --prompt "参考音频对应的文本" ja

# 6. 启动服务，测试合成
tts-server
tts-speak "こんにちは。" ja
```

> 📖 步骤 4 的 `--infer-auto` 会自动扫描 `models/` 目录、检测 GPU/CUDA、推断版本并生成 `tts_infer.yaml`。如需手动调整设备、半精度、路径等参数，使用 `tts-config --infer-show` 查看，或参见 [推理配置](#推理配置-tts_inferyaml) 章节逐项修改。

### 场景 B：已有 GPT-SoVITS 服务（纯客户端）

如果你已经有运行中的 GPT-SoVITS API 服务，只需客户端工具：

```bash
git clone https://github.com/AndyYang12345/voice-pipeline.git
cd voice-pipeline && bash install.sh

# 指向你的服务器
tts-config --server 192.168.1.100:9880

# 直接使用
tts-speak "こんにちは。" ja
```

### 场景 C：已有 GPT-SoVITS 安装（自管服务）

用环境变量指向你已有的 GPT-SoVITS 目录：

```bash
git clone https://github.com/AndyYang12345/voice-pipeline.git
cd voice-pipeline && bash install.sh

# 指定 GPT-SoVITS 路径和推理配置
export VOICE_PIPELINE_PROJECT_DIR=/path/to/your/GPT-SoVITS
export VOICE_PIPELINE_CONFIG=/path/to/your/tts_infer.yaml

# 仍可使用一键配置（会写入 $VOICE_PIPELINE_CONFIG 指向的文件）
tts-config --infer-auto

tts-server
tts-speak "こんにちは。" ja
```

## 依赖

- Python 3.8+ / PyYAML
- conda 环境 — 按 [GPT-SoVITS 官方指南](https://github.com/RVC-Boss/GPT-SoVITS) 配置（默认环境名 `GPTSoVits`）
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
