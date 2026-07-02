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
    python tts_config.py --infer-show           # 查看推理配置
    python tts_config.py --infer-auto           # 自动检测模型并配置
    python tts_config.py --infer-device cuda    # 设置推理设备
    python tts_config.py --infer-init           # 初始化推理配置文件
"""

import argparse
import json
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None

PIPELINE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.expanduser("~/.voice_pipeline")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
TOGGLE_FILE = os.path.expanduser("~/.tts_speak_enabled")

# ── 推理配置路径 ──────────────────────────────────────
INFER_CONFIG_FILE = os.path.join(PIPELINE_DIR, "tts_infer.yaml")
INFER_EXAMPLE_FILE = os.path.join(PIPELINE_DIR, "tts_infer.yaml.example")
GPT_SOVITS_DIR = os.path.join(PIPELINE_DIR, "GPT-SoVITS")
MODELS_DIR = os.path.join(PIPELINE_DIR, "models")

VERSION_CHOICES_INFER = ["v1", "v2", "v2Pro", "v2ProPlus", "v3", "v4"]

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

    # 推理配置状态
    infer_status = "✅ 已配置" if os.path.exists(INFER_CONFIG_FILE) else "⚠️  未配置"

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
    print(f"║  推理配置    │ {infer_status}")
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


# ═══════════════════════════════════════════════════════════
# 推理配置管理 (tts_infer.yaml)
# ═══════════════════════════════════════════════════════════

def _yaml_available():
    """检查 PyYAML 是否可用，不可用则打印提示并返回 False"""
    if yaml is None:
        print("❌ 需要 PyYAML 库来管理推理配置文件")
        print("   请运行: pip install pyyaml")
        return False
    return True


def _load_infer_config():
    """加载 tts_infer.yaml，返回完整 dict；文件不存在返回 None"""
    if not os.path.exists(INFER_CONFIG_FILE):
        return None
    if not _yaml_available():
        return None
    with open(INFER_CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)


def _save_infer_config(config):
    """保存完整 dict 到 tts_infer.yaml"""
    if not _yaml_available():
        return
    with open(INFER_CONFIG_FILE, "w") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _resolve_weight_path(user_path):
    """将用户输入的路径转换为相对于 GPT-SoVITS/ 的路径。

    支持:
    - 绝对路径 → 转换为相对路径 (../...)
    - ~/ 路径 → 展开后转换
    - 已相对于 GPT-SoVITS 的路径 → 保持原样
    - 相对于 pipeline 根目录的路径 → 转换为 ../... 格式
    """
    expanded = os.path.expanduser(user_path)
    if os.path.isabs(expanded):
        return os.path.relpath(expanded, GPT_SOVITS_DIR)
    # 检查是否相对于 pipeline 根目录存在
    candidate = os.path.join(PIPELINE_DIR, expanded)
    if os.path.exists(candidate):
        return os.path.relpath(candidate, GPT_SOVITS_DIR)
    # 假设已经是相对于 GPT-SoVITS 的路径
    return expanded


def _scan_models():
    """扫描 models/ 目录，返回发现的模型文件。

    Returns:
        dict: {
            "gpt": [{"path": "相对路径", "abs": "绝对路径", "name": "文件名"}, ...],
            "sovits": [{"path": "相对路径", "abs": "绝对路径", "name": "文件名"}, ...],
        }
    """
    result = {"gpt": [], "sovits": []}

    gpt_dir = os.path.join(MODELS_DIR, "gpt_weights")
    if os.path.isdir(gpt_dir):
        for root, dirs, files in os.walk(gpt_dir):
            for f in sorted(files):
                if f.endswith(".ckpt"):
                    abs_path = os.path.join(root, f)
                    rel_to_gpt = os.path.relpath(abs_path, GPT_SOVITS_DIR)
                    result["gpt"].append({
                        "path": rel_to_gpt,
                        "abs": abs_path,
                        "name": f,
                    })

    sovits_dir = os.path.join(MODELS_DIR, "sovits_weights")
    if os.path.isdir(sovits_dir):
        for root, dirs, files in os.walk(sovits_dir):
            for f in sorted(files):
                if f.endswith(".pth"):
                    abs_path = os.path.join(root, f)
                    rel_to_gpt = os.path.relpath(abs_path, GPT_SOVITS_DIR)
                    result["sovits"].append({
                        "path": rel_to_gpt,
                        "abs": abs_path,
                        "name": f,
                    })

    return result


def _detect_version():
    """尝试从模型目录名或文件名推断版本，默认 v2ProPlus"""
    # 检查 models/ 子目录名是否包含版本号
    for subdir in ["gpt_weights", "sovits_weights"]:
        full = os.path.join(MODELS_DIR, subdir)
        if os.path.isdir(full):
            for name in os.listdir(full):
                name_lower = name.lower()
                for v in reversed(VERSION_CHOICES_INFER):  # 优先匹配更具体的
                    if v.lower() in name_lower:
                        return v
    return "v2ProPlus"


def _detect_device():
    """尝试检测最佳设备，多层回退:
    1. 直接 import torch (conda 环境内运行时)
    2. nvidia-smi 命令 (有 NVIDIA GPU 驱动)
    3. conda 环境内检测 torch
    4. 默认 cuda (TTS 工具以 GPU 为主，CPU 用户可手动改)
    """
    # 第一层: 直接导入 torch
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    except ImportError:
        pass

    # 第二层: 检查 nvidia-smi
    import subprocess
    try:
        subprocess.run(
            ["nvidia-smi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        return "cuda"
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # 第三层: 通过 conda 环境检测
    for env_name in ["GPTSoVits", "gptsovits"]:
        try:
            result = subprocess.run(
                ["conda", "run", "-n", env_name, "python3", "-c",
                 "import torch; print(torch.cuda.is_available())"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and "True" in result.stdout:
                return "cuda"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # 默认: cuda（TTS 推理极少用 CPU）
    return "cuda"


def cmd_infer_show():
    """显示推理配置中 custom 部分的内容"""
    config = _load_infer_config()
    if config is None:
        print("⚠️  推理配置文件不存在: " + INFER_CONFIG_FILE)
        print("   请运行: python tts_config.py --infer-init")
        return

    custom = config.get("custom", {})
    if not custom:
        print("⚠️  tts_infer.yaml 中没有 [custom] 节")
        return

    print("╔══════════════════════════════════════╗")
    print("║     推理配置 (tts_infer.yaml)        ║")
    print("╠══════════════════════════════════════╣")
    print(f"║  设备        │ {custom.get('device', '?')}")
    print(f"║  半精度      │ {custom.get('is_half', '?')}")
    print(f"║  版本        │ {custom.get('version', '?')}")
    print(f"║  GPT 权重    │ {custom.get('t2s_weights_path', '?')}")
    print(f"║  SoVITS 权重 │ {custom.get('vits_weights_path', '?')}")
    print("╚══════════════════════════════════════╝")


def cmd_infer_device(device):
    """设置推理设备: cuda 或 cpu"""
    if device not in ("cuda", "cpu"):
        print(f"❌ 无效设备: {device}，可选: cuda, cpu")
        return
    config = _load_infer_config()
    if config is None:
        print("⚠️  推理配置文件不存在，请先运行 --infer-init")
        return
    config.setdefault("custom", {})["device"] = device
    _save_infer_config(config)
    print(f"✅ 推理设备已设为: {device}")


def cmd_infer_half(on_off):
    """设置半精度: on/true/yes → True, off/false/no → False"""
    positive = ("on", "true", "yes", "1")
    negative = ("off", "false", "no", "0")
    val = on_off.lower()
    if val in positive:
        is_half = True
    elif val in negative:
        is_half = False
    else:
        print(f"❌ 无效值: {on_off}，可选: on, off")
        return
    config = _load_infer_config()
    if config is None:
        print("⚠️  推理配置文件不存在，请先运行 --infer-init")
        return
    config.setdefault("custom", {})["is_half"] = is_half
    _save_infer_config(config)
    print(f"✅ 半精度已设为: {is_half}")


def cmd_infer_version(version):
    """设置模型版本"""
    if version not in VERSION_CHOICES_INFER:
        print(f"❌ 无效版本: {version}，可选: {', '.join(VERSION_CHOICES_INFER)}")
        return
    config = _load_infer_config()
    if config is None:
        print("⚠️  推理配置文件不存在，请先运行 --infer-init")
        return
    config.setdefault("custom", {})["version"] = version
    _save_infer_config(config)
    print(f"✅ 模型版本已设为: {version}")


def cmd_infer_gpt_weights(path):
    """设置 GPT 权重路径 (.ckpt)"""
    resolved = _resolve_weight_path(path)
    config = _load_infer_config()
    if config is None:
        print("⚠️  推理配置文件不存在，请先运行 --infer-init")
        return
    config.setdefault("custom", {})["t2s_weights_path"] = resolved
    _save_infer_config(config)
    print(f"✅ GPT 权重路径已设为: {resolved}")


def cmd_infer_sovits_weights(path):
    """设置 SoVITS 权重路径 (.pth)"""
    resolved = _resolve_weight_path(path)
    config = _load_infer_config()
    if config is None:
        print("⚠️  推理配置文件不存在，请先运行 --infer-init")
        return
    config.setdefault("custom", {})["vits_weights_path"] = resolved
    _save_infer_config(config)
    print(f"✅ SoVITS 权重路径已设为: {resolved}")


def cmd_infer_auto():
    """自动检测模型文件并配置推理参数"""
    if not _yaml_available():
        return

    # 确保配置文件存在
    if not os.path.exists(INFER_CONFIG_FILE):
        cmd_infer_init()

    models = _scan_models()
    gpt_models = models["gpt"]
    sovits_models = models["sovits"]

    if not gpt_models:
        print("⚠️  未找到 GPT 权重文件 (.ckpt)")
        print(f"   请将 .ckpt 文件放入: {MODELS_DIR}/gpt_weights/")
    if not sovits_models:
        print("⚠️  未找到 SoVITS 权重文件 (.pth)")
        print(f"   请将 .pth 文件放入: {MODELS_DIR}/sovits_weights/")

    if not gpt_models and not sovits_models:
        print("❌ 未发现任何模型文件，无法自动配置")
        return

    print("→ 自动检测模型文件...")
    print()

    # 选择模型文件
    if gpt_models:
        if len(gpt_models) == 1:
            gpt_path = gpt_models[0]["path"]
            print(f"  GPT 权重:    {gpt_models[0]['name']}")
        else:
            print(f"  发现 {len(gpt_models)} 个 GPT 权重文件:")
            for i, m in enumerate(gpt_models, 1):
                print(f"    [{i}] {m['name']}")
            gpt_path = gpt_models[0]["path"]
            print(f"  → 已选择: {gpt_models[0]['name']}")
    else:
        gpt_path = None

    if sovits_models:
        if len(sovits_models) == 1:
            sovits_path = sovits_models[0]["path"]
            print(f"  SoVITS 权重: {sovits_models[0]['name']}")
        else:
            print(f"  发现 {len(sovits_models)} 个 SoVITS 权重文件:")
            for i, m in enumerate(sovits_models, 1):
                print(f"    [{i}] {m['name']}")
            sovits_path = sovits_models[0]["path"]
            print(f"  → 已选择: {sovits_models[0]['name']}")
    else:
        sovits_path = None

    version = _detect_version()
    device = _detect_device()
    print(f"  检测版本:    {version}")
    print(f"  检测设备:    {device}")
    print()

    # 写入配置
    config = _load_infer_config() or {}
    custom = config.setdefault("custom", {})

    if gpt_path:
        custom["t2s_weights_path"] = gpt_path
    if sovits_path:
        custom["vits_weights_path"] = sovits_path
    custom["version"] = version
    custom["device"] = device
    custom["is_half"] = (device == "cuda")

    _save_infer_config(config)

    print("✅ 推理配置已自动生成！")
    print()
    cmd_infer_show()


def cmd_infer_init():
    """从示例文件初始化 tts_infer.yaml"""
    if os.path.exists(INFER_CONFIG_FILE):
        print(f"⚠️  推理配置文件已存在: {INFER_CONFIG_FILE}")
        print("   如需重新初始化，请先删除该文件")
        return

    if not os.path.exists(INFER_EXAMPLE_FILE):
        print(f"❌ 示例文件不存在: {INFER_EXAMPLE_FILE}")
        return

    # 复制示例文件
    with open(INFER_EXAMPLE_FILE, "r") as src:
        content = src.read()

    # 追加预设版本配置
    if "v1:" not in content:
        content += _generate_preset_sections()

    with open(INFER_CONFIG_FILE, "w") as dst:
        dst.write(content)

    print(f"✅ 推理配置文件已创建: {INFER_CONFIG_FILE}")
    print("   接下来请运行: python tts_config.py --infer-auto")


def _generate_preset_sections():
    """生成 v1-v4 预设模型路径（相对于 GPT-SoVITS/）"""
    return """
