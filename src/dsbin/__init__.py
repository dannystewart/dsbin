"""This is my personal collection of Python scripts, built up over many years of solving problems most people don't care about (or don't *know* they care about… until they discover my scripts).

## Script List

### Meta Scripts

- **dsver**: Show installed versions of my packages.
- **lsbin**: Lists executable files and their descriptions based on docstrings. What you're looking at now.

### File Management

- **backupsort**: Sorts saved backup files by adding a timestamp suffix to the filename.
- **bigfiles**: Finds the top N file types in a directory by cumulative size.
- **dupefinder**: Find duplicate files in a directory.
- **fml**: Uploads a file to Fastmail's file storage using WebDAV.
- **foldermerge**: Tries to merge two folders, accounting for duplicates and name conflicts.
- **rsyncer**: Build an rsync command interactively.
- **workcalc**: Calculate how much time went into a project.

### Text Processing Scripts

- **pycompare**: Compare two lists and output common/unique elements.
- **w11renamer**: Generates non-stupid filenames for Windows 11 ISO files from stupid ones.

### Media Scripts

- **ffgif**: Converts a video file to a GIF using ffmpeg.
- **fftrim**: Use ffmpeg to trim a video file without re-encoding.
- **ytdl**: Custom yt-dlp command to ensure highest quality MP4.

### Music Scripts

- **aif2wav**, **wav2aif**: Convert AIFF to WAV or WAV to AIFF, with optional Logic metadata.
- **alacrity**: Converts files in a directory to ALAC, with additional formats and options.
- **hpfilter**: Apply a highpass filter to cut bass frequencies for HomePod playback.
- **metacopy**: Copy audio metadata from a known file to a new file.
- **mp3ify**: Converts files to MP3.
- **mshare**: A script for sharing music bounces in a variety of formats.
- **pybounce**: Uploads audio files to a Telegram channel.
- **rmp3**: Removes MP3 files if there is an AIFF or WAV file with the same name.
- **wpmusic**: Uploads and replaces song remixes on WordPress.

### Mac Scripts

- **dmg-encrypt**: Encrypts DMG files with AES-256 encryption.
- **dmgify**: Creates DMG files from folders, with specific handling for Logic projects.
- **mvdmg**: Recursively moves nested DMG files to a desired location.
- **netreset**: macOS network reset script.
- **pkginst**: Wrapper for the macOS Installer command-line utility.
- **setmag**: Set MagSafe light according to power status.
- **spacepurger**: Generate large files to fill the disk and free up purgeable space.
- **timestamps**: Quick and easy timestamp getting/setting for macOS.

### Logic Pro Scripts

- **bipclean**: Identify and delete recently created AIFF files (default 2 hours).
- **bouncefiler**: Sort files into folders based on filename suffix.
- **bounceprune**: Prunes and consolidates bounces from Logic projects.
- **bounces**: CLI tool for working with Logic bounce files using BounceParser.
- **oldprojects**: Moves old Logic projects out of folders then deletes empty folders.

### System Tools

- **changehostname**: Changes the system hostname in all the relevant places.
- **dockermounter**: Checks to see if mount points are mounted, and act accordingly.
- **dsservice**: Main function for managing systemd services.
- **dsupdater**: Comprehensive update installer for Linux and macOS.
- **dsupdater-install**: Entry point for installer.
- **envsync**: Synchronize two .env files by merging their content.
- **ssh-tunnel**: Create or kill an SSH tunnel on the specified port.
- **watchtower**: Script to help with running Watchtower for Docker.

### Development Scripts

- **changelog**: Update CHANGELOG.md with a new version and automatically manage links.
- **checkdeps**: Check all interdependencies between dsbin and dsbin.
- **checkimports**: Check for circular imports in a Python project.
- **codeconfigs**: Download configs for coding tools and compare against local versions.
- **impactanalyzer**: Analyze the impact of changes in repositories and their dependencies.
- **packageanalyzer**: Analyze package dependencies and generate an import graph.
- **poetry-migrate**, **uvmigrate**: Process pyproject.toml file(s) based on command line arguments.
- **pybumper**: Version management tool for Python projects.
- **pyenversioner**: Updates .python-version files recursively.
- **repo-run**: Package management utility for working with multiple Poetry projects.
- **scriptdep**: Analyze dependencies and imports across scripts to help separate concerns.
- **tagreplace**: Replace an existing Git tag with a new tag name and description.
"""  # noqa: D415, W505
