# Tokyo Weather Short Movie - Production Kit

**Date**: 2026-01-22 (Thursday)
**Weather**: Clear / Sunny ☀️ (Low: 1°C, High: 6°C)
**Concept**: "Winter Morning Clarity"
**Target Output**: 5 seconds, 16:9 (1920x1080), Landscape.

---

## 1. Visual Generation (Nanobanana)
**Tool**: `generate_image` (User Execution via KamuiMCP)

**Prompt**:
```text
Photorealistic cinematic shot, Tokyo city street in winter morning, clear blue sky, crisp sunlight casting long shadows.
Low angle shot of a busy intersection (Shibuya or Shinjuku), people wearing warm coats and scarves.
Atmosphere: Cold air, high contrast, sharp details, 8k resolution.
Weather: Sunny, clear visibility.
Aspect Ratio: 16:9
```

## 2. Motion Generation (Hailuo)
**Tool**: `video_generation` (User Execution via KamuiMCP)
**Input**: The image generated above.

**Prompt**:
```text
(Cinematic Movement)
Camera: Slow dolly forward and slight tilt up towards the clear blue sky.
Action: People walking naturally, wind gently blowing coat tails.
Atmosphere: The sunlight glimmers between buildings. High quality, smooth motion.
Duration: 5 seconds.
```

## 3. Post-Processing (Optional)
**Text Overlay**: "2026.01.22 TOKYO / Sunny"
**Audio**: Ambient city sounds + Soft wind.
