import os
import sys
from os import path

import torch
import torchaudio
import multiprocessing as mp
import subprocess
from demucs.audio import AudioFile, convert_audio, save_audio
from demucs import pretrained
from demucs.apply import apply_model

model = pretrained.get_model('htdemucs_ft')
device = "cuda"
model.to(device)
sample_rate = model.samplerate
model.zero_grad()
model.eval()

def load_track(track, audio_channels, samplerate):
    errors = {}
    wav = None
    try:
        wav = AudioFile(track).read(
            streams=0,
            samplerate=samplerate,
            channels=audio_channels)
    except FileNotFoundError:
        errors['ffmpeg'] = 'FFmpeg is not installed.'
    except subprocess.CalledProcessError:
        errors['ffmpeg'] = 'FFmpeg could not read the file.'
    if wav is None:
        try:
            wav, sr = torchaudio.load(str(track))
        except RuntimeError as err:
            errors['torchaudio'] = err.args[0]
        else:
            wav = convert_audio(wav, sr, samplerate, audio_channels)
    if wav is None:
        print(f"Could not load file {track}. "
              "Maybe it is not a supported file format? ")
        for backend, error in errors.items():
            print(f"When trying to load using {backend}, got the following error: {error}")
        sys.exit(1)
    return wav

@torch.no_grad()
def separate(track, root):
    print("Separating track")
    wav = load_track(track, model.audio_channels, model.samplerate)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()

    # sources = separate_sources(
    #     model,
    #     wav[None],
    #     device=device,
    #     segment=segment,
    #     overlap=overlap,
    # )[0]
    sources = apply_model(model, wav[None], device=device, progress=True,
                          num_workers=mp.cpu_count())[0]
    sources = sources * ref.std() + ref.mean()

    sources = list(sources)
    kwargs = {
        'samplerate': model.samplerate,
        'bitrate': 320,
        'clip': "rescale",
        'as_float': True,
        'bits_per_sample': 16,
    }
    os.makedirs(path.join(root, "audio"), exist_ok=True)
    save_audio(sources.pop(model.sources.index("vocals")), path.join(root, "audio", "vocals.wav"), **kwargs)
    other_stem = torch.zeros_like(sources[0])
    for i in sources:
        other_stem += i
    save_audio(other_stem, path.join(root, "audio", "no_vocals.wav"), **kwargs)
    print("Done separating track")