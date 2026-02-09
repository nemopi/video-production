# Project: Rainy Heart, Forward Step - Production Kit

**Producer**: Antigravity (Persona: Producer)
**Visual Director**: Makoto Shinkai
**Sound Director**: Nujabes

Image generation capacity was temporarily unavailable, so here are the **Precise Prompts** designed by the Shinkai Persona. Please assume the role of the "Executor" and input these into your KamiMCP tools.

---

## 1. Visual Generation (nanobanana)
**Target Tool**: `generate_image` (or KamiMCP equivalent)
**Goal**: Create the "Key Visual" (The emotional anchor).

**Prompt**:
```text
Makoto Shinkai style, highly detailed anime art.
Scene: Rain-soaked asphalt in Tokyo Shinjuku street at golden hour twilight.
Composition: Close-up low angle of a puddle on the ground.
Reflections: In the puddle, a clear reflection of a "Go" (Blue) traffic light and a pair of white sneakers stepping forward.
Atmosphere: Deep blue and warm orange gradient sky, volumetric lighting (crepuscular rays), lens flare from street lamps.
Details: Hyper-realistic water droplets, wet texture on asphalt, floating dust particles, melancholic but hopeful vibe.
Aspect Ratio: 16:9 (Cinematic)
```

---

## 2. Motion Generation (Sora2Pro)
**Target Tool**: `run_sora_video` (or KamiMCP I2V)
**Input**: The image generated above.
**Goal**: Turn the key visual into a 10-second narrative of "moving forward".

**Prompt**:
```text
(Cinematic Anime Motion, Shinkai Style)
Camera Movement: Slow, smooth Tilt Up starting from the reflection in the puddle, moving up to show the character's back as they start walking.
Action: The character (in the reflection and reality) takes a step forward into the light.
Atmosphere: Gentle rain falling with visible droplets, wind blowing the character's hair and coat softy.
Lighting: The traffic light changes from Red to Green (if possible) or stays Green, symbolizing "Go". The sunlight flares intensity as the camera tilts up.
Duration: 10 seconds.
Quality: High fidelity, 60fps, smooth interpolation.
```

---

## 3. Sound Direction (Nujabes Style)
**Instructions for Sound Engineer**:
*   **Base**: Heavy vinyl crackle noise (Rain texture).
*   **0:00-0:03**: Only the sound of rain hitting asphalt and distant traffic.
*   **0:03**: A distinct sound of a footstep (splash in shallow water).
*   **0:04**: A mellow, lo-fi piano loop fades in (Chord: Fmaj7 -> Em7).
*   **Mix**: Keep the beat slightly behind the grid (lazy swing) to create a relaxed, healing vibe.

---

## Producer's Note
"This combination—Shinkai's light handling the visual 'pain', and Nujabes' beat handling the 'healing'—is the optimal solution for your request. Execute these prompts to witness the synthesis."
