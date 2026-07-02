# voice-pipeline

基于 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 的本地 TTS 语音合成命令行工具链。

## 功能

| 工具 | 用途 |
|------|------|
| `tts-speak` | 合成文本为语音并自动播放（支持流式/非流式） |
| `tts-config` | 交互式/命令行配置管理 |
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

# 4. 编辑 tts_infer.yaml 指向你的模型
cp tts_infer.yaml.example tts_infer.yaml

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

## 依赖

- Python 3.8+
- conda 环境（GPT-SoVITS 推理环境）
- ffmpeg（音频播放）
- GPT-SoVITS（作为 git submodule 包含）

## 配置

配置文件位于 `~/.voice_pipeline/config.json`：

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

## 许可证

MIT License — 参见 [LICENSE](LICENSE)

本项目包含 GPT-SoVITS 作为 git submodule，GPT-SoVITS 使用 MIT License。
