# SmartHub Releases

Dieses Repository enthält öffentliche Release-Pakete für SmartHub.

## Schnellstart

Stable installieren oder aktualisieren:

```bash
curl -fsSL https://raw.githubusercontent.com/ehive-dev/smarthub-releases/main/install.sh | sudo bash
```

Pre-Release installieren:

```bash
curl -fsSL https://raw.githubusercontent.com/ehive-dev/smarthub-releases/main/install.sh | sudo bash -s -- --pre
```

Bestimmte Version installieren:

```bash
curl -fsSL https://raw.githubusercontent.com/ehive-dev/smarthub-releases/main/install.sh | sudo bash -s -- --tag v1.1.6
```

## Service

```bash
systemctl status smarthub --no-pager
journalctl -u smarthub -f
```

Health-Check lokal:

```bash
curl http://127.0.0.1:3002/healthz
```

## Lizenz

Die Nutzung ist für private und nicht-kommerzielle Zwecke erlaubt. Kommerzielle Nutzung benötigt eine vorherige schriftliche Zustimmung von ehive. Siehe `LICENSE.txt` und `THIRD_PARTY_NOTICES.txt`.
