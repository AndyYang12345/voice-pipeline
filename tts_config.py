#!/usr/bin/env python3
"""
voice-pipeline — GPT-SoVITS 客户端配置工具
用法:
    python tts_config.py                        # 交互式菜单
    python tts_config.py --show                 # 查看当前配置
    python tts_config.py --server 192.168.1.100:9880   # 设置服务器
    python tts_config.py --host 192.168.1.100   # 仅改 IP
    python tts_config.py --port 9880            # 仅改端口
    python tts_config.py --mode 2               # 设置合成模式
    python tts_config.py --ref-audio /path/to/ref.wav  # 设置参考音频
    python tts_config.py --ref-dir /path/to/dir        # 设置音频目录
    python tts_config.py --prompt "テキスト" ja        # 设置提示文本
    python tts_config.py --toggle on            # 开启语音播报
    python tts_config.py --toggle off           # 关闭语音播报
"""

import argparse
import json
import os
import sys

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.expanduser("~/.voice_pipeline")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
TOGGLE_FILE = os.path.expanduser("~/.tts_speak_enabled")

MODE_CHOICES = {
    "0": ("普通模式", "完整合成后一次性播放，质量最好"),
    "1": ("流式·分句", "按标点分句，逐句返回"),
    "2": ("流式·语义块", "边生成边播放，平衡质量与延迟（推荐）"),
    "3": ("流式·定长块", "最快响应，质量略降"),
}

DEFAULT_CONFIG = {
    "server": {"host": "127.0.0.1", "port": 9880},
    "stream_mode": 2,
    "reference": {
        "audio_dir": "",
        "default_audio": "",
        "default_prompt_text": "",
        "default_prompt_lang": "ja",
    },
}


def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load():
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


def save(cfg):
    ensure_config_dir()
    current = load()
    _deep_merge(current, cfg)
    with open(CONFIG_FILE, "w") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)


def _deep_merge(base, update):
    for k, v in update.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def toggle_status():
    return os.path.exists(TOGGLE_FILE)


def cmd_show():
    cfg = load()
    srv = cfg["server"]
    ref = cfg["reference"]
    mode = str(cfg.get("stream_mode", 2))
    mode_name, mode_desc = MODE_CHOICES.get(mode, ("?", ""))

    print("╔══════════════════════════════════════╗")
    print("║     voice-pipeline 客户端配置        ║")
    print("╠══════════════════════════════════════╣")
    print(f"║  服务器地址  │ http://{srv['host']}:{srv['port']}")
    print(f"║  合成模式    │ {mode_name} (mode={mode})")
    print(f"║              │ {mode_desc}")
    print(f"║  参考音频    │ {ref['default_audio'] or '(未设置)'}")
    print(f"║  提示文本    │ {ref['default_prompt_text'] or '(未设置)'}")
    print(f"║  提示语言    │ {ref['default_prompt_lang']}")
    print(f"║  音频目录    │ {ref['audio_dir'] or '(未设置)'}")
    print(f"║  语音播报    │ {'✅ 开启' if toggle_status() else '🔇 关闭'}")
    print(f"║  配置文件    │ {CONFIG_FILE}")
    print("╚══════════════════════════════════════╝")


def cmd_set_server(host, port=None):
    if ":" in host and port is None:
        host, p = host.rsplit(":", 1)
        port = int(p)
    cfg = {"server": {}}
    cfg["server"]["host"] = host.strip()
    if port is not None:
        cfg["server"]["port"] = int(port)
    save(cfg)
    updated = load()
    print(f"✅ 服务器已设为: http://{updated['server']['host']}:{updated['server']['port']}")


def cmd_set_mode(mode):
    save({"stream_mode": mode})
    name, desc = MODE_CHOICES.get(str(mode), ("?", ""))
    print(f"✅ 合成模式已设为: {name}")


def cmd_set_ref_audio(path):
    save({"reference": {"default_audio": path}})
    print(f"✅ 默认参考音频已设为: {path}")


def cmd_set_ref_dir(path):
    save({"reference": {"audio_dir": os.path.abspath(path)}})
    print(f"✅ 参考音频目录已设为: {os.path.abspath(path)}")


def cmd_set_prompt(text, lang="ja"):
    save({"reference": {"default_prompt_text": text, "default_prompt_lang": lang}})
    print(f"✅ 提示文本已设为: {text}")
    print(f"   提示语言: {lang}")


def cmd_toggle(action=None):
    if action == "on":
        open(TOGGLE_FILE, "w").close()
        print("✅ 语音播报已开启")
    elif action == "off":
        if os.path.exists(TOGGLE_FILE):
            os.remove(TOGGLE_FILE)
        print("🔇 语音播报已关闭")
    else:
        print(f"语音播报: {'✅ 开启' if toggle_status() else '🔇 关闭'}")


