"""This is my personal collection of Python scripts, built up over many years of solving problems most people don't care about (or don't *know* they care about… until they discover my scripts).

## Script List

### Meta Scripts

- [**dsver**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/dsver.py): Show installed versions of my packages and flag deprecated packages.
- [**lsbin**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/lsbin.py): Lists executable files and their descriptions based on docstrings. What you're looking at now.

### Development Scripts

- [**changelogs**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/dev/update_changelog.py): Update CHANGELOG.md with a new version and automatically manage links.
- [**checkdeps**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/dev/check_dependencies.py): Check all interdependencies between dsbin and dsbin.
- [**checkimports**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/dev/check_imports.py): Check for circular imports in a Python project.
- [**codeconfigs**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/dev/code_configs/code_configs.py): Download configs for coding tools and compare against local versions.
- [**impactanalyzer**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/dev/impact_analyzer.py): Analyze the impact of changes in repositories and their dependencies.
- [**packageanalyzer**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/dev/package_analyzer.py): Analyze package dependencies and generate an import graph.
- [**pybumper**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/pybumper/main.py): Version management tool for Python projects.
- [**reporun**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/dev/reporun.py): Package management utility for working with multiple Poetry projects.
- [**tagreplace**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/dev/tag_replace.py): Replace an existing Git tag with a new tag name and description.

### File Management

- [**backupsort**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/files/backupsort.py): Sorts saved backup files by adding a timestamp suffix to the filename.
- [**bigfiles**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/files/bigfiles.py): Finds the top N file types in a directory by cumulative size.
- [**dupefinder**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/files/dupefinder.py): Find duplicate files in a directory.
- [**foldermerge**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/files/foldermerge.py): Tries to merge two folders, accounting for duplicates and name conflicts.
- [**rsyncer**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/files/rsyncer.py): Build an rsync command interactively.
- [**workcalc**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/workcalc/main.py): Calculate how much time went into a project.

### Text Processing

- [**pycompare**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/text/pycompare.py): Compare two lists and output common/unique elements.
- [**w11renamer**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/text/w11renamer.py): Generates non-stupid filenames for Windows 11 ISO files from stupid ones.

### System Tools

- [**changehostname**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/tools/changehostname.py): Changes the system hostname in all the relevant places.
- [**dockermounter**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/tools/dockermounter.py): Checks to see if mount points are mounted, and act accordingly.
- [**dsservice**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/tools/dsservice.py): Main function for managing systemd services.
- [**dsupdater**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/updater/updater.py): Comprehensive update installer for Linux and macOS.
- [**dsupdater-install**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/updater/install.py): Entry point for installer.
- [**envsync**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/tools/envsync.py): Synchronize two .env files by merging their content.
- [**ssh-tunnel**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/tools/ssh_tunnel.py): Create or kill an SSH tunnel on the specified port.

### macOS-Specific Scripts

- [**dmg-encrypt**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/mac/dmg_encrypt.py): Encrypts DMG files with AES-256 encryption.
- [**dmgify**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/mac/dmgify.py): Creates DMG files from folders, with specific handling for Logic projects.
- [**netreset**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/mac/netreset.py): macOS network reset script.
- [**setmag**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/mac/setmag.py): Set MagSafe light according to power status.
- [**timestamps**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/mac/timestamps.py): Quick and easy timestamp getting/setting for macOS.

### Music Scripts

- [**aif2wav**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/music/awa.py), [**wav2aif**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/music/awa.py): Convert AIFF to WAV or WAV to AIFF, with optional Logic metadata.
- [**alacrity**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/music/alacrity.py): Converts files in a directory to ALAC, with additional formats and options.
- [**hpfilter**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/music/hpfilter.py): Apply a highpass filter to cut bass frequencies for HomePod playback.
- [**metacopy**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/music/metacopy.py): Copy audio metadata from a known file to a new file.
- [**mp3ify**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/music/mp3ify.py): Converts files to MP3.
- [**mshare**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/music/mshare.py): A script for sharing music bounces in a variety of formats.
- [**pybounce**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/pybounce/main.py): Uploads audio files to a Telegram channel.
- [**rmp3**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/music/rmp3.py): Removes MP3 files if there is an AIFF or WAV file with the same name.
- [**wpmusic**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/wpmusic/main.py): Uploads and replaces song remixes on WordPress.

### Logic Pro Scripts

- [**bipclean**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/logic/bipclean.py): Identify and delete recently created AIFF files (default 2 hours).
- [**bouncefiler**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/logic/bouncefiler.py): Sort files into folders based on filename suffix.
- [**bounceprune**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/logic/bounceprune.py): Prunes and consolidates bounces from Logic projects.
- [**bounces**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/logic/bounces.py): CLI tool for working with Logic bounce files using BounceParser.
- [**oldprojects**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/logic/oldprojects.py): Moves old Logic projects out of folders then deletes empty folders.

### Other Media Scripts

- [**ffgif**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/media/ffgif.py): Converts a video file to a GIF using ffmpeg.
- [**fftrim**](https://github.com/dannystewart/dsbin/blob/main/src/dsbin/media/fftrim.py): Use ffmpeg to trim a video file without re-encoding.
"""  # noqa: D415, W505
