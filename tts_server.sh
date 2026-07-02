#!/usr/bin/env bash
#
# voice-pipeline — GPT-SoVITS API 服务管理脚本
# 用法:
#   tts_server.sh          # 检查状态，未运行则自动启动
#   tts_server.sh --on     # 启动服务
#   tts_server.sh --off    # 停止服务
#
set -e

PORT="${VOICE_PIPELINE_PORT:-9880}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="${VOICE_PIPELINE_PROJECT_DIR:-${SCRIPT_DIR}/GPT-SoVITS}"
CONDA_ENV="${VOICE_PIPELINE_CONDA:-GPTSoVits}"
PID_FILE="/tmp/voice_pipeline_server.pid"
LOG_FILE="/tmp/voice_pipeline_server.log"
CONFIG_FILE="${VOICE_PIPELINE_CONFIG:-${SCRIPT_DIR}/tts_infer.yaml}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# ── 辅助函数 ──────────────────────────────────────────

get_pid() {
    lsof -ti :${PORT} 2>/dev/null | head -1
}

is_running() {
    local pid=$(get_pid)
    [[ -n "$pid" ]]
}

show_status() {
    local pid=$(get_pid)
    if is_running; then
        echo -e "${GREEN}✅ TTS 服务运行中${NC}"
        echo "   PID:    ${pid}"
        echo "   地址:   http://127.0.0.1:${PORT}"
        echo "   项目:   ${PROJECT_DIR}"
        echo "   日志:   ${LOG_FILE}"
        echo "   Conda:  ${CONDA_ENV}"
    else
        echo -e "${RED}🔴 TTS 服务未运行${NC}"
        echo "   端口:   ${PORT}"
        echo "   项目:   ${PROJECT_DIR}"
    fi
}

# ── 启动 ──────────────────────────────────────────────

do_start() {
    if is_running; then
        echo -e "${YELLOW}⚠️  服务已在运行，无需重复启动${NC}"
        return 0
    fi

    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo -e "${RED}❌ 配置文件不存在: ${CONFIG_FILE}${NC}"
        echo "   请从 tts_infer.yaml.example 复制并修改"
        return 1
    fi

    echo -n "→ 正在启动 TTS 服务... "

    cd "$PROJECT_DIR"
    nohup conda run -n "$CONDA_ENV" --no-capture-output \
        python api_v2.py -a 0.0.0.0 -p "$PORT" \
        -c "$CONFIG_FILE" \
        > "$LOG_FILE" 2>&1 &

    local pid=$!
    echo "$pid" > "$PID_FILE"

    local waited=0
    while ! is_running && [[ $waited -lt 40 ]]; do
        sleep 1
        waited=$((waited + 1))
    done

    if is_running; then
        echo -e "${GREEN}完成${NC}"
    else
        echo -e "${RED}超时${NC}"
        echo "  请查看日志: tail -f ${LOG_FILE}"
        return 1
    fi
}

# ── 停止 ──────────────────────────────────────────────

do_stop() {
    if ! is_running; then
        echo -e "${YELLOW}⚠️  服务未在运行${NC}"
        return 0
    fi

    local pid=$(get_pid)
    echo -n "→ 正在停止 TTS 服务 (PID: ${pid})... "
    kill "$pid" 2>/dev/null

    local waited=0
    while is_running && [[ $waited -lt 10 ]]; do
        sleep 1
        waited=$((waited + 1))
    done

    if ! is_running; then
        echo -e "${GREEN}完成${NC}"
        rm -f "$PID_FILE"
    else
        echo -e "${YELLOW}强制终止...${NC}"
        kill -9 "$pid" 2>/dev/null
        sleep 1
        rm -f "$PID_FILE"
        echo -e "${GREEN}完成${NC}"
    fi
}

# ── 入口 ──────────────────────────────────────────────

case "${1:-auto}" in
    --on|on|start)
        do_start
        ;;
    --off|off|stop)
        do_stop
        ;;
    auto)
        if ! is_running; then
            echo -e "${YELLOW}→ 服务未运行，自动启动...${NC}"
            do_start
        fi
        ;;
    *)
        echo "用法: tts_server.sh [--on|--off]"
        echo ""
        echo "环境变量:"
        echo "  VOICE_PIPELINE_PROJECT_DIR   GPT-SoVITS 项目路径（默认: ./GPT-SoVITS）"
        echo "  VOICE_PIPELINE_PORT=9880     服务端口"
        echo "  VOICE_PIPELINE_CONDA=GPTSoVits   conda 环境名"
        echo "  VOICE_PIPELINE_CONFIG        推理配置文件（默认: ./tts_infer.yaml）"
        exit 1
        ;;
esac

echo ""
show_status
