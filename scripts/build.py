#!/usr/bin/env python

import argparse

from index import load, remotionInit, remotionPreview, syncEnv

def main():
    parser = argparse.ArgumentParser(
        prog='Scrolly',
        description='the ultimate karaoke video workflow',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("filename", help="path to music file", type=str)
    parser.add_argument(
        "-d", "--darkMode",
        help="gives your video a dark theme",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "-p", "--preview",
        help="initializes remotion and shows a preview of your video in the browser",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "-s", "--skipSep", "--skip",
        help="skips the separation step. Assumes you have stems in the scrolly_video/../assets folder.",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "-t", "--transcribe",
        help="""transcribe lyrics from audio using Whisper instead of fetching from Musixmatch.
             Note that the latter requires a Musixmatch Token""",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "-u", "--uri", "--url",
        help="Spotify URI for your song, to help fetch lyrics",
        default="",
        type=str,
    )
    args = parser.parse_args()
    syncEnv()
    load(args)
    if args.preview:
        remotionInit()
        remotionPreview()

if __name__ == "__main__":
    main()