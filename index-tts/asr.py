import os
import warnings

from faster_whisper import WhisperModel

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCAL_MODEL_PATH = os.path.join(root_dir, 'models', "large-v3")

class WhisperModelSingleton:
    _instance = None
    _model = None

    def __new__(cls, model_size="large-v3", device="cuda"):
        if cls._instance is None:
            cls._instance = super(WhisperModelSingleton, cls).__new__(cls)

            warnings.filterwarnings("ignore", category=FutureWarning)
            warnings.filterwarnings("ignore", category=UserWarning)
            # 如果本地存在模型，则从本地加载
            if os.path.exists(LOCAL_MODEL_PATH):
                print(f"📦 正在从本地加载模型: {LOCAL_MODEL_PATH}")
                cls._model = WhisperModel(
                    model_size_or_path=LOCAL_MODEL_PATH,
                    device=device,
                )
            else:
                print(f"🌐 未找到本地模型，正在从远程下载: {model_size}")
                cls._model = WhisperModel(
                    model_size_or_path=model_size,
                    device=device,
                )
        return cls._instance

    def transcribe(self, audio_path, **kwargs):
        """
        调用 whisper 模型进行语音识别
        :param audio_path: 音频文件路径
        :param kwargs: 其他 transcribe 参数
        :return: segments, info
        """
        segments, info = self._model.transcribe(audio_path, **kwargs)
        segments = list(segments)
        return segments, info
def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"


def get_whisper_model():
    """
    获取单例的 Whisper 模型
    """
    return WhisperModelSingleton()

def process_single_audio(whisper, audio_path, output_srt_path):
    """处理单个音频文件"""
    print(f"🔊 处理音频: {audio_path}")
    segments, _ = whisper.transcribe(audio_path, beam_size=7,language="en", condition_on_previous_text=False, word_timestamps=True)
    generate_srt(segments, output_srt_path)
    return output_srt_path

def generate_srt(segments, output_srt_path):
    with open(output_srt_path, "w", encoding="utf-8") as f:
        index = 1  # 序号从1开始递增

        for segment in segments:
            start_time = segment.start
            end_time = segment.end
            text = segment.text.strip()

            # 判断是否有逗号
            if ',' in text:
                parts = [p.strip() for p in text.split(',') if p.strip()]
                if len(parts) == 0:
                    continue

                # 平均分配时间
                duration = (end_time - start_time) / len(parts)
                times = []

                for i in range(len(parts)):
                    part_start = start_time + i * duration
                    part_end = start_time + (i + 1) * duration
                    times.append((part_start, part_end))

                # 写入多个字幕条目
                for part_text, (part_start, part_end) in zip(parts, times):
                    start = format_timestamp(part_start/0.7)
                    end = format_timestamp(part_end/0.7)

                    f.write(f"{index}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{part_text}\n\n")
                    index += 1
            else:
                # 无逗号，保持原样输出
                start = format_timestamp(segment.start)
                end = format_timestamp(segment.end)

                f.write(f"{index}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")
                index += 1

    print(f"✅ SRT 字幕文件已生成：{output_srt_path}")
