# voice-pipeline

[**中文**](README.md) | **English**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Shell](https://img.shields.io/badge/Shell-bash-4EAA25?logo=gnu-bash&logoColor=white)](https://www.gnu.org/software/bash/)
[![Platform](https://img.shields.io/badge/platform-Linux%20|%20macOS-lightgrey)](https://github.com/AndyYang12345/voice-pipeline)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![GPT-SoVITS](https://img.shields.io/badge/GPT--SoVITS-submodule-8A2BE2)](https://github.com/RVC-Boss/GPT-SoVITS)

Local TTS voice synthesis CLI toolchain powered by [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS).

## Highlights

Turns GPT-SoVITS from a raw inference engine (manual YAML edits, hand-written paths) into a **production-ready CLI product**.

| Highlight | Description |
|-----------|-------------|
| 🔍 **One-Click Auto-Config** | `--infer-auto` scans `models/`, auto-discovers weight files, detects GPU/CUDA, infers version, and generates correct paths. The only GPT-SoVITS tool with this feature |
| 🎧 **Streaming + Instant Playback** | Generate and play simultaneously — hear the first sentence before the full text finishes. 4 streaming modes (sentence / semantic chunk / fixed chunk / full synthesis) |
| 🤖 **Claude Code Voice Assistant** | The only project integrating GPT-SoVITS with an AI coding assistant — Priestess character roleplay, context-aware TTS (permission prompts, error notifications, progress updates, welcome messages) |
| 🧩 **Standalone Toolchain** | Not a QQ/WeChat/nonebot plugin, not dependent on any external framework. `install.sh` one-liner setup, `tts-server` lifecycle management |
| 🎛️ **Unified Config Management** | `tts-config` manages all settings (client + inference) from a single tool. Interactive menu + CLI flags dual mode — no manual JSON or YAML editing |
| 🔄 **Persistent Service + Hot-Swap** | Models loaded once, subsequent requests respond instantly. Hot-swap GPT/SoVITS weights at runtime without restarting the server |

## Tools

| Tool | Purpose |
|------|---------|
| `tts-speak` | Synthesize text to speech and auto-play (streaming & non-streaming) |
| `tts-config` | Interactive / CLI configuration management (client + inference) |
| `tts-server` | API server lifecycle management (start / stop / status) |

## Quick Start

> 💡 The minimal flow below gets you up and running with a single auto-config command. For fine-tuning individual parameters, see [Configuration](#configuration).

### Scenario A: Full Installation (submodule, recommended)

```bash
# 1. Clone and install
git clone --recurse-submodules https://github.com/AndyYang12345/voice-pipeline.git
cd voice-pipeline
bash install.sh

# 2. Set up GPT-SoVITS environment
#    → Follow the GPT-SoVITS official guide to create a conda environment (default: GPTSoVits)
#    → https://github.com/RVC-Boss/GPT-SoVITS

# 3. Place your model files and reference audio
mkdir -p models/gpt_weights models/sovits_weights ref_audio
#   → Put your .ckpt in models/gpt_weights/
#   → Put your .pth  in models/sovits_weights/
#   → Put reference audio in ref_audio/

# 4. One-click config (auto-detect models, device, version)
tts-config --infer-auto

# 5. Configure reference audio
tts-config --ref-dir ./ref_audio
tts-config --ref-audio reference.wav
tts-config --prompt "reference audio transcript text" ja

# 6. Start server and test
tts-server
tts-speak "こんにちは。" ja
```

> 📖 Step 4's `--infer-auto` automatically scans `models/`, detects GPU/CUDA, infers version, and generates `tts_infer.yaml`. To manually tweak device, half-precision, paths, etc., use `tts-config --infer-show` or see [Inference Config](#inference-config-tts_inferyaml).

### Scenario B: Existing GPT-SoVITS Service (client-only)

If you already have a running GPT-SoVITS API server:

```bash
git clone https://github.com/AndyYang12345/voice-pipeline.git
cd voice-pipeline && bash install.sh

# Point to your server
tts-config --server 192.168.1.100:9880

# Use directly
tts-speak "こんにちは。" ja
```

### Scenario C: Existing GPT-SoVITS Installation (self-managed server)

Point to your own GPT-SoVITS directory via environment variables:

```bash
git clone https://github.com/AndyYang12345/voice-pipeline.git
cd voice-pipeline && bash install.sh

# Point to your GPT-SoVITS installation and config
export VOICE_PIPELINE_PROJECT_DIR=/path/to/your/GPT-SoVITS
export VOICE_PIPELINE_CONFIG=/path/to/your/tts_infer.yaml

# Auto-config still works (writes to $VOICE_PIPELINE_CONFIG)
tts-config --infer-auto

tts-server
tts-speak "こんにちは。" ja
```

## Dependencies

- Python 3.8+ / PyYAML
- conda environment — set up via the [GPT-SoVITS official guide](https://github.com/RVC-Boss/GPT-SoVITS) (default env name: `GPTSoVits`)
- ffmpeg (audio playback)
- GPT-SoVITS (included as git submodule)

## Configuration

### Client Config (`~/.voice_pipeline/config.json`)

```json
{
  "server": {"host": "127.0.0.1", "port": 9880},
  "stream_mode": 2,
  "reference": {
    "audio_dir": "/path/to/ref_audio",
    "default_audio": "reference.wav",
    "default_prompt_text": "reference audio transcript",
    "default_prompt_lang": "ja"
  }
}
```

Manage via `tts-config` interactive menu or CLI flags:

```bash
tts-config                  # interactive menu
tts-config --show           # view current config
tts-config --server 192.168.1.100:9880
tts-config --mode 2
tts-config --ref-audio reference.wav
tts-config --ref-dir /path/to/ref_audio
tts-config --prompt "reference text" ja
tts-config --toggle on|off  # voice announcement toggle
```

### Inference Config (`tts_infer.yaml`)

Server-side model configuration for GPT-SoVITS. **No manual editing needed** — manage entirely through `tts-config`:

```bash
tts-config --infer-auto              # one-click auto-detect & configure (recommended)
tts-config --infer-show              # view current inference config
tts-config --infer-device cuda       # set device (cuda/cpu)
tts-config --infer-half on           # toggle half precision (on/off)
tts-config --infer-version v2ProPlus # set model version
tts-config --infer-gpt-weights PATH  # set GPT weights path
tts-config --infer-sovits-weights PATH # set SoVITS weights path
tts-config --infer-init              # initialize config from template
```

You can also select `[7] Configure Inference` from the `tts-config` interactive menu for step-by-step setup.

`--infer-auto` detection logic:
1. Scan `models/gpt_weights/` for `.ckpt` files
2. Scan `models/sovits_weights/` for `.pth` files
3. Detect optimal device via `nvidia-smi` / `torch.cuda`
4. Infer model version from directory/file names
5. Generate correct paths relative to GPT-SoVITS

## Environment Variables

`tts-server` accepts the following environment variables for flexible deployment:

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_PIPELINE_PROJECT_DIR` | `./GPT-SoVITS` | GPT-SoVITS project root |
| `VOICE_PIPELINE_PORT` | 9880 | Server port |
| `VOICE_PIPELINE_CONDA` | GPTSoVits | conda environment name |
| `VOICE_PIPELINE_CONFIG` | `./tts_infer.yaml` | Inference config file path |

`tts-speak` and `tts-config` do not require a local GPT-SoVITS installation — they interact purely through the HTTP API. Server address is configured in `~/.voice_pipeline/config.json`.

## Related Projects

- [voice-assistant](https://github.com/AndyYang12345/voice-assistant) — Claude Code voice assistant plugin, provides TTS voice interaction integration on top of voice-pipeline

## License

MIT License — see [LICENSE](LICENSE)

This project includes GPT-SoVITS as a git submodule. GPT-SoVITS is also MIT-licensed.
