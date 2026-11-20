# home_1

**`home_1`** is a modular, voice-first personal assistant designed to help plan daily tasks, converse with modern AI models, and provide a natural speech interface to home automation.

The project starts **software-only** (running on a development machine and a **Raspberry Pi CM4** with microphone/speaker I/O) and is architected from day one to grow into a physically embodied desktop companion inspired by **[Reachy Mini](https://www.pollen-robotics.com/)**.

---

## Project Goals

1. **Personal Planning & Assistance**
   Help organize daily schedules, capture notes/tasks, break down goals, and act as an always-available conversational helper.
2. **Pluggable AI Backends**
   Start with cloud LLM providers (**Google Gemini** and **Anthropic Claude**), while keeping a clean provider abstraction so a **locally hosted LLM** (e.g., Ollama, vLLM, llama.cpp) can be plugged in later for privacy or offline operation.
3. **Speech Interface to Home Automation**
   Enable natural voice control over smart-home devices through a generic, tool/MCP-based adapter layer (supporting platforms like Home Assistant, MQTT/Zigbee2MQTT, and custom services without tight coupling).
4. **Software-First, Hardware-Ready Embodiment**
   Begin purely in software on a Raspberry Pi CM4 with audio I/O, while designing clear state and expression boundaries so expressive robotics hardware (pan/tilt head, antennas, sound-source tracking, optional camera) can be added incrementally.

---

## Core Design Principles

- **Modular Python (`src/` layout)**: Python 3.11+ chosen for first-class support across Raspberry Pi OS, AI SDKs, audio/speech pipelines, and robotics tooling.
- **Provider-Agnostic Interfaces**: Core orchestration should not depend directly on a specific LLM vendor, home automation hub, or hardware platform.
- **Audio & Privacy Awareness**: Run wake-word detection and voice activity detection (VAD) locally on the Pi CM4 so audio is only processed/transmitted when triggered.
- **Graceful Embodiment**: Expressive behaviors (`idle`, `listening`, `thinking`, `speaking`, `look_at`) work with a no-op/console adapter in software mode and map directly to motors/LEDs once hardware is added.

---

## High-Level Architecture

`home_1` separates concerns into five core modules under `src/home_1/`:

- **`audio/`** — Audio capture/playback, wake word, VAD, Speech-to-Text (STT), Text-to-Speech (TTS), and Direction of Arrival (DoA) events.
- **`core/`** — Central orchestrator, assistant state machine, conversation memory, and planning workflows.
- **`llm/`** — Unified LLM client abstraction supporting Google Gemini, Anthropic Claude, and future local OpenAI-compatible/Ollama endpoints.
- **`integrations/`** — Pluggable tool and MCP adapters for home automation (Home Assistant, MQTT, etc.) and personal productivity tools (calendars, tasks).
- **`embodiment/`** — Hardware-agnostic physical expression interface bridging software-only execution to future Reachy Mini-style actuation.

For detailed component diagrams and interaction flows, see [`docs/architecture.md`](docs/architecture.md).

---

## Target Hardware Snapshot

- **Initial Compute Target**: Raspberry Pi Compute Module 4 (CM4) with speaker and microphone input.
- **Recommended Audio Front-End**: A USB DSP microphone array with hardware Acoustic Echo Cancellation (AEC) and Direction of Arrival (DoA) (e.g., *Seeed ReSpeaker Lite USB / XMOS XVF3800* or *ReSpeaker USB Mic Array v2.0*), enabling barge-in and future head-tracking toward the active speaker.
- **Future Physical Embodiment**: Reachy Mini-inspired desktop hardware (articulated head, expressive antennas, status LEDs, optional camera).

For the full hardware comparison, microphone array trade-offs, and embodiment roadmap, see [`docs/hardware.md`](docs/hardware.md).

---

## Roadmap

- **Phase 0 — Project Foundation** *(current)*
  - Repository structure, Git setup, architecture design, and Pi CM4 hardware/audio specification.
- **Phase 1 — Software-Only Core**
  - Python packaging (`pyproject.toml`), configuration management, text/CLI loop, Google Gemini & Anthropic Claude adapters, and initial planning tools.
- **Phase 2 — Raspberry Pi CM4 Voice Interface**
  - Local wake-word + VAD + STT/TTS pipeline on Pi CM4, microphone array & speaker integration, and first home automation tool/MCP adapters.
- **Phase 3 — Local & Hybrid LLM Support**
  - Add local LLM backend (Ollama / OpenAI-compatible LAN server) with optional routing between local fast commands (e.g., home automation) and cloud reasoning.
- **Phase 4 — Physical Embodiment (Reachy Mini-Inspired)**
  - Implement hardware embodiment adapter: DoA-driven head orientation, expressive idle/listening/speaking motions, and optional vision input.

---

## Repository Structure

```text
home_1/
├── config/                 # Configuration templates & environment profiles (dev, pi-cm4)
├── docs/
│   ├── architecture.md     # Layered software architecture & interaction flows
│   └── hardware.md         # Pi CM4, mic array/speaker proposal & embodiment roadmap
├── hardware/               # Future BOMs, wiring diagrams, CAD/3D models, CM4 carrier notes
├── scripts/                # Pi CM4 provisioning, audio verification & utility scripts
├── src/
│   └── home_1/
│       ├── audio/          # Wake word, VAD, STT, TTS, audio I/O & DoA
│       ├── core/           # Orchestrator, event bus, state machine & planner
│       ├── embodiment/     # Expression abstraction (software -> physical robot)
│       ├── integrations/   # Pluggable tool/MCP adapters (home automation, planning)
│       └── llm/            # LLM provider adapters (Gemini, Claude, local)
└── tests/                  # Automated unit and integration tests
```
