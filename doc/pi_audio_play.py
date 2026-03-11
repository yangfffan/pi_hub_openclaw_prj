#使用pyaudio实现播放
import pyaudio,wave
# 打开我们要播放的文件
wf=wave.open(r"01.wav",'rb')
# 实例化一个PyAudio对象
pa = pyaudio.PyAudio()
# 打开声卡
stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),    # 从wf中获取采样深度
                 channels=wf.getnchannels(),                            # 从wf中获取声道数
                 rate=wf.getframerate(),                                # 从wf中获取采样率
                 output=True)                                           # 设置为输出
count = 0
while count < 8*5:
    audio_data = stream.read(2048)      # 读出声卡缓冲区的音频数据
    record_buf.append(audio_data)       # 将读出的音频数据追加到record_buf列表
    count += 1
    print('*')
# 关闭声卡
stream.close()
pa.terminate()