import { Composition } from 'remotion';
import { TwilightStation } from './Composition';
import './style.css';

export const RemotionRoot: React.FC = () => {
    return (
        <>
            <Composition
                id="TwilightStation"
                component={TwilightStation}
                durationInFrames={300} // 10 seconds at 30fps
                fps={30}
                // Background generated is usually landscape/square. Assuming 16:9 for cinematic feel or square.
                // Let's set to 1920x1080 (Landscape) to match Shinkai cinematic style.
                width={1920}
                height={1080}
            />
        </>
    );
};
