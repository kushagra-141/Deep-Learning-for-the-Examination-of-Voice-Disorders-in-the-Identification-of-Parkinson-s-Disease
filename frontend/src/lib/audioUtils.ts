/**
 * Converts a WebM/Ogg audio Blob into a WAV Blob using the Web Audio API.
 * This avoids any server-side ffmpeg dependency.
 */
export async function convertToWav(audioBlob: Blob): Promise<Blob> {
  const arrayBuffer = await audioBlob.arrayBuffer();
  const audioCtx = new AudioContext();
  const decoded = await audioCtx.decodeAudioData(arrayBuffer);
  await audioCtx.close();

  const numChannels = decoded.numberOfChannels;
  const sampleRate = decoded.sampleRate;
  const numSamples = decoded.length;
  const bitsPerSample = 16;
  const byteRate = (sampleRate * numChannels * bitsPerSample) / 8;
  const blockAlign = (numChannels * bitsPerSample) / 8;
  const dataLength = numSamples * numChannels * (bitsPerSample / 8);
  const wavBuffer = new ArrayBuffer(44 + dataLength);
  const view = new DataView(wavBuffer);

  // ── WAV Header ──────────────────────────────────────────────────────────────
  const writeStr = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeStr(0, "RIFF");
  view.setUint32(4, 36 + dataLength, true);          // ChunkSize
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true);                       // Subchunk1Size (PCM)
  view.setUint16(20, 1, true);                        // AudioFormat (PCM = 1)
  view.setUint16(22, numChannels, true);              // NumChannels
  view.setUint32(24, sampleRate, true);               // SampleRate
  view.setUint32(28, byteRate, true);                 // ByteRate
  view.setUint16(32, blockAlign, true);               // BlockAlign
  view.setUint16(34, bitsPerSample, true);            // BitsPerSample
  writeStr(36, "data");
  view.setUint32(40, dataLength, true);               // Subchunk2Size

  // ── PCM Samples (interleaved channels, clamped to int16) ────────────────────
  let offset = 44;
  for (let i = 0; i < numSamples; i++) {
    for (let ch = 0; ch < numChannels; ch++) {
      const sample = decoded.getChannelData(ch)[i] || 0;
      const clamped = Math.max(-1, Math.min(1, sample));
      const int16 = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
      view.setInt16(offset, int16, true);
      offset += 2;
    }
  }

  return new Blob([wavBuffer], { type: "audio/wav" });
}
