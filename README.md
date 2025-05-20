<img src="data/icons/hicolor/scalable/apps/io.github.vmkspv.netsleuth.svg" width="128" align="left"/>

# Netsleuth

_Netsleuth_ is a simple utility for calculating and analyzing IP subnet values.

<p align="center">
  <a href="https://github.com/vmkspv/netsleuth/actions/workflows/flatpak.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/vmkspv/netsleuth/flatpak.yml?logo=flatpak&logoColor=fff&labelColor=1a4138&color=229770"/>
  </a>
  <a href="https://github.com/vmkspv/netsleuth/releases/latest">
    <img src="https://img.shields.io/github/v/release/vmkspv/netsleuth?logo=github&logoColor=fff&labelColor=1a4138&color=229770"/>
  </a>
  <a href="https://flathub.org/apps/details/io.github.vmkspv.netsleuth">
    <img src="https://img.shields.io/flathub/downloads/io.github.vmkspv.netsleuth?logo=flathub&logoColor=fff&labelColor=1a4138&color=229770"/>
  </a>
</p>

<p align="center">
  <img src="data/screenshots/preview.png" width="756" title="Main window"/>
</p>

## Installation

The recommended installation method is via Flatpak.

<p>
  <a href="https://flathub.org/apps/details/io.github.vmkspv.netsleuth">
    <img src="https://flathub.org/api/badge?svg&locale=en" width="182"/>
  </a>
</p>

To use the command-line interface, add a shell alias by running the following command:

```bash
echo "alias netsleuth='flatpak run io.github.vmkspv.netsleuth'" >> ~/.bashrc
```

<details>
  <summary>Command-line interface</summary>

  ```
  > netsleuth --help
  usage: netsleuth [ip_address] [-m MASK] [--binary] [--hex] [-h] [-v]

  positional arguments:
    ip_address            ip for calculation

  options:
    -m MASK, --mask MASK  subnet mask (default: 24)
    --binary              show binary values
    --hex                 show hexadecimal values

  general:
    -h, --help            show this help message and exit
    -v, --version         show version information and exit
  ```

</details>

## Building from source

### GNOME Builder

The recommended method is to use GNOME Builder:

1. Install [`org.gnome.Builder`](https://gitlab.gnome.org/GNOME/gnome-builder) from Flathub.
2. Open Builder and select `Clone Repository`.
3. Clone `https://github.com/vmkspv/netsleuth.git`.
4. Press `Run Project` at the top once project is loaded.

### Flatpak

You can also build the actual code as Flatpak:

1. Install [`org.flatpak.Builder`](https://github.com/flatpak/flatpak-builder) from Flathub.
2. Clone `https://github.com/vmkspv/netsleuth.git` and `cd netsleuth`.
3. Run `flatpak run org.flatpak.Builder --install --user --force-clean build-dir io.github.vmkspv.netsleuth.json`.

## Contributing

Contributions are welcome!

If you have an idea, bug report or something else, don’t hesitate to [open an issue](https://github.com/vmkspv/netsleuth/issues).

> This project follows the [GNOME Code of Conduct](https://conduct.gnome.org).

## License

Netsleuth is released under the [GPL-3.0 license](COPYING).
