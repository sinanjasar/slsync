# slsync

slsync monitors your specified download folder(s) for new files. it extracts zip files, recursively filters audio files with your chosen extensions, converts them to alac, and moves them to your music library. if artwork is missing, it’ll embed any included images or try to fetch artwork from the web.

## installation

clone the repo and run:
```sh
bash setup.sh
```

## usage

start monitoring:
```sh
slsync
```

## requirements

- macos

## setup script

- creates python venv
- installs dependencies
- creates symlink
