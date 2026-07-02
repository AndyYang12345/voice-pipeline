# voice-pipeline

基于 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 的本地 TTS 语音合成命令行工具链。

## 功能

| 工具 | 用途 |
|------|------|
| `tts-speak` | 合成文本为语音并自动播放（支持流式/非流式） |
| `tts-config` | 交互式/命令行配置管理 |
| `tts-server` | API 服务生命周期管理（启动/停止/状态） |

## 快速开始

### 1. 克隆并初始化

```bash
git clone --recurse-submodules https://github.com/<your-username>/voice-pipeline.git
cd voice-pipeline
```

### 2. 安装

```bash
bash install.sh
```

### 3. 配置

```bash
# 设置参考音频（必需）
tts-config --ref-dir ./ref_audio
tts-config --ref-audio reference.wav
tts-config --prompt "参考音频对应的文本" ja

# 设置服务器地址（默认 127.0.0.1:9880）
tts-config --server 127.0.0.1:9880
```

### 4. 准备模型

将训练好的模型权重放入 `models/` 目录，然后复制并编辑 `tts_infer.yaml`：

```bash
cp tts_infer.yaml.example tts_infer.yaml
# 编辑 tts_infer.yaml，设置正确的模型路径
```

### 5. 启动服务并合成

```bash
tts-server              # 启动 API 服务
tts-speak "こんにちは。" ja   # 合成并播放
```

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

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `VOICE_PIPELINE_PORT` | 9880 | 服务端口 |
| `VOICE_PIPELINE_CONDA` | GPTSoVits | conda 环境名 |
| `VOICE_PIPELINE_CONFIG` | ./tts_infer.yaml | 推理配置文件路径 |

## 许可证

MIT License — 参见 [LICENSE](LICENSE)

本项目包含 GPT-SoVITS 作为 git submodule，GPT-SoVITS 使用 MIT License。
