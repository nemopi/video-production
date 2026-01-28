---
name: audio-analysis-strategy
description: Strategy for selecting audio analysis tools (madmom, essentia, librosa) based on music type.
metadata:
  tags: audio, analysis, madmom, essentia, librosa, beat-detection
---

# Audio Analysis Strategy

When analyzing audio to sync video effects (beat sync, motion), choose the right tool based on the characteristics of the music.

## Tool Selection Guide

| Music Characteristic | Recommended Tool | Why? |
| :--- | :--- | :--- |
| **Rubato, Free Tempo, Live Performance** | **madmom** | Best at tracking fluctuating tempos and complex rhythms (RNN-based). |
| **Regular, EDM, Pop, Dance** | **essentia** | Extremely accurate for steady beats and rigid structures. Fast. |
| **Simple Structure, Few Beats** | **librosa** | Standard library. Good enough for simple tasks. |
| **Ambient, Quiet, Atmospheric** | **librosa** | When you don't need "hard" beat detection but rather spectral features or onset strength. |

## Detailed Usage

### 1. madmom (For "Human" Grooves)
Use for Jazz, Classical, or Live Rock where the grid is not perfect.
- **Strengths**: Deep Learning based beat tracking (RNN).
- **Python Usage**: `madmom.features.beats.RNNBeatProcessor()`

### 2. essentia (For "Machine" Grooves)
Use for Techno, House, Pop where the beat is quantized.
- **Strengths**: Standard and RhythmExtractor2013 are industry standards for BPM detection.
- **Python Usage**: `essentia.standard.RhythmExtractor2013()`

### 3. librosa (For "Texture" & Simple Beats)
Use for Ambient, Lo-fi, or when you just need a "general sense" of the energy.
Also preferred when you want **fewer cuts** (Long takes).
- **Strengths**: Easy to calculate `onset_env` (energy curve) and smooth it.
- **Python Usage**: `librosa.beat.beat_track()` or just using `librosa.onset.onset_strength()`.
