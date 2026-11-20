# Hardware Architecture & Proposals

This document outlines the initial hardware target (**Raspberry Pi CM4** with microphone and speaker), evaluates microphone options, and sketches the upgrade path toward a **Reachy Mini-inspired** physical companion.

---

## 1. Initial Compute Platform: Raspberry Pi CM4

The initial voice appliance targets a **Raspberry Pi Compute Module 4 (CM4)** paired with a carrier/IO board.

### Recommended Baseline
- **RAM**: 4 GB or 8 GB (4 GB is comfortable for Python + wake word + VAD + Piper TTS; 8 GB gives headroom for local `faster-whisper` small models and extra services).
- **Storage**: 32 GB+ eMMC (or fast industrial microSD if using CM4 Lite) + active/passive heatsink.
- **Connectivity**: Built-in Wi-Fi/BT or Ethernet via the CM4 carrier board.
- **Carrier Board**: Official CM4 IO Board (ideal for prototyping with full USB, HDMI, GPIO, and 12V power) or a compact carrier board once moving into a custom enclosure.

> **Note on Local LLMs & Pi CM4**: While wake-word detection (`openWakeWord`), VAD (`Silero VAD`), and lightweight TTS (`Piper`) run smoothly on a Pi CM4 CPU, running capable local LLMs directly on a CM4 is slow. When adding a local LLM in Phase 3, the recommended setup is to run the LLM on a dedicated LAN host (PC/mini-PC/GPU server running Ollama or llama.cpp) and connect to it over the local network from the Pi CM4.

---

## 2. Microphone & Speaker Proposal

A voice assistant in a living space faces three acoustic challenges that a bare single microphone struggles with:
1. **Far-field pickup**: Understanding speech reliably from 1–4 meters away in a reverberant room.
2. **Acoustic Echo Cancellation (AEC)**: Preventing the assistant's own speaker output from triggering false wake words or drowning out your voice when interrupting (*barge-in*).
3. **Direction of Arrival (DoA)**: Knowing *which direction* a voice came from — critical later when adding a Reachy Mini-style pan/tilt head that turns to face you.

### Option Comparison

| Option | Example Hardware | Pros | Cons | Best Fit |
| :--- | :--- | :--- | :--- | :--- |
| **USB DSP Mic Array** *(Recommended)* | **Seeed ReSpeaker Lite USB** (XMOS XVF3800, 2-mic array) or **ReSpeaker USB Mic Array v2.0** (4-mic circular array) | Hardware **AEC**, beamforming, noise suppression, **DoA** over USB/HID, standard USB audio class (no fragile Linux HAT kernel drivers), works on both dev PC and Pi CM4 | Slightly higher cost (~$35–$70); requires a small speaker wired to its audio output for hardware AEC reference | **Best long-term choice** for CM4 + future Reachy Mini head tracking |
| **USB Conference Speakerphone** | Jabra Speak 510 / Anker PowerConf S330 | All-in-one mic array + speaker + proven hardware AEC; zero wiring; plug-and-play | Bulkier enclosure; does **not** expose DoA angle data for robotics | **Fastest Phase 1–2 prototype** if you already own one |
| **Single I2S Mic + I2S Amp** | `INMP441` MEMS mic + `MAX98357A` 3W amp on CM4 GPIO | Very cheap (<$10) and ultra-compact for tight enclosures | No hardware AEC (harder barge-in), no DoA, weaker far-field pickup, requires I2S device-tree config | Ultra-compact/low-cost custom builds where close-range speech is acceptable |

### Recommended Starting Audio Setup
1. **Microphone Array**: **Seeed ReSpeaker Lite USB (XMOS XVF3800)** (compact 2-mic linear/bar form factor, great for a small desktop head/base) or **ReSpeaker USB Mic Array v2.0** (circular 4-mic array with 360° DoA and LED ring).
   - *Why USB over GPIO HAT?* Older I2S ReSpeaker HATs often rely on out-of-tree kernel drivers that break across Raspberry Pi OS kernel updates. USB DSP arrays present standard UAC audio devices to both Windows/macOS/Linux (during software-only development) and Raspberry Pi OS.
2. **Speaker**: Connect a compact **3W–5W (4Ω or 8Ω) enclosed speaker** directly to the mic array's onboard speaker/3.5mm output. Routing playback through the array keeps the speaker audio inside the DSP's **hardware AEC reference loop**, dramatically improving wake-word accuracy and barge-in during playback.

---

## 3. Future Physical Embodiment (Reachy Mini-Inspired)

Once the software voice loop, planning workflows, and home automation integrations are solid, hardware embodiment can be layered on without rewriting the core assistant:

### Planned Physical Capabilities
- **Expressive Head Motion (2–3 DoF)**: Pan/tilt (and optional roll) driven by smart serial bus servos (e.g., Feetech STS3215 / Dynamixel XL330) controlled over USB-UART from the Pi CM4.
- **Expressive Antennas / Ears**: 1–2 lightweight micro-servos to convey subtle states (`listening`, `thinking`, `happy`, `sleeping`).
- **Sound-Source Tracking**: Feed the mic array's **DoA angle** directly into `embodiment.look_at(azimuth_deg)` so the assistant naturally turns toward whoever is speaking.
- **Visual Feedback**: Subtle status LED ring or eye display synchronized with the `core` state machine.
- **Optional Vision**: Raspberry Pi Camera Module connected via the CM4 CSI port for presence detection, face tracking, or multimodal queries to Gemini/Claude.

### Hardware Directory Usage
All future bills of materials (BOM), wiring schematics, CM4 carrier pinouts, and CAD/3D-printable enclosure files will be stored under [`hardware/`](../hardware/).
