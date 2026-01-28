---
name: css-3d
description: Creating 3D effects using CSS transforms in Remotion (perspective, rotateX, rotateY).
metadata:
  tags: 3d, css, perspective, transform, rotate
---

# CSS 3D Transforms

For simple 3D effects (cards flipping, floating interfaces) where `Three.js` is overkill, use CSS 3D transforms.
This is lighter and easier to integrate with standard React components like Tailwind.

## Basic Setup

1.  **Perspective Container**: The parent element MUST have a `perspective` style to create depth.
2.  **Transformed Child**: The child element uses `rotateX`, `rotateY`, `rotateZ` and `translateZ`.

```tsx
import { AbsoluteFill, useVideoConfig } from "remotion";

export const MyComposition = () => {
  return (
    <AbsoluteFill
      style={{
        // 1. Perspective on parent
        perspective: 1000, 
        backgroundColor: "#e5e5e5",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          width: 500,
          height: 300,
          backgroundColor: "white",
          borderRadius: 20,
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          // 2. Transform on child
          transform: "rotateX(20deg) rotateY(-15deg)", 
        }}
      >
        <h1>Hello 3D World</h1>
      </div>
    </AbsoluteFill>
  );
};
```

## Animating 3D Transforms

Combine `interpolate()` with template literals to animate the rotation.

```tsx
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

const frame = useCurrentFrame();
const { durationInFrames } = useVideoConfig();

// Rotate Y from 20 to -20 degrees over the full video duration
const rotateY = interpolate(frame, [0, durationInFrames], [20, -20]);

return (
  <div style={{ transform: `rotateX(10deg) rotateY(${rotateY}deg)` }}>
    {/* Content */}
  </div>
);
```

## "Mac Terminal" Style Example

A popular effect is a floating UI window with slight 3D rotation to give it a premium feel.

- **Perspective**: `1000px` (standard depth)
- **Rotation**: Small values! e.g., `rotateX(5deg) rotateY(-5deg)`. Don't overdo it.
- **Shadow**: Use a large, soft shadow (`box-shadow`) to emphasize the floating effect.
