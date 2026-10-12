# TinkerByteTech Gaming Setup

## Quick start

1. **Download the ZIP for your distro:** [Debian](tinkerbytetech-debian-gaming-setup-terminal.zip) · [Ubuntu](tinkerbytetech-ubuntu-gaming-setup-terminal.zip) · [Kubuntu](tinkerbytetech-kubuntu-gaming-setup-terminal.zip) · [Fedora](tinkerbytetech-fedora-gaming-setup-terminal.zip). On the file page, click **Download raw file** (the download arrow).
2. **Extract the ZIP.** Open the extracted folder, right-click an empty area, and choose **Open in Terminal**.
3. **Start the installer.** For Ubuntu, enter:
   ```sh
   python3 tinkerbytetech-ubuntu-gaming-setup-terminal.py
   ```
   For another distro, replace `ubuntu` with `debian`, `kubuntu`, or `fedora`. Run it as your normal user—do not put `sudo` before this command.
4. **Choose your tools.** Enter `1 2 3 5` for **Steam, Lutris, Faugus Launcher, and Wine**, then press Enter. The menu also lets you choose a different combination.
5. **Choose Native or Flatpak.** Press Enter for **Native (default)**, or enter **F** for Flatpak.
6. **Review the setup**, then type **I** and press Enter to install. Enter your password in the terminal if requested. To see a preview first, choose **P**; choose **Q** to quit.

When installation finishes, open your installed apps from your desktop’s application menu.

