#!/usr/bin/env python3
"""
voice-pipeline — GPT-SoVITS 语音合成播放工具
用法:
    python tts_speak.py "こんにちは。" ja                   # 流式合成+播放
    python tts_speak.py "こんにちは。" ja --no-stream       # 完整合成后播放
    python tts_speak.py --set-server 192.168.1.100:9880      # 设置远程服务器
    python tts_speak.py --set-server 127.0.0.1:9880          # 恢复本地服务器
    python tts_speak.py --set-default-mode 2                  # 设置流式模式
    python tts_speak.py --set-ref-audio /path/to/ref.wav      # 设置默认参考音频
    python tts_speak.py --set-prompt "参考テキスト" ja       # 设置默认提示文本
    python tts_speak.py --status                              # 查看当前配置
    python tts_speak.py --list-refs                           # 查看参考音频
    python tts_speak.py --check-toggle                        # 检查开关状态
"""

import argparse
import json
import subprocess
import sys
import os
import struct
import requests

# ── 路径常量 ──────────────────────────────────────────

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.expanduser("~/.voice_pipeline")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
TOGGLE_FILE = os.path.expanduser("~/.tts_speak_enabled")

STREAM_MODES = {
    0: "普通（完整合成）",
    1: "流式·分句返回",
    2: "流式·语义块（默认）",
    3: "流式·定长块",
}

DEFAULT_CONFIG = {
    "server": {
        "host": "127.0.0.1",
        "port": 9880,
    },
    "stream_mode": 2,
    "reference": {
        "audio_dir": "",
        "default_audio": "",
        "default_prompt_text": "",
        "default_prompt_lang": "ja",
    },
}


# ── 配置读写 ──────────────────────────────────────────

def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def is_enabled():
    return os.path.exists(TOGGLE_FILE)


def load_config():
    """加载完整配置，缺失字段用默认值补齐"""
    cfg = DEFAULT_CONFIG.copy()
    cfg["reference"] = DEFAULT_CONFIG["reference"].copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
            if "server" in saved:
                cfg["server"].update(saved["server"])
            cfg["stream_mode"] = saved.get("stream_mode", DEFAULT_CONFIG["stream_mode"])
            if "reference" in saved:
                cfg["reference"].update(saved["reference"])
        except (json.JSONDecodeError, KeyError):
            pass
    return cfg


def save_config(cfg: dict):
    """保存配置（深度合并）"""
    ensure_config_dir()
    current = load_config()
    _deep_merge(current, cfg)
    with open(CONFIG_FILE, "w") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)


def _deep_merge(base, update):
    """递归合并嵌套 dict"""
    for k, v in update.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def get_server_url():
    cfg = load_config()
    srv = cfg["server"]
    return f"http://{srv['host']}:{srv['port']}"


# ── 管理命令 ──────────────────────────────────────────

def show_status():
    cfg = load_config()
    srv = cfg["server"]
    ref = cfg["reference"]
    print(f"TTS 服务器:  http://{srv['host']}:{srv['port']}")
    print(f"默认模式:    {STREAM_MODES.get(cfg['stream_mode'], '?')} (mode={cfg['stream_mode']})")
    print(f"参考音频:    {ref['default_audio'] or '(未设置)'}")
    print(f"提示文本:    {ref['default_prompt_text'] or '(未设置)'}")
    print(f"提示语言:    {ref['default_prompt_lang']}")
    print(f"语音播报:    {'✅ 开启' if is_enabled() else '🔇 关闭'}")
    print(f"音频目录:    {ref['audio_dir'] or '(未设置)'}")
    print(f"配置文件:    {CONFIG_FILE}")


def list_refs():
    cfg = load_config()
    ref_dir = cfg["reference"].get("audio_dir", "")
    if not ref_dir or not os.path.isdir(ref_dir):
        print(f"参考音频目录未设置或不存在。请使用 --set-ref-audio-dir 配置。", file=sys.stderr)
        print(f"当前设置: {ref_dir or '(空)'}", file=sys.stderr)
        sys.exit(1)
    files = sorted(f for f in os.listdir(ref_dir) if f.endswith(('.wav', '.mp3', '.flac', '.ogg')))
    if not files:
        print(f"目录 {ref_dir} 中未找到音频文件", file=sys.stderr)
        sys.exit(1)
    default = cfg["reference"].get("default_audio", "")
    for i, f in enumerate(files, 1):
        label = " ★" if f == default else ""
        print(f"  {i:2d}. {f}{label}")
    if default and default not in files:
        print(f"\n⚠ 默认参考音频 '{default}' 不在目录中")
    print(f"\n目录: {ref_dir}")


