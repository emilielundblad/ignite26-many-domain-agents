"""Fake knowledge base for the Documentation domain: 30 articles about the
fictional Aurora smart thermostat. Every article has a stable URL on the
reserved example.com domain so agent answers can cite it."""

from __future__ import annotations

BASE_URL = "https://docs.example.com/aurora/kb"

_ARTICLES: list[tuple[str, str, list[str]]] = [
    ("Short cycling after firmware 4.1.3", "Firmware 4.1.3 can reset the switching hysteresis to 0.1 C, which makes the boiler start and stop every few minutes. Fix: open Installer menu > Control > Hysteresis and set 0.5 C for radiators or 0.3 C for underfloor heating, or update to firmware 4.2.1, which restores the previous value.", ["short cycling", "hysteresis", "firmware", "boiler", "on and off"]),
    ("Set the switching hysteresis", "Hysteresis is the temperature band around the target. Values below 0.3 C cause frequent switching. Recommended: 0.5 C radiators, 0.3 C underfloor heating.", ["hysteresis", "installer", "cycling"]),
    ("Firmware release notes 4.2.1", "Restores hysteresis after upgrade from 4.1.x, fixes update hang at 80 percent, improves Wi-Fi reconnect.", ["firmware", "release notes", "4.2.1"]),
    ("Update stuck at 80 percent", "Power-cycle the device, keep it on a 2.4 GHz network during update, then retry from Settings > Device > Update.", ["firmware", "update", "stuck"]),
    ("Wi-Fi disconnects in the evening", "Disable band steering on the router or pin the device to 2.4 GHz. Firmware 4.2.1 improves reconnect.", ["wi-fi", "network", "disconnect"]),
    ("Calibrate the humidity sensor", "Settings > Sensors > Humidity offset. Allow 24 hours after installation before calibrating.", ["humidity", "sensor", "calibration"]),
    ("Pair the mobile app", "Keep the phone within 2 meters, enable Bluetooth, and enter the pairing code within 60 seconds.", ["pairing", "app", "bluetooth"]),
    ("Restore a schedule after a power cut", "Schedules are stored in the cloud. Open the app and select Restore last schedule.", ["schedule", "power cut", "restore"]),
    ("Configure away mode with geofencing", "All household phones need location permission set to Always. Away mode starts when every phone has left the 500 m zone.", ["away mode", "geofencing"]),
    ("Relay clicking noise", "A click every 30 seconds while idle indicates a failing relay on hardware revision A. Replace under warranty.", ["relay", "noise", "click", "warranty"]),
    ("Daylight saving time issues", "Set the time zone by region, not by UTC offset, in Settings > Time.", ["time zone", "daylight saving"]),
    ("Energy report shows zero", "Energy reports need the boiler profile set under Settings > Heating system. Reports rebuild within 24 hours.", ["energy", "report"]),
    ("Link a voice assistant", "Error VA-17 means the account region differs from the device region. Align regions and relink.", ["voice assistant", "VA-17"]),
    ("Child lock", "Hold the lower right corner for 5 seconds and enter the PIN. Firmware 4.2.0 fixes the stuck lock icon.", ["child lock", "pin"]),
    ("Outdoor sensor battery life", "Expected battery life is 18 months. Short life indicates a weak signal; move the receiver closer.", ["outdoor sensor", "battery"]),
    ("Heat pump mode on hardware revision B", "Heat pump mode requires firmware 4.2.0 or later on revision B.", ["heat pump", "hardware revision"]),
    ("Frost protection threshold", "Frost protection uses the outdoor sensor when present. Check that the sensor is not exposed to direct sun.", ["frost protection"]),
    ("Device shows offline in the app", "Sign out and in again; the app caches state for up to 15 minutes.", ["offline", "app"]),
    ("Touch screen calibration", "Settings > Display > Calibrate touch. Follow the five targets.", ["touch screen", "calibration"]),
    ("Overshoot with underfloor heating", "Enable Adaptive start and set hysteresis to 0.3 C for slow heating systems.", ["overshoot", "underfloor", "adaptive start"]),
    ("Night mode brightness", "Night mode ends at the next scheduled day period. Check Settings > Display > Night mode.", ["night mode", "display"]),
    ("Factory reset", "Hold the dial for 15 seconds. All local settings are erased; cloud schedules remain.", ["factory reset"]),
    ("Warranty and returns", "The Aurora has a two-year warranty. Returns are handled by the Customer operations team; support agents do not issue refunds or credit notes.", ["warranty", "returns", "refund", "credit note"]),
    ("Installer menu access", "Hold the dial and the back button for 5 seconds. Installer changes are logged.", ["installer"]),
    ("OpenTherm compatibility", "OpenTherm 2.2 is supported. Modulating control requires boiler support.", ["opentherm", "boiler"]),
    ("Multi-zone setup", "Up to six zones per hub. Each zone needs its own receiver.", ["zones", "multi-zone"]),
    ("Data and privacy", "Telemetry is pseudonymised and kept for 13 months.", ["privacy", "data"]),
    ("Accessibility features", "Large text and high contrast are available under Settings > Accessibility.", ["accessibility"]),
    ("Supported routers", "Any 802.11 b/g/n router on 2.4 GHz. WPA3 requires firmware 4.2.0.", ["router", "wpa3", "wi-fi"]),
    ("Contact support", "Open a ticket from the app. Response target is one business day.", ["support", "ticket"]),
]

ARTICLES: dict[str, dict] = {}
for _i, (_title, _body, _tags) in enumerate(_ARTICLES, start=1):
    _id = f"KB{_i:04d}"
    ARTICLES[_id] = {"id": _id, "title": _title, "body": _body, "tags": _tags, "url": f"{BASE_URL}/{_id}"}