Prefer a graphical interface? Use the **Graphical installer** links in [Downloads](#downloads) below.

---

The main method is an interactive terminal installer, with an optional browser-based graphical edition. Native launcher installation is the default; Flatpak is optional.

Four original standalone terminal downloads:

- `tinkerbytetech-debian-gaming-setup-terminal.py`
- `tinkerbytetech-ubuntu-gaming-setup-terminal.py`
- `tinkerbytetech-kubuntu-gaming-setup-terminal.py`
- `tinkerbytetech-fedora-gaming-setup-terminal.py`

Run the matching file with Python, choose tool numbers, review the commands, then choose Install or Preview. Terminal authentication uses sudo.

Optional graphical downloads:

- `tinkerbytetech-debian-gaming-setup.py`
- `tinkerbytetech-ubuntu-gaming-setup.py`
- `tinkerbytetech-kubuntu-gaming-setup.py`
- `tinkerbytetech-fedora-gaming-setup.py`

Each download opens a graphical interface in the user's browser on localhost. It needs Python 3.9 or newer and has no extra Python dependencies. Administrator package operations use the desktop's polkit authentication agent through `pkexec`; launch the tool as the regular desktop user, not with sudo.

The source, interface, command planner, HTTP protocol, and tests were written for TinkerByteTech. No code was imported from the supplied Debian Gaming Setup project. Four downloads are generated from our own common source so fixes remain consistent. Ubuntu and Kubuntu intentionally share Ubuntu's package-manager backend; Kubuntu identifies as Ubuntu in `/etc/os-release`.

## Main terminal method

```sh
python3 tinkerbytetech-ubuntu-gaming-setup-terminal.py
```

Enter `1 2 3 5` to select Steam, Lutris, Faugus Launcher and Wine. Choose **N** for Native (the default), or **F** for Flatpak. The setup summary lists the commands and any repository additions before any package operation. Choose `I` to install, `P` to preview, or `Q` to quit. Preview is the default. System steps request sudo authentication through the terminal. Run as your regular user so Flatpak apps belong to that account. Installation logs are saved under `~/.local/state/tinkerbytetech/gaming-setup/`.

```sh
python3 tinkerbytetech-ubuntu-gaming-setup-terminal.py --dry-run --select steam,lutris,faugus,wine
```

`--select` supports command-line choices and `--yes` skips the final installation question for deliberate unattended runs. Distro and architecture checks still apply. Each terminal download contains the planner and runner; it starts no browser or local web server.

## Optional graphical method

```sh
python3 tinkerbytetech-ubuntu-gaming-setup.py
```

Choose the corresponding filename for the other distributions. The installer opens its local graphical page automatically. Preview mode is selected initially. Choose tools, click Review setup, and run the preview. For installation, uncheck Preview only, review again, and click Install selected tools.

```sh
python3 tinkerbytetech-ubuntu-gaming-setup.py --demo
```

Demo mode permits reviewing any distro download on another system and always simulates commands. `--no-browser` prints the link instead of opening it. Close installer shuts down the local server when idle.

## Tools and installation routes

| Tool | Native on Debian / Ubuntu / Kubuntu | Native on Fedora | Flatpak mode |
| --- | --- | --- | --- |
| Steam | Valve's upstream `.deb` | RPM Fusion `steam` | Flathub |
| Lutris | Upstream `.deb`, with native Wine dependencies | Fedora `lutris`, with Wine | Flathub |
| Faugus Launcher | Upstream `.deb` | Project Copr `faugus/faugus-launcher` | Flathub |
| ProtonUp-Qt | Upstream AppImage with menu shortcut | Upstream AppImage with menu shortcut | Flathub |
| Wine | `wine`, `wine64`, `wine32:i386` | `wine` | Same native packages |
| GameMode / MangoHud | Distro packages | Distro packages | Distro packages; matching MangoHud Flatpak extensions are added for newly installed gaming launchers |

- Native is the default. The terminal supports `--mode native` and `--mode flatpak`.
- Existing native and Flatpak launchers are retained, without installing a second copy in the selected format.
- Fedora native Steam adds RPM Fusion free/nonfree repositories matching the detected release. Native Faugus enables the project's Copr. Repository additions appear in the review before installation.
- Upstream downloads are pinned and SHA256-checked. If an upstream asset changes, setup stops and asks for an updated installer.
- Native Lutris includes Wine dependencies. Debian/Ubuntu/Kubuntu enable i386 for native Steam, Faugus or Wine.
- ProtonUp-Qt's AppImage is installed in `~/.local/share/tinkerbytetech/protonup-qt/` with an application-menu shortcut. It uses extract-and-run mode, without requiring FUSE.
- Flatpak apps are installed per user. An unrelated existing Flathub remote is rejected.
- GameMode and MangoHud still need enabling in your launcher; this installer does not add game launch options automatically.
- GPU drivers, kernel settings, game files and account sign-ins are configured separately. Broad Flatpak permission overrides are not applied automatically.
- Conventional x86-64 distro installations are supported; Fedora Atomic editions use a different package workflow.

## Development checks

```sh
python3 build.py
python3 -m unittest discover -s tests -v
```

## Sources used for package routes

- [Flatpak usage](https://docs.flatpak.org/en/latest/using-flatpak.html)
- [Debian setup](https://flathub.org/en/setup/Debian)
- [Ubuntu setup](https://flathub.org/en/setup/Ubuntu)
- [Fedora setup](https://flathub.org/en/setup/Fedora)
- [Lutris downloads](https://lutris.net/downloads)
- [Faugus installation](https://github.com/Faugus/faugus-launcher)
- [Debian wine32](https://packages.debian.org/trixie/wine32)
- [Fedora Wine package](https://packages.fedoraproject.org/pkgs/wine/wine/)


## Downloads

- **Debian**: [Terminal installer](tinkerbytetech-debian-gaming-setup-terminal.zip) · [Graphical installer](tinkerbytetech-debian-gaming-setup.zip)
- **Ubuntu**: [Terminal installer](tinkerbytetech-ubuntu-gaming-setup-terminal.zip) · [Graphical installer](tinkerbytetech-ubuntu-gaming-setup.zip)
- **Kubuntu**: [Terminal installer](tinkerbytetech-kubuntu-gaming-setup-terminal.zip) · [Graphical installer](tinkerbytetech-kubuntu-gaming-setup.zip)
- **Fedora**: [Terminal installer](tinkerbytetech-fedora-gaming-setup-terminal.zip) · [Graphical installer](tinkerbytetech-fedora-gaming-setup.zip)

Download a ZIP using GitHub’s **Download raw file** button, then extract it and follow START-HERE.txt.

[Source and build tools](tinkerbytetech-gaming-setup-source.zip) · [SHA256 checksums](SHA256SUMS)