# ── 交互式菜单 ──────────────────────────────────────

def interactive():
    while True:
        cmd_show()
        print()
        print("  [1] 修改服务器地址")
        print("  [2] 修改合成模式")
        print("  [3] 切换语音播报开关")
        print("  [4] 设置参考音频")
        print("  [5] 设置参考音频目录")
        print("  [6] 设置提示文本")
        print("  [0] 退出")
        print()
        try:
            choice = input("请选择 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if choice == "1":
            cfg = load()
            host = input(f"  服务器 IP [{cfg['server']['host']}] > ").strip()
            port_str = input(f"  端口 [{cfg['server']['port']}] > ").strip()
            update = {"server": {}}
            if host:
                update["server"]["host"] = host
            if port_str:
                update["server"]["port"] = int(port_str)
            if update["server"]:
                save(update)
                cfg2 = load()
                print(f"  ✅ 已更新: http://{cfg2['server']['host']}:{cfg2['server']['port']}")
            print()

        elif choice == "2":
            print()
            for k, (name, desc) in MODE_CHOICES.items():
                print(f"  [{k}] {name} — {desc}")
            mode = input("\n  选择模式 > ").strip()
            if mode in MODE_CHOICES:
                cmd_set_mode(int(mode))
            else:
                print("  ❌ 无效选项")
            print()

        elif choice == "3":
            if toggle_status():
                cmd_toggle("off")
            else:
                cmd_toggle("on")
            print()

        elif choice == "4":
            cfg = load()
            ref = input(f"  参考音频文件名 [{cfg['reference'].get('default_audio', '')}] > ").strip()
            if ref:
                cmd_set_ref_audio(ref)
            print()

        elif choice == "5":
            cfg = load()
            d = input(f"  参考音频目录 [{cfg['reference'].get('audio_dir', '')}] > ").strip()
            if d:
                cmd_set_ref_dir(d)
            print()

        elif choice == "6":
            cfg = load()
            text = input(f"  提示文本 [{cfg['reference'].get('default_prompt_text', '')}] > ").strip()
            lang = input(f"  提示语言 [{cfg['reference'].get('default_prompt_lang', 'ja')}] > ").strip() or "ja"
            if text:
                cmd_set_prompt(text, lang)
            print()

        elif choice == "0":
            print("Goodbye")
            break

        else:
            print("  ❌ 未知选项")
            print()


# ── CLI 入口 ──────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="voice-pipeline — GPT-SoVITS 客户端配置工具")
    parser.add_argument("--show", action="store_true", help="查看当前配置")
    parser.add_argument("--server", type=str, metavar="HOST:PORT", help="设置服务器地址")
    parser.add_argument("--host", type=str, metavar="HOST", help="设置服务器 IP")
    parser.add_argument("--port", type=int, metavar="PORT", help="设置服务器端口")
    parser.add_argument("--mode", type=int, choices=[0, 1, 2, 3], help="设置合成模式")
    parser.add_argument("--ref-audio", type=str, metavar="FILE", help="设置默认参考音频")
    parser.add_argument("--ref-dir", type=str, metavar="DIR", help="设置参考音频目录")
    parser.add_argument("--prompt", type=str, nargs=2, metavar=("TEXT", "LANG"),
                        help="设置提示文本和语言")
    parser.add_argument("--toggle", nargs="?", const="status",
                        choices=["on", "off", "status"], help="语音播报开关")

    args = parser.parse_args()

    has_args = any([
        args.show, args.server, args.host, args.port,
        args.mode is not None, args.ref_audio, args.ref_dir,
        args.prompt, args.toggle is not None,
    ])

    if not has_args:
        interactive()
        sys.exit(0)

    if args.show:
        cmd_show()

    if args.server:
        cmd_set_server(args.server)

    if args.host:
        cfg = load()
        cmd_set_server(args.host, cfg["server"]["port"])

    if args.port:
        cfg = load()
        cmd_set_server(cfg["server"]["host"], args.port)

    if args.mode is not None:
        cmd_set_mode(args.mode)

    if args.ref_audio:
        cmd_set_ref_audio(args.ref_audio)

    if args.ref_dir:
        cmd_set_ref_dir(args.ref_dir)

    if args.prompt:
        cmd_set_prompt(args.prompt[0], args.prompt[1])

    if args.toggle is not None:
        cmd_toggle(args.toggle if args.toggle != "status" else None)

    if not args.show and has_args:
        print()
        cmd_show()