# ── 请求构建 ──────────────────────────────────────────

def resolve_ref_path(ref):
    """解析参考音频路径：绝对路径直接返回，相对路径从 audio_dir 查找"""
    if os.path.isabs(ref):
        return ref

    cfg = load_config()
    audio_dir = cfg["reference"].get("audio_dir", "")
    if audio_dir:
        candidate = os.path.join(audio_dir, ref)
        if os.path.exists(candidate):
            return candidate

    # 回退：当前目录
    candidate = os.path.join(PIPELINE_DIR, ref)
    if os.path.exists(candidate):
        return candidate

    return ref  # 让服务器报错


def build_payload(text, lang, ref, prompt_text, prompt_lang):
    cfg = load_config()
    ref_cfg = cfg["reference"]

    ref = ref or ref_cfg.get("default_audio", "")
    if not ref:
        print("[エラー] 参考音频未设置。请使用 -r 指定或 --set-ref-audio 配置默认值。", file=sys.stderr)
        sys.exit(1)

    prompt_text = prompt_text or ref_cfg.get("default_prompt_text", "")
    prompt_lang = prompt_lang or ref_cfg.get("default_prompt_lang", lang)
    ref_path = resolve_ref_path(ref)

    if not os.path.exists(ref_path):
        print(f"[エラー] 参考音声が見つかりません: {ref_path}", file=sys.stderr)
        sys.exit(1)

    return {
        "text": text,
        "text_lang": lang,
        "ref_audio_path": ref_path,
        "prompt_text": prompt_text,
        "prompt_lang": prompt_lang,
    }, ref_path


def parse_wav_header(data: bytes):
    """从 WAV 头部解析采样率，返回 (sample_rate, channels, header_size)"""
    if len(data) < 44:
        raise ValueError(f"WAV头部过短: {len(data)} bytes")
    sr = struct.unpack_from("<I", data, 24)[0]
    channels = struct.unpack_from("<H", data, 22)[0]
    return sr, channels, 44


# ── 普通模式 ──────────────────────────────────────────

