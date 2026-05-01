import { useEffect, useRef } from "react";

interface LiveWaveformProps {
  stream: MediaStream | null;
  isRecording: boolean;
}

export function LiveWaveform({ stream, isRecording }: LiveWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    if (!stream || !isRecording || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Initialize AudioContext
    const audioCtx = new window.AudioContext();
    const analyser = audioCtx.createAnalyser();
    const source = audioCtx.createMediaStreamSource(stream);

    analyser.fftSize = 256;
    source.connect(analyser);

    audioCtxRef.current = audioCtx;
    analyserRef.current = analyser;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animationRef.current = requestAnimationFrame(draw);

      analyser.getByteFrequencyData(dataArray);

      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw bars
      const barWidth = (canvas.width / bufferLength) * 2.5;
      let barHeight = 0;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        barHeight = (dataArray[i] || 0) / 2;

        // Use primary theme color (teal)
        ctx.fillStyle = `hsl(173, 58%, 49%)`;
        
        // Draw centered vertically
        const y = canvas.height / 2 - barHeight / 2;
        
        // Add rounded corners
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth - 1, barHeight || 2, 2);
        ctx.fill();

        x += barWidth;
      }
    };

    draw();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (audioCtxRef.current?.state !== "closed") {
        audioCtxRef.current?.close();
      }
    };
  }, [stream, isRecording]);

  if (!isRecording) return null;

  return (
    <canvas
      ref={canvasRef}
      width={300}
      height={100}
      className="w-full h-[100px] opacity-80 transition-opacity"
    />
  );
}
