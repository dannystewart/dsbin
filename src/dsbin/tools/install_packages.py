"""Perform initial package installation based on the package manager(s) available."""

from __future__ import annotations

import platform
import shutil
import subprocess

# List of packages to install
packages = [
    "age",
    "bat",
    "chafa",
    "chezmoi",
    "curl",
    "displayplacer",
    "exiftool",
    "eza",
    "fd",
    "gcc",
    "gh",
    "git-lfs",
    "htop",
    "inetutils",
    "lesspipe",
    "mosh",
    "rsync",
    "sed",
    "tmux",
    "tmux-mem-cpu-load",
    "wget",
]


def run_command(cmd: str) -> str | None:
    """Run a command and return the output."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return result.stdout.decode().strip()
    except subprocess.CalledProcessError:
        return None


def is_arm() -> bool:
    """Check if the current machine is ARM64."""
    return "ARM64" in platform.uname().machine.upper()


def install_x86_homebrew_on_arm() -> bool:
    """Install x86 Homebrew on ARM64 if not already present."""
    if is_arm() and not shutil.which("/usr/local/bin/brew"):
        print("Installing x86 Homebrew on ARM64.")
        command = 'arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"'
        run_command(command)
        return True
    return False


def install_with_apt() -> bool:
    """Install packages with apt."""
    if not shutil.which("apt-get"):
        return False

    run_command("sudo apt update")
    run_command("sudo apt -y install build-essential")

    for pkg in packages:
        cmd_to_check = "ftp" if pkg == "inetutils" else "lesspipe.sh" if pkg == "lesspipe" else pkg
        if not shutil.which(cmd_to_check):
            run_command(f"sudo apt -y install {pkg}")

    return True


def install_with_pacman() -> bool:
    """Install packages with pacman."""
    if not shutil.which("pacman"):
        return False

    if not run_command("sudo pacman -Qs base-devel"):
        run_command("sudo pacman --noconfirm -Syu base-devel")

    for pkg in packages:
        cmd_to_check = "ftp" if pkg == "inetutils" else "lesspipe.sh" if pkg == "lesspipe" else pkg
        if not shutil.which(cmd_to_check):
            run_command(f"sudo pacman -S --noconfirm {pkg}")

    return True


def install_with_dnf() -> bool:
    """Install packages with dnf."""
    if not shutil.which("dnf"):
        return False

    run_command("sudo dnf check-update")
    run_command("sudo dnf -y install @development-tools")

    for pkg in packages:
        cmd_to_check = "ftp" if pkg == "inetutils" else "lesspipe.sh" if pkg == "lesspipe" else pkg
        if not shutil.which(cmd_to_check):
            run_command(f"sudo dnf -y install {pkg}")

    return True


def install_with_homebrew() -> bool:
    """Install packages with Homebrew."""
    if not shutil.which("brew"):
        return False

    run_command("brew update")

    for pkg in packages:
        cmd_to_check = "ftp" if pkg == "inetutils" else "lesspipe.sh" if pkg == "lesspipe" else pkg
        if not shutil.which(cmd_to_check):
            run_command(f"brew install {pkg}")

    run_command("brew cleanup")

    return True


def install_remaining_with_homebrew() -> None:
    """Use Homebrew as the fallback for any packages still missing."""
    if shutil.which("brew"):
        remaining_packages = [
            pkg
            for pkg in packages
            if not shutil.which(
                "ftp" if pkg == "inetutils" else "lesspipe.sh" if pkg == "lesspipe" else pkg
            )
        ]
        if remaining_packages:
            run_command("brew update")
            for pkg in remaining_packages:
                run_command(f"brew install {pkg}")
            run_command("brew cleanup")
            print("Remaining packages installed successfully with Homebrew.")


def main() -> None:
    """Install packages based on the package manager(s) available."""
    install_x86_homebrew_on_arm()

    if install_with_apt():
        print("Packages installed successfully with APT.")
    elif install_with_pacman():
        print("Packages installed successfully with Pacman.")
    elif install_with_dnf():
        print("Packages installed successfully with DNF.")
    elif install_with_homebrew():
        print("Packages installed successfully with Homebrew.")
    else:
        print("No supported package managers found.")

    install_remaining_with_homebrew()


if __name__ == "__main__":
    main()
