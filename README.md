# RSS News Ticker with Holy Quran

A customizable desktop RSS news ticker with integrated Holy Quran display, built with Python and PyQt5.

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-GPLv3-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

## Features

- **Complete Holy Quran Display** — Full Quran text with verse-by-verse scrolling (Credits to [Tanzil Project](https://tanzil.net))
- **Multiple RSS Feed Support** — Smart organization with sequential, round-robin, and random display modes
- **Auto-Translation** — Automatic translation to 20+ languages via Google Translate
- **Fully Customizable Appearance** — Colors, fonts, sizes, separators, and tray icons
- **System Tray Integration** — Quick actions and persistent background operation
- **Multi-Language UI** — English, French, and Arabic interface support
- **Smart Direction Detection** — Automatic RTL/LTR scrolling based on content language
- **Chunked Quran Loading** — Efficient memory usage with configurable verse group sizes

## Screenshots

*The ticker appears as a sleek, customizable bar at the top or bottom of your screen, continuously scrolling news headlines or Quranic verses.*

## Installation

### Prerequisites

- Python 3.7 or higher
- Qt5 development libraries (for PyQt5 compilation)

### From Source

1. Clone the repository:
```bash
git clone https://github.com/maher-berzig/rss-ticker.git
cd rss-ticker
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download the Quran XML file:
   - Visit [Tanzil.net](https://tanzil.net) to download the Quran XML file
   - Place it in the application directory as `quran.xml`

5. Run the application:
```bash
python rss_ticker.py
```

### Building Executable (Optional)

To create a executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --windowed --icon=rss.ico --add-data "quran.xml;." QuranNewsTicker.py
```

## Usage

### First Launch

On first launch, the ticker will appear at the bottom of your screen with default settings. Right-click the system tray icon or the ticker itself to access the configuration menu.

### Configuration

Access settings via the system tray icon (⚙️ Configuration):

#### RSS Feeds Tab
- Add, remove, and activate/deactivate RSS feed sources
- Configure Quran display mode (Full, Random Sura, Specific Sura)
- Set verse group size for chunked loading
- Enable/disable translation and select target language
- Choose feed display mode: Sequential, Round-Robin, or Random

#### Appearance Tab
- Bar height, background color, and text color
- Font family, size, and weight
- News separator type (default circle or custom image)
- Verse numbers color (for Quran mode)
- System tray icon customization

#### Behavior Tab
- Bar position (top/bottom) with vertical offset
- Scroll direction (auto-detect, LTR, or RTL)
- Scroll speed (1.0–20.0)
- Cycle spacing for RTL mode

#### About Tab
- Application information, version, and credits

### System Tray Controls

- **Left Click** — Show/hide the ticker
- **Double Click** — Open configuration
- **Middle Click** — Refresh RSS feeds
- **Right Click** — Context menu with feed toggles and controls

### Keyboard & Mouse

- **Hover** over the ticker to pause scrolling and reduce opacity
- **Left Click** on ticker to toggle visibility
- **Right Click** on ticker to open context menu

## Supported Languages

### Interface Languages
- English
- French (Français)
- Arabic (العربية)

### Translation Targets
Arabic, English, French, German, Spanish, Russian, Italian, Japanese, Chinese, Portuguese, Turkish, Korean, Hindi, Dutch, Polish, Swedish, Greek, Hebrew, Thai, Vietnamese

## Default RSS Feeds

The application comes pre-configured with major international news sources:

| Source | Language | URL |
|--------|----------|-----|
| Al Jazeera | Arabic | aljazeera.net |
| Al Arabiya | Arabic | alarabiya.net |
| BBC News | English | bbc.co.uk |
| CNN | English | cnn.com |
| France 24 | French | france24.com |
| France Info | French | franceinfo.fr |
| Rai News | Italian | rainews.it |
| El País | Spanish | elpais.com |
| Deutsche Welle | German | dw.com |
| RT | Russian | russian.rt.com |

## Configuration File

Settings are stored in `rss_ticker_config.json` in the application directory. The file is automatically created on first run and updated when you apply changes in the configuration dialog.

## Requirements

See [requirements.txt](requirements.txt) for the full dependency list.

Key dependencies:
- **PyQt5** — GUI framework
- **feedparser** — RSS/Atom feed parsing
- **googletrans** — Google Translate API
- **requests** — HTTP library (used by feedparser)

## Project Structure

```
rss-ticker/
├── rss_ticker.py          # Main application code
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── rss_ticker_config.json # User configuration (auto-generated)
└── quran.xml             # Holy Quran text (download separately)
```

## Troubleshooting

### Quran file not found
Ensure `quran.xml` is in the same directory as the executable/script. Download from [Tanzil.net](https://tanzil.net).

### Translation not working
The Google Translate API may occasionally rate-limit requests. Wait a few minutes and try again, or disable translation.

### Ticker not visible
Check if the ticker is hidden via the system tray menu. On multi-monitor setups, the ticker appears on the primary screen.

### High CPU usage
Reduce scroll speed or increase verse chunk size in Quran mode to lower refresh frequency.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Credits

- **Author:** Maher Berzig
- **Quran Data:** [Tanzil Project](https://tanzil.net) — Universal Quran text
- **Translation:** [Google Translate](https://translate.google.com) via googletrans library
- **RSS Parsing:** [feedparser](https://pypi.org/project/feedparser/) library

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).

```
Copyright © 2026 Maher Berzig

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
```

## Support

- **Email:** maher.berzig@gmail.com
- **Issues:** [GitHub Issues](https://github.com/maher-berzig/rss-ticker/issues)
- **Repository:** [github.com/maher-berzig/rss-ticker](https://github.com/maher-berzig/rss-ticker)

---

**Built with** Python • PyQt5 • feedparser • googletrans • Holy Quran XML
