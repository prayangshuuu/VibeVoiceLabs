/** Wrap raw PCM s16le mono chunks into a WAV Blob for playback / WaveSurfer. */

export function pcmChunksToWavBlob(
  chunks: ArrayBuffer[],
  sampleRate: number = 24000
): Blob {
  const totalBytes = chunks.reduce((n, c) => n + c.byteLength, 0);
  const out = new ArrayBuffer(44 + totalBytes);
  const view = new DataView(out);
  const pcm = new Uint8Array(out, 44);
  let offset = 0;
  for (const c of chunks) {
    pcm.set(new Uint8Array(c), offset);
    offset += c.byteLength;
  }

  const writeStr = (o: number, s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(o + i, s.charCodeAt(i));
  };
  writeStr(0, "RIFF");
  view.setUint32(4, 36 + totalBytes, true);
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeStr(36, "data");
  view.setUint32(40, totalBytes, true);

  return new Blob([out], { type: "audio/wav" });
}
