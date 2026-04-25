# GeoRecon

Asynchronous geolocation capture service for OSINT investigations. Serve convincing phishing pages to capture visitor device information and GPS coordinates.

## Features

- **Geolocation Capture**: Obtain precise GPS coordinates from visitors via browser API
- **Device Fingerprinting**: Collect OS, browser, CPU cores, RAM, GPU info, and screen resolution
- **Telegram Integration**: Optional real-time notifications via Telegram bot
- **Multiple Templates**: Extensible template system (comes with Telegram-style template)
- **Configurable**: CLI arguments and YAML configuration file support
- **Clean Output**: Formatted CLI logs with colored device/location data

## Requirements

- Python 3.12+
- Modern browser with Geolocation API support

## Installation (later)

```bash
pip install .
```

## Usage

```bash
# Run with defaults
geo-recon

# Custom host and port
geo-recon --host 127.0.0.1 --port 8080

# Use config file
geo-recon --config /path/to/geoconf.yaml

# Disable access logs
geo-recon --no-access-log
```

### Configuration File

Create `geoconf.yaml`:

```yaml
host: "0.0.0.0"
port: 8080
log_level: "info"
no_access_log: false
```

### Telegram Setup

When prompted, enter your bot token and target chat ID. Configuration is saved to `~/.geo_recon.conf`.

## How It Works

1. Launch the server and select a template
2. Configure template parameters (e.g., group name, member count)
3. Share the phishing link with your target
4. When the target clicks "VIEW IN TELEGRAM", their device info and location are captured
5. Results display in CLI and optionally forward to Telegram


## Roadmap

- [ ] Package for AUR (Arch Linux)
- [ ] Package for apt (Debian/Ubuntu)
- [ ] More templates (like GDisk, NearYou, WhatsApp, & etc)
## License

MIT License - see [LICENSE](LICENSE)