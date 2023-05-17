<p align="center">
  <img src=".docs/assets/intro_1.png" width="80%" />
</p>
<p align="center">
  <img src=".docs/assets/scroll_2.png" width="80%" />
</p>
<p align="center">
  <img src=".docs/assets/trans_3.gif" width="80%" />
</p>

[Full video demo](https://youtu.be/8w8nkJMx9L4)

# [WIP] Scrolly

## The ultimate karaoke video workflow

To run:

    python scrolly/build.py

&nbsp;

    usage: Scrolly [-h] [-d | --darkMode | --no-darkMode] [-p | --preview | --no-preview]
                   [-s | --skipSep | --no-skipSep | --skip | --no-skip] [-t | --transcribe | --no-transcribe] [-u URI]
                   filename

    the ultimate karaoke video workflow

    positional arguments:
      filename              path to music file

    options:
      -h, --help            show this help message and exit
      -d, --darkMode, --no-darkMode
                            gives your video a dark theme (default: False)
      -p, --preview, --no-preview
                            initializes remotion and shows a preview of your video in the browser (default: False)
      -s, --skipSep, --no-skipSep, --skip, --no-skip
                            skips the separation step. Assumes you have stems in the scrolly_video/../assets folder.
                            (default: False)
      -t, --transcribe, --no-transcribe
                            transcribe lyrics from audio using Whisper instead of fetching from Musixmatch. Note that the
                            latter requires a Musixmatch Token (default: False)
      -u URI, --uri URI, --url URI
                            Spotify URI for your song, to help fetch lyrics (default: )
