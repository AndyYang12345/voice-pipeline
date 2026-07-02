#!/usr/bin/env bash
#
# voice-pipeline 安装脚本
# 将脚本 symlink 到 ~/.local/bin/，创建默认配置
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="${HOME}/.local/bin"

echo "╔══════════════════════════════════════╗"
echo "║   voice-pipeline — 安装向导          ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 检查依赖 ──
echo "→ 检查依赖..."

if ! command -v python3 &>/dev/null; then
    echo "  ❌ python3 未安装"
    exit 1
fi
echo "  ✅ python3: $(python3 --version)"

if ! command -v ffplay &>/dev/null; then
    echo "  ⚠️  ffplay 未安装（播放音频需要 ffmpeg）"
else
    echo "  ✅ ffplay: $(ffplay -version 2>&1 | head -1)"
fi

# ── 创建 bin 目录 ──
mkdir -p "$BIN_DIR"

# ── 安装 symlink ──
echo ""
echo "→ 安装脚本..."

install_script() {
    local src="$1"
    local name="$2"
    local dst="${BIN_DIR}/${name}"

    if [[ -L "$dst" ]] || [[ -f "$dst" ]]; then
        echo "  ⚠️  ${name} 已存在，跳过"
    else
        ln -s "${SCRIPT_DIR}/${src}" "$dst"
        chmod +x "${SCRIPT_DIR}/${src}"
        echo "  ✅ ${name} → ${dst}"
    fi
}

install_script "tts_speak.py" "tts-speak"
install_script "tts_config.py" "tts-config"
install_script "tts_server.sh" "tts-server"

# ── 检查 PATH ──
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "  ⚠️  ${BIN_DIR} 不在 PATH 中。"
    echo "  请将以下行添加到 ~/.zshrc 或 ~/.bashrc:"
    echo ""
    echo "    export PATH=\"${BIN_DIR}:\$PATH\""
fi

# ── 配置文件 ──
echo ""
echo "→ 配置文件..."
CONFIG_DIR="${HOME}/.voice_pipeline"

if [[ -f "${CONFIG_DIR}/config.json" ]]; then
    echo "  ⚠️  配置文件已存在: ${CONFIG_DIR}/config.json"
else
    echo "  💡 首次使用请配置:"
    echo "     tts-config                    # 交互式配置"
    echo "     tts-config --ref-dir /path/to/ref_audio"
    echo "     tts-config --ref-audio reference.wav"
    echo "     tts-config --prompt '参考テキスト' ja"
fi

# ── 更新 submodule ──
echo ""
echo "→ GPT-SoVITS submodule..."
cd "$SCRIPT_DIR"
if git submodule status | grep -q "^-"; then
    echo "  ⚠️  submodule 未初始化，请运行:"
    echo "     cd ${SCRIPT_DIR} && git submodule update --init --recursive"
else
    echo "  ✅ submodule 已就绪"
fi

echo ""
echo "══════════════════════════════════════"
echo "  安装完成！"
echo ""
echo "  快速开始:"
echo "    1. 配置推理参数: tts-config --infer-auto"
echo "    2. 配置客户端: tts-config"
echo "    3. 启动服务: tts-server"
echo "    4. 测试合成: tts-speak 'こんにちは' ja"
echo "══════════════════════════════════════"
