from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from json import dump
from os import path, walk, makedirs

import whisper_timestamped as whisper
from Pylette import extract_colors
from mutagen import File

from app.separateAudio import separate

darkMode = True

mimeExt = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
}

root = path.abspath("../scrolly_video/public/assets")

def to_code(color):
    return f"rgb({color[0]}, {color[1]}, {color[2]})"


def _getColors(audio: File, voc_start=0, voc_end=30):
    data = audio['APIC:Cover'].data
    image = BytesIO(data)
    colors = extract_colors(image, palette_size=10)
    colors = [to_code(color.rgb) for color in colors]
    if darkMode:
        colors.reverse()
    print(f"{audio['TIT2'].text[0]}: Palette extracted")
    return {
        "txt": colors[0],
        "bg": colors[9],
        "shadow": colors[6],
        "visual": colors[3],
        "voc_start": voc_start,
        "voc_end": voc_end,
    }


def sendMetadata(audio: File, bounds: dict[str, float]):
    colors = _getColors(audio)
    config = {
        'album': audio['TALB'].text[0],
        'artists': [audio[k].text[0] for k in ['TPE1', 'TOPE'] if k in audio],
        'title': audio['TIT2'].text[0],
        'length': audio.info.length,
        'colors': colors,
        **bounds
    }
    with open(path.join(root, 'temp.json'), "w+") as fp:
        fp.seek(0)
        dump(config, fp, indent=4)
        fp.truncate()
    fp.close()
    print(f"{audio['TIT2'].text[0]}: Metadata sent")


def sendCover(audio: File):
    cover = audio['APIC:Cover']
    ext = mimeExt[cover.mime]
    with open(path.join(root, f"temp.{ext}"), "wb+") as fp:
        fp.seek(0)
        fp.write(cover.data)
        fp.truncate()
    fp.close()
    print(f"{audio['TIT2'][0]}: Cover sent")


def to_timestamp(seconds):
    minutes = int(seconds / 60)
    seconds %= 60
    return "{:0>2}:{:0>5.2f}".format(minutes, seconds)


def splitTranscribe(audio: File) -> dict[str, float]:
    separate(audio.filename, root)
    print(f"{audio['TIT2'][0]}: Separated")
    audio_w = whisper.load_audio(path.join(root, 'audio', 'vocals.wav'))
    model = whisper.load_model('medium.en', device='cuda')
    result = whisper.transcribe(model, audio_w, language="en", vad=True)

    with open(path.join(root, 'temp.lrc'), "w+") as fp:
        # dump(result, fp)
        fp.seek(0)
        for line in result["segments"]:
            fp.write(f"[{to_timestamp(line['words'][0]['start'])}]")
            for word in line["words"]:
                fp.write(f"{word['text']} <{to_timestamp(word['end'])}>")
            fp.write("\n")
        fp.truncate()

    print(f"{audio['TIT2'][0]}: Transcribed")
    return {
        "voc_start": result["segments"][0]['words'][0]['start'],
        "voc_end": result["segments"][-1]['words'][-1]['end']
    }


def main():
    makedirs(root, exist_ok=True)
    audio = None
    source = '..\\raw'
    for file in next(walk(source))[2]:
        if file.endswith(".mp3") or file.endswith(".wav"):
            audio = File(path.join(source, file))
            break

    if not audio:
        print("No music file found")
        return

    with ThreadPoolExecutor(max_workers=3) as e:
        print(f"{audio['TIT2'][0]}: Starting tasks")
        e.submit(sendCover, audio)
        fut = e.submit(splitTranscribe, audio)
        e.shutdown(wait=True)

    sendMetadata(audio, fut.result())

    print(f"{audio['TIT2'][0]}: All tasks completed")


if __name__ == "__main__":
    main()