def speak(text: str, lang: str = "ja", ref: str = None, prompt_text: str = None,
          prompt_lang: str = None, quiet: bool = False):
    """完整合成后播放"""
    server_url = get_server_url()
    payload, _ = build_payload(text, lang, ref, prompt_text, prompt_lang)

    try:
        resp = requests.post(f"{server_url}/tts", json=payload, timeout=120)
    except requests.exceptions.ConnectionError:
        if not quiet:
            print(f"[エラー] サーバー {server_url} に接続できません", file=sys.stderr)
        sys.exit(1)

    if resp.status_code != 200:
        if not quiet:
            print(f"[エラー] HTTP {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    tmp_path = os.path.join(CONFIG_DIR, "tts_tmp.wav")
    ensure_config_dir()
    with open(tmp_path, "wb") as f:
        f.write(resp.content)

    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


# ── 流式模式 ──────────────────────────────────────────

def speak_stream(text: str, lang: str = "ja", ref: str = None, prompt_text: str = None,
                 prompt_lang: str = None, quiet: bool = False, stream_mode: int = 2):
    """逐块合成 + 实时播放"""
    server_url = get_server_url()
    payload, _ = build_payload(text, lang, ref, prompt_text, prompt_lang)
    payload["streaming_mode"] = stream_mode

    try:
        resp = requests.post(f"{server_url}/tts", json=payload, stream=True, timeout=120)
    except requests.exceptions.ConnectionError:
        if not quiet:
            print(f"[エラー] サーバー {server_url} に接続できません", file=sys.stderr)
        sys.exit(1)

    if resp.status_code != 200:
        if not quiet:
            print(f"[エラー] HTTP {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    chunks = resp.iter_content(chunk_size=None)
    try:
        first_chunk = next(chunks)
    except StopIteration:
        print("[エラー] サーバーからデータがありません", file=sys.stderr)
        sys.exit(1)

    sr, channels, header_size = parse_wav_header(first_chunk[:44])
    body_remainder = first_chunk[header_size:]

    if not quiet:
        print(f"→ 流式 (mode={stream_mode}, {STREAM_MODES[stream_mode]}, {sr}Hz)...",
              flush=True)

    proc = subprocess.Popen(
        ["ffplay", "-f", "s16le", "-ar", str(sr), "-ac", str(channels),
         "-nodisp", "-autoexit", "-loglevel", "quiet", "-i", "pipe:0"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        if body_remainder:
            proc.stdin.write(body_remainder)
        for chunk in chunks:
            if chunk:
                proc.stdin.write(chunk)
        proc.stdin.close()
        proc.wait()
    except BrokenPipeError:
        proc.kill()
        proc.wait()


# ── 入口 ──────────────────────────────────────────────

def parse_server(value: str) -> dict:
    if ":" in value:
        host, port = value.rsplit(":", 1)
        return {"host": host.strip(), "port": int(port)}
    cfg = load_config()
    return {"host": value.strip(), "port": cfg["server"]["port"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="voice-pipeline — GPT-SoVITS TTS 语音合成播放",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tts_speak.py "こんにちは。" ja
  python tts_speak.py "こんにちは。" ja -r my_ref.wav -p "参考テキスト"
  python tts_speak.py --set-ref-audio my_ref.wav --set-prompt "参考テキスト" ja
  python tts_speak.py --set-server 192.168.1.100:9880
  python tts_speak.py --status
        """,
    )
    parser.add_argument("text", nargs="?", help="要合成的文本")
    parser.add_argument("lang", nargs="?", default="ja",
                        help="文本语言 (ja/zh/en/ko/yue)，默认 ja")
    parser.add_argument("-r", "--ref", help="参考音频文件名或路径")
    parser.add_argument("-p", "--prompt", help="参考音频对应文本")
    parser.add_argument("-l", "--lang-ref", help="参考音频语言，默认同文本语言")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="安静模式（无控制台输出）")
    parser.add_argument("--no-stream", action="store_true",
                        help="关闭流式，使用完整合成模式")
    parser.add_argument("--stream-mode", type=int, choices=[1, 2, 3],
                        help="流式模式: 1=分句, 2=语义块, 3=定长块")

    # ── 配置命令 ──
    parser.add_argument("--set-server", type=str, metavar="HOST:PORT",
                        help="设置 TTS 服务器地址")
    parser.add_argument("--set-default-mode", type=int, choices=[0, 1, 2, 3],
                        help="设置默认合成模式")
    parser.add_argument("--set-ref-audio", type=str, metavar="FILE",
                        help="设置默认参考音频文件名")
    parser.add_argument("--set-ref-audio-dir", type=str, metavar="DIR",
                        help="设置参考音频目录")
    parser.add_argument("--set-prompt", type=str, nargs=2, metavar=("TEXT", "LANG"),
                        help="设置默认提示文本和语言")
    parser.add_argument("--status", action="store_true",
                        help="查看当前配置状态")
    parser.add_argument("--list-refs", action="store_true",
                        help="列出所有可用参考音频")
    parser.add_argument("--check-toggle", action="store_true",
                        help="检查开关状态，exit 0=开, 1=关")

    args = parser.parse_args()

    # ── 管理命令 ──
    if args.check_toggle:
        sys.exit(0 if is_enabled() else 1)

    if args.status:
        show_status()
        sys.exit(0)

    if args.set_server:
        save_config({"server": parse_server(args.set_server)})
        print(f"✅ 服务器已设为: {get_server_url()}")
        sys.exit(0)

    if args.set_default_mode is not None:
        save_config({"stream_mode": args.set_default_mode})
        print(f"✅ 默认模式已设为: {STREAM_MODES[args.set_default_mode]}")
        sys.exit(0)

    if args.set_ref_audio:
        save_config({"reference": {"default_audio": args.set_ref_audio}})
        cfg = load_config()
        print(f"✅ 默认参考音频已设为: {cfg['reference']['default_audio']}")
        sys.exit(0)

    if args.set_ref_audio_dir:
        path = os.path.abspath(args.set_ref_audio_dir)
        save_config({"reference": {"audio_dir": path}})
        print(f"✅ 参考音频目录已设为: {path}")
        sys.exit(0)

    if args.set_prompt:
        text, lang = args.set_prompt
        save_config({"reference": {"default_prompt_text": text, "default_prompt_lang": lang}})
        print(f"✅ 默认提示文本已设为: {text}")
        print(f"   提示语言: {lang}")
        sys.exit(0)

    if args.list_refs:
        list_refs()
        sys.exit(0)

    # ── 合成命令 ──
    if not args.text:
        parser.print_help()
        sys.exit(0)

    if args.no_stream:
        use_stream = False
        stream_mode = 2
    else:
        stream_mode = args.stream_mode or load_config()["stream_mode"]
        use_stream = stream_mode > 0

    if use_stream:
        speak_stream(
            args.text, lang=args.lang, ref=args.ref,
            prompt_text=args.prompt, prompt_lang=args.lang_ref,
            quiet=args.quiet, stream_mode=stream_mode,
        )
    else:
        speak(
            args.text, lang=args.lang, ref=args.ref,
            prompt_text=args.prompt, prompt_lang=args.lang_ref,
            quiet=args.quiet,
        )
