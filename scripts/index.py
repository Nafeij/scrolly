import logging
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from json import dump
from os import path, makedirs, getenv
from pathlib import Path
from subprocess import run
from typing import TypedDict
from shutil import copyfile

import whisper_timestamped as whisper
from Pylette import extract_colors
from dotenv import load_dotenv
from mutagen import File

from MxLRC import mxlrc
from separateAudio import separate

MIME_EXTS = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
}

COVERS = [
    'APIC:',
    'APIC:Cover',
    'APIC:Cover (front)',
    'APIC:Cover (back)',
]

root = Path(path.abspath(__file__)).parent.parent
remotion_root = root.joinpath("scrolly_video")
asset_root = path.join(remotion_root, "public", "assets")


def to_code(color):
    return f"rgb({color[0]}, {color[1]}, {color[2]})"


def _getColors(name : str, data : bytes, darkMode: bool):
    image = BytesIO(data)
    colors = extract_colors(image, palette_size=10, sort_mode="luminance")
    colors = [to_code(color.rgb) for color in colors]
    if darkMode:
        colors.reverse()
    logging.info(f"{name}: Palette extracted")
    return {
        "txt": colors[0],
        "bg": colors[9],
        "shadow": colors[6],
        "visual": colors[3],
    }


def fetch_artists(audio: File):
    return [audio[k].text[0] for k in ['TPE1', 'TOPE'] if k in audio]


def sendMetadata(audio: File, colorData : bytes, bounds: dict[str, float], args: Namespace):
    colors = _getColors(audio['TIT2'].text[0], colorData, args.darkMode)
    config = {
        'album': audio['TALB'].text[0],
        'artists': fetch_artists(audio),
        'title': audio['TIT2'].text[0],
        'length': audio.info.length,
        'colors': colors,
        **bounds
    }
    with open(path.join(asset_root, 'temp.json'), "w+") as fp:
        fp.seek(0)
        dump(config, fp, indent=4)
        fp.truncate()
    fp.close()
    logging.info(f"{audio['TIT2'].text[0]}: Metadata sent")


def sendCover(audio: File):
    cover = None
    for key in COVERS:
        if key in audio:
            cover = audio[key]
            break
    if cover is None:
        logging.warning(f"{audio['TIT2'].text[0]}: Cover not found")
        return
    ext = MIME_EXTS[cover.mime]
    with open(path.join(asset_root, f"temp.{ext}"), "wb+") as fp:
        fp.seek(0)
        fp.write(cover.data)
        fp.truncate()
    fp.close()
    logging.info(f"{audio['TIT2'][0]}: Cover sent")
    return cover.data


class Word(TypedDict):
    start: float
    text: str
    end: float


def timestamp(seconds):
    minutes = int(seconds / 60)
    seconds %= 60
    return "{:0>2}:{:0>5.2f}".format(minutes, seconds)

def seconds(line: dict[str, int]):
    return line['minutes'] * 60 + line['seconds'] + line['hundredths'] / 100

class WordList(object):
    def __init__(self, wordlist: list[list[Word]]):
        self.wordlist = wordlist
        self.start = wordlist[0][0]['start']
        self.end = wordlist[-1][-1]['end']

    def __str__(self) -> str:
        return f"{self.wordlist}\nStart: {self.start}\nEnd: {self.end}\n"

    def write_lrc(self):
        with open(path.join(asset_root, 'temp.lrc'), "w+") as fp:
            # dump(result, fp)
            fp.seek(0)
            for line in self.wordlist:
                fp.write(f"[{timestamp(line[0]['start'])}]")
                for word in line:
                    fp.write(f"{word['text']} <{timestamp(word['end'])}>")
                fp.write("\n")
            fp.truncate()


def fromMM(audio: File, args: Namespace):
    load_dotenv()
    MX_TOKEN = getenv("MX_TOKEN", default="2203269256ff7abcb649269df00e14c833dbf4ddfb5b36a1aae8b0")
    mx = mxlrc.Musixmatch(MX_TOKEN)
    song = mxlrc.Song(
        artist=fetch_artists(audio)[0],
        title=audio['TIT2'][0],
        album=audio['TALB'].text[0],
        uri=args.uri
    )
    body = mx.find_lyrics(song)
    if body is None:
        logging.warning(f"Failed to find song {audio['TIT2'][0]} @ {args.uri}")
        return None
    song.update_info(body)
    logging.info(f"Song found: {song}")
    logging.info(f"Searching lyrics: {song}")
    mx.get_synced(song, body)

    lyrics = song.subtitles
    if lyrics is None:
        logging.warning(f"Synced lyrics not found for song {audio['TIT2'][0]} @ {args.uri}")
    last = len(lyrics) - 1
    templist : list[list[Word]] = [[Word(start=seconds(line), text=line['text'], end=seconds(lyrics[i + 1]))]
                                   for i, line in enumerate(lyrics) if i < last]
    lastL = lyrics[last]
    templist.append([Word(start=seconds(lastL), text=lastL['text'], end=audio.info.length)])
    return WordList(templist)


def split_transcribe(audio: File, args: Namespace) -> dict[str, float]:
    if not args.skipSep:
        separate(audio.filename, asset_root)
        # separate.main(["--mp3", "--two-stems", "vocals", "-n", "mdx_extra", "track with space.mp3"])
        logging.info(f"{audio['TIT2'][0]}: Separated")
    if args.transcribe:
        audio_w = whisper.load_audio(path.join(asset_root, 'audio', 'vocals.wav'))
        model = whisper.load_model('medium.en', device='cuda')
        result = whisper.transcribe(model, audio_w, language="en", vad=True)

        wordlist = WordList([[Word(start=word['start'], text=word['text'], end=word['end'])
                              for word in line["words"]] for line in result["segments"]])
    else:
        wordlist = fromMM(audio, args)
        if wordlist is None:
            return {"voc_start": 0, "voc_end": audio.info.length}
    wordlist.write_lrc()
    logging.info(f"{audio['TIT2'][0]}: Transcribed")
    return {
        "voc_start": wordlist.start,
        "voc_end": wordlist.end
    }


def remotionInit():
    run("npm install", shell=True, cwd=remotion_root, check=True)


def remotionPreview():
    run("npx remotion preview", shell=True, cwd=remotion_root, check=True)

def syncEnv():
    copyfile(root.joinpath(".env"), remotion_root.joinpath(".env"))

def load(args):
    audioPath = args.filename
    audio = File(audioPath)

    makedirs(asset_root, exist_ok=True)

    with ThreadPoolExecutor(max_workers=3) as e:
        logging.info(f"{audio['TIT2'][0]}: Starting tasks")
        futCover =  e.submit(sendCover, audio)
        futStartEnd = e.submit(split_transcribe, audio, args)
        e.shutdown(wait=True)

    sendMetadata(audio, futCover.result(), futStartEnd.result(), args)

    logging.info(f"{audio['TIT2'][0]}: All tasks completed")
