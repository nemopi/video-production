import {
    AbsoluteFill,
    Img,
    staticFile,
    useCurrentFrame,
    useVideoConfig,
    interpolate,
    random,
    Easing,
} from 'remotion';
import React, { useMemo } from 'react';

const backgroundSource = staticFile('background.png');

export const TwilightStation: React.FC = () => {
    const frame = useCurrentFrame();
    const { width, height, durationInFrames } = useVideoConfig();

    // --- Shinkai Magic: Layers of Atmosphere ---

    // 1. Floating Particles (Dust Motes / Fireflies)
    // Generates 100 random particles that slowly float upwards
    const particles = useMemo(() => {
        return new Array(80).fill(0).map((_, i) => {
            const x = random(i) * 100; // 0-100%
            const yStr = random(i + 1) * 100; // 0-100%
            const size = random(i + 2) * 2 + 1; // 1-3px
            const speed = random(i + 3) * 0.2 + 0.05; // speed
            const opacityBase = random(i + 4) * 0.5 + 0.3;
            return { x, yStr, size, speed, opacityBase };
        });
    }, []);

    // 2. Train Passing Effect (Light & Shadow)
    // Occurs every 300 frames (10 sec) roughly, or just once in this loop.
    // Let's make it pass at frame 150 (5 sec mark).
    const trainPassProgress = interpolate(
        frame,
        [100, 200], // Lasts 100 frames (3.3 sec)
        [0, 1],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.25, 0.1, 0.25, 1) }
    );

    // Train Light (Bright sweep)
    const trainLightX = interpolate(trainPassProgress, [0, 1], [-50, 150]); // Sweeps across screen
    const trainLightOpacity = interpolate(
        frame,
        [100, 150, 200],
        [0, 0.4, 0],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );

    // 3. Pulsing Light Leak (Breathing world)
    const breath = Math.sin(frame / 30) * 0.05 + 0.95; // 0.9 - 1.0 slowly

    return (
        <AbsoluteFill style={{ backgroundColor: 'black' }}>
            {/* Base Layer: Background Image */}
            {/* Slight zoom for "Breathing" effect */}
            <AbsoluteFill style={{ transform: `scale(${1.0 + Math.sin(frame / 100) * 0.01})` }}>
                <Img src={backgroundSource} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            </AbsoluteFill>

            {/* Layer 2: Train Passing Light Effect (Additive) */}
            <AbsoluteFill
                style={{
                    background: `linear-gradient(90deg, transparent 0%, rgba(255, 255, 200, 0.5) 50%, transparent 100%)`,
                    left: `${trainLightX}%`,
                    width: '50%',
                    opacity: trainLightOpacity,
                    mixBlendMode: 'overlay',
                    transform: 'skewX(-20deg)', // Motion blur feel
                }}
            />

            {/* Layer 3: Particles (The Air) */}
            <AbsoluteFill>
                {particles.map((p, i) => {
                    // Move Upwards
                    const currentY = (p.yStr - frame * p.speed) % 100;
                    const displayY = currentY < 0 ? 100 + currentY : currentY;

                    // Twinkle
                    const opacity = p.opacityBase + Math.sin(frame / 10 + i) * 0.2;

                    return (
                        <div
                            key={i}
                            style={{
                                position: 'absolute',
                                left: `${p.x}%`,
                                top: `${displayY}%`,
                                width: p.size,
                                height: p.size,
                                borderRadius: '50%',
                                backgroundColor: '#fff',
                                opacity: opacity,
                                boxShadow: `0 0 ${p.size * 2}px ${random(i) > 0.5 ? '#ffaa00' : '#ffffff'}`, // Warm or Cool glow
                            }}
                        />
                    );
                })}
            </AbsoluteFill>

            {/* Layer 4: Cinematic Vignette & Color Grade */}
            <AbsoluteFill
                style={{
                    background: 'radial-gradient(circle, rgba(0,0,0,0) 60%, rgba(10,10,30,0.4) 100%)', // Blue-ish vignette
                    pointerEvents: 'none',
                }}
            />

            {/* Layer 5: Lens Flare Overlay (Top Left source usually) */}
            <AbsoluteFill
                style={{
                    background: 'radial-gradient(circle at 10% 20%, rgba(255,100,50,0.15) 0%, transparent 50%)', // Warm flare
                    mixBlendMode: 'screen',
                    opacity: breath, // Pulsing
                }}
            />

        </AbsoluteFill>
    );
};
