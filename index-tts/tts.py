import os
import warnings
import sys

import torch

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def singleton(func):
    instances = {}

    def wrapper(*args, **kwargs):
        if 'instance' not in instances:
            instances['instance'] = func(*args, **kwargs)
        return instances['instance']

    return wrapper


@singleton
def init_tts():
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning)

    from indextts.infer import IndexTTS
    from tools.i18n.i18n import I18nAuto
    i18n = I18nAuto(language="zh_CN")
    # 自动判断是否支持 CUDA
    use_cuda = torch.cuda.is_available()
    if use_cuda:
        print("🎮 CUDA 可用，使用 GPU 加载模型")
        device = "cuda:0"
    else:
        print("☁️ CUDA 不可用，使用 CPU 加载模型")
        device = "cpu"
    try:
        tts = IndexTTS(
            model_dir=os.path.join(root_dir, "index-tts/checkpoints"),
            cfg_path=os.path.join(root_dir, "index-tts/checkpoints/config.yaml"),
            device=device,
            use_cuda_kernel=use_cuda  # 如果有 CUDA 才使用加速内核
        )
    except Exception as e:
        print(f"⚠️ 使用指定设备加载失败: {e}，尝试使用默认设备重新加载...")
        # 再次兜底
        fallback_device = "cpu"
        tts = IndexTTS(
            model_dir=os.path.join(root_dir, "index-tts/checkpoints"),
            cfg_path=os.path.join(root_dir, "index-tts/checkpoints/config.yaml"),
            device=fallback_device,
            use_cuda_kernel=False
        )

    return tts, i18n



