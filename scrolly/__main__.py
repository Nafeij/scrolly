import argparse

from index import load, remotionInit, remotionPreview


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("filename", help="path to music file", type=str)
    parser.add_argument(
        "--darkMode",
        help="set to make it light text on a dark background",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--display",
        help="launch remotion to preview the video immediately",
        action=argparse.BooleanOptionalAction,
    )
    args = parser.parse_args()

    load(args.filename, args.darkMode)

    if args.display:
        remotionInit()
        remotionPreview()

if __name__ == "__main__":
    main()