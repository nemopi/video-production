import { staticFile } from "remotion";

export const getAudioDuration = async (audioPath: string): Promise<number> => {
  return new Promise((resolve, reject) => {
    const audio = new Audio(staticFile(audioPath));

    audio.addEventListener("loadedmetadata", () => {
      resolve(audio.duration);
    });

    audio.addEventListener("error", (error) => {
      reject(error);
    });

    // ブラウザで音声データを読み込む
    audio.load();
  });
};