v1:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt
  version: v1
  vits_weights_path: GPT_SoVITS/pretrained_models/s2G488k.pth
v2:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt
  version: v2
  vits_weights_path: GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth
v2Pro:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/s1v3.ckpt
  version: v2Pro
  vits_weights_path: GPT_SoVITS/pretrained_models/v2Pro/s2Gv2Pro.pth
v2ProPlus:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/s1v3.ckpt
  version: v2ProPlus
  vits_weights_path: GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth
v3:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/s1v3.ckpt
  version: v3
  vits_weights_path: GPT_SoVITS/pretrained_models/s2Gv3.pth
v4:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cpu
  is_half: false
  t2s_weights_path: GPT_SoVITS/pretrained_models/s1v3.ckpt
  version: v4
  vits_weights_path: GPT_SoVITS/pretrained_models/gsv-v4-pretrained/s2Gv4.pth
"""


# ── 推理配置子菜单 ──────────────────────────────────

def interactive_infer():
    """推理配置交互式子菜单"""
    while True:
        config = _load_infer_config()
        if config is None:
            print("\n⚠️  推理配置文件不存在")
            print("  [I] 从示例初始化")
            print("  [0] 返回主菜单")
            try:
                choice = input("\n请选择 > ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\n")
                break
            if choice == "I":
                cmd_infer_init()
                continue
            elif choice == "0":
                break
            else:
                print("  ❌ 未知选项")
                continue

        custom = config.get("custom", {})
        print()
        print("╔══════════════════════════════════════╗")
        print("║     推理配置 (tts_infer.yaml)        ║")
        print("╠══════════════════════════════════════╣")
        print(f"║  设备        │ {custom.get('device', '(未设置)')}")
        print(f"║  半精度      │ {custom.get('is_half', '(未设置)')}")
        print(f"║  版本        │ {custom.get('version', '(未设置)')}")
        gpt = custom.get('t2s_weights_path', '') or '(未设置)'
        sovits = custom.get('vits_weights_path', '') or '(未设置)'
        # 截断过长路径
        if len(gpt) > 40:
            gpt = "…" + gpt[-37:]
        if len(sovits) > 40:
            sovits = "…" + sovits[-37:]
        print(f"║  GPT 权重    │ {gpt}")
        print(f"║  SoVITS 权重 │ {sovits}")
        print("╚══════════════════════════════════════╝")
        print()
        print("  [1] 修改设备 (cuda/cpu)")
        print("  [2] 切换半精度")
        print("  [3] 修改版本")
        print("  [4] 设置 GPT 权重路径")
        print("  [5] 设置 SoVITS 权重路径")
        print("  [A] 自动检测模型")
        print("  [0] 返回主菜单")
        print()

        try:
            choice = input("请选择 > ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if choice == "1":
            current = custom.get("device", "cuda")
            d = input(f"  设备 [{current}] (cuda/cpu) > ").strip().lower()
            if d in ("cuda", "cpu"):
                cmd_infer_device(d)
            elif d:
                print("  ❌ 无效设备，可选: cuda, cpu")
            print()

        elif choice == "2":
            current = custom.get("is_half", True)
            label = "on" if current else "off"
            d = input(f"  半精度 [{label}] (on/off) > ").strip().lower()
            if d in ("on", "off"):
                cmd_infer_half(d)
            elif d:
                print("  ❌ 无效值，可选: on, off")
            print()

        elif choice == "3":
            current = custom.get("version", "v2ProPlus")
            print(f"  可选版本: {', '.join(VERSION_CHOICES_INFER)}")
            d = input(f"  版本 [{current}] > ").strip()
            if d in VERSION_CHOICES_INFER:
                cmd_infer_version(d)
            elif d:
                print(f"  ❌ 无效版本，可选: {', '.join(VERSION_CHOICES_INFER)}")
            print()

        elif choice == "4":
            current = custom.get("t2s_weights_path", "")
            d = input(f"  GPT 权重路径 [{current}] > ").strip()
            if d:
                cmd_infer_gpt_weights(d)
            print()

        elif choice == "5":
            current = custom.get("vits_weights_path", "")
            d = input(f"  SoVITS 权重路径 [{current}] > ").strip()
            if d:
                cmd_infer_sovits_weights(d)
            print()

        elif choice == "A":
            cmd_infer_auto()
            print()
            input("按回车继续...")

        elif choice == "0":
            break

        else:
            print("  ❌ 未知选项")
            print()


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
        print("  [7] 配置推理参数 (tts_infer.yaml)")
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

        elif choice == "7":
            interactive_infer()
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

    # ── 推理配置参数 ──
    parser.add_argument("--infer-show", action="store_true", help="查看推理配置")
    parser.add_argument("--infer-device", type=str, choices=["cuda", "cpu"],
                        metavar="DEVICE", help="设置推理设备: cuda 或 cpu")
    parser.add_argument("--infer-half", type=str, metavar="ON_OFF",
                        help="设置半精度: on 或 off")
    parser.add_argument("--infer-version", type=str, choices=VERSION_CHOICES_INFER,
                        metavar="VER", help=f"设置模型版本: {', '.join(VERSION_CHOICES_INFER)}")
    parser.add_argument("--infer-gpt-weights", type=str, metavar="PATH",
                        help="设置 GPT 权重路径 (.ckpt)")
    parser.add_argument("--infer-sovits-weights", type=str, metavar="PATH",
                        help="设置 SoVITS 权重路径 (.pth)")
    parser.add_argument("--infer-auto", action="store_true", help="自动检测模型并配置")
    parser.add_argument("--infer-init", action="store_true", help="初始化推理配置文件")

    args = parser.parse_args()

    has_args = any([
        args.show, args.server, args.host, args.port,
        args.mode is not None, args.ref_audio, args.ref_dir,
        args.prompt, args.toggle is not None,
        args.infer_show, args.infer_device, args.infer_half,
        args.infer_version, args.infer_gpt_weights, args.infer_sovits_weights,
        args.infer_auto, args.infer_init,
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

    # ── 推理配置命令 ──
    if args.infer_show:
        cmd_infer_show()

    if args.infer_device:
        cmd_infer_device(args.infer_device)

    if args.infer_half:
        cmd_infer_half(args.infer_half)

    if args.infer_version:
        cmd_infer_version(args.infer_version)

    if args.infer_gpt_weights:
        cmd_infer_gpt_weights(args.infer_gpt_weights)

    if args.infer_sovits_weights:
        cmd_infer_sovits_weights(args.infer_sovits_weights)

    if args.infer_auto:
        cmd_infer_auto()

    if args.infer_init:
        cmd_infer_init()

    if not args.show and has_args:
        print()
        cmd_show()
