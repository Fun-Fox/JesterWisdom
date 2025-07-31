import glob
import os
import random

import pandas as pd
import asyncio

from tts import init_tts
from asr import generate_srt, get_whisper_model
from loguru import logger
from doubao_rpa import image_to_image_start

root_dir = os.path.dirname(os.path.abspath(__file__))


def read_excel_data(excel_path):
    """
    读取 Excel 文件中的内容。

    :param excel_path: Excel 文件的路径
    :return: 包含 "英文翻译" 和 "中文句子" 的 DataFrame
    """
    df = pd.read_excel(excel_path)
    return df[["英文翻译", "中文句子"]]


def main():
    tts, i18n = init_tts()
    # 读取 Excel 数据
    excel_path = os.path.join(root_dir, "assets", "鸡汤.xlsx")
    df = read_excel_data(excel_path)

    start_row = 0
    end_row = 20

    for idx, row in df[start_row:end_row].iterrows():
        english_text = row["英文翻译"]
        # english_text = row["中文句子"]
        chinese_text = row["中文句子"]

        # 创建以行号命名的输出目录
        output_dir = os.path.join(root_dir, "output", f"row_{idx + 1}")
        os.makedirs(output_dir, exist_ok=True)

        # TTS 生成音频
        speaker_audio_path = os.path.join(root_dir, "assets", "小丑音频-1.MP3")
        tts_audio_tmp_output_path = os.path.join(output_dir, f"tts_audio_{idx + 1}.wav")
        tts.infer_fast(speaker_audio_path, english_text, tts_audio_tmp_output_path)

        # 图像生成
        image_nums = 6
        prompt = f"""参考这个小丑角色图片，生成{image_nums}张16:9的图。
        - 角色主体镜头由：全景 → 中景-> 中近景 → 近景 →特写->  极特写
        - 风格要与参考图风格保持一致
        - 多图间人物风格保持一致
        - 场景风格保持一致
        - 图片中不允许出现文字
        - 注意需要深度结合以下内容的意境：
        '{chinese_text}'
        """
        reference_images_pattern = os.path.join(root_dir, "assets", "小丑主体参考图*.png")
        reference_images = glob.glob(reference_images_pattern)

        # 随机选择一张参考图
        reference_image_path = random.choice(reference_images)

        asyncio.run(
            image_to_image_start(logger, [reference_image_path], prompt, output_dir, image_nums, sleep_time=60000,
                                 enable_download_image=True)
        )

        # Whisper 转录音频并生成 SRT
        whisper = get_whisper_model()
        segments, _ = whisper.transcribe(tts_audio_tmp_output_path, beam_size=7, language="en",
                                         condition_on_previous_text=False, word_timestamps=True)
        output_srt_path = os.path.join(output_dir, "output.srt")
        generate_srt(segments, output_srt_path)

        print(f"🔊 处理音频: {tts_audio_tmp_output_path}")


if __name__ == "__main__":
    main()
