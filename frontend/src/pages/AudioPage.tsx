import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Square, Upload, Loader2, AlertCircle, RefreshCw, Activity } from "lucide-react";
import { predictAudio } from "../api/client";
import { convertToWav } from "../lib/audioUtils";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { LiveWaveform } from "../components/prediction/LiveWaveform";
import { LLMExplanation } from "../components/prediction/LLMExplanation";

export default function AudioPage() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const [isConverting, setIsConverting] = useState(false);

  const mutation = useMutation({
    mutationFn: predictAudio,
  });

  const startRecording = async () => {
    try {
      setPermissionError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      
      setMediaStream(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
        setMediaStream(null);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = window.setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= 29) {
            stopRecording();
            return 30;
          }
          return prev + 1;
        });
      }, 1000);

    } catch (err) {
      console.error("Error accessing microphone:", err);
      setPermissionError("Microphone permission denied or device not found. Please use the upload fallback.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioBlob(file);
      setRecordingTime(0);
    }
  };

  const handleSubmit = async () => {
    if (!audioBlob) return;
    setIsConverting(true);
    try {
      const wavBlob = await convertToWav(audioBlob);
      mutation.mutate(wavBlob);
    } catch (err) {
      console.error("WAV conversion failed:", err);
      mutation.mutate(audioBlob);
    } finally {
      setIsConverting(false);
    }
  };

  const handleReset = () => {
    setAudioBlob(null);
    mutation.reset();
    setRecordingTime(0);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="container py-12 max-w-3xl mx-auto space-y-8">
      <motion.div 
        className="space-y-2 text-center"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-4xl font-extrabold tracking-tight">Audio Analysis</h1>
        <p className="text-muted-foreground text-lg">
          Record or upload a 5-10 second clip of yourself saying a sustained "aahh" vowel sound.
        </p>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <Card className="border-2 shadow-sm overflow-hidden">
          <CardHeader className="text-center pb-4 bg-muted/20 border-b">
            <CardTitle>Live Recording</CardTitle>
            <CardDescription>
              Hold the vowel sound steady. Recording will automatically stop at 30 seconds.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center py-10 space-y-8 relative">
            
            <AnimatePresence mode="popLayout">
              {isRecording && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 100 }}
                  exit={{ opacity: 0, height: 0 }}
                  className="w-full absolute top-8 left-0 px-8"
                >
                  <LiveWaveform stream={mediaStream} isRecording={isRecording} />
                </motion.div>
              )}
            </AnimatePresence>

            <motion.div 
              className={`relative flex items-center justify-center w-36 h-36 rounded-full transition-colors duration-500 ${isRecording ? "bg-primary/5" : "bg-muted/30"}`}
              layout
            >
              {isRecording && (
                <>
                  <div className="absolute inset-0 rounded-full animate-ping bg-primary/20" style={{ animationDuration: "3s" }} />
                  <div className="absolute inset-2 rounded-full animate-ping bg-primary/10" style={{ animationDuration: "2s" }} />
                </>
              )}
              <div className={`text-5xl font-mono z-10 transition-colors ${isRecording ? "text-primary font-bold" : "text-foreground"}`}>
                {formatTime(recordingTime)}
              </div>
            </motion.div>

            <div className="flex gap-4">
              {!isRecording ? (
                <Button size="lg" onClick={startRecording} className="rounded-full h-16 w-16 p-0 shadow-lg shadow-primary/20 transition-transform hover:scale-105 active:scale-95">
                  <Mic className="h-7 w-7" />
                </Button>
              ) : (
                <Button size="lg" onClick={stopRecording} variant="destructive" className="rounded-full h-16 w-16 p-0 shadow-lg shadow-destructive/20 transition-transform hover:scale-105 active:scale-95">
                  <Square className="h-6 w-6 fill-current" />
                </Button>
              )}
            </div>

            {permissionError && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 text-sm text-destructive mt-4 p-3 bg-destructive/10 rounded-md w-full max-w-sm"
              >
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{permissionError}</span>
              </motion.div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground uppercase font-semibold">
        <div className="h-px bg-border w-16"></div>
        <span>OR</span>
        <div className="h-px bg-border w-16"></div>
      </div>

      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle>Upload Recording</CardTitle>
            <CardDescription>Already have a .wav or .webm file? Upload it directly.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid w-full items-center gap-1.5">
              <input 
                id="audio-upload" 
                type="file" 
                accept="audio/*" 
                onChange={handleUpload}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 hover:bg-muted/30 transition-colors"
              />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <AnimatePresence>
        {audioBlob && (
          <motion.div
            initial={{ opacity: 0, height: 0, y: 20 }}
            animate={{ opacity: 1, height: "auto", y: 0 }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <Card className="border-primary/20 bg-primary/5 shadow-md mt-8">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-primary" /> Ready to Analyze
                </CardTitle>
                <CardDescription>Audio clip ({Math.round(audioBlob.size / 1024)} KB) is staged for processing.</CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  size="lg" 
                  className="w-full text-lg shadow-lg shadow-primary/10" 
                  onClick={handleSubmit}
                  disabled={mutation.isPending || isConverting}
                >
                  {isConverting ? (
                    <><Loader2 className="mr-2 h-5 w-5 animate-spin" />Converting to WAV...</>
                  ) : mutation.isPending ? (
                    <><Loader2 className="mr-2 h-5 w-5 animate-spin" />Extracting Acoustic Features...</>
                  ) : (
                    <><Upload className="mr-2 h-5 w-5" />Analyze Audio</>
                  )}
                </Button>
                <Button variant="ghost" size="sm" className="w-full mt-2" onClick={handleReset} disabled={mutation.isPending}>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Discard and try another
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {mutation.isError && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <Card className="border-destructive/50 bg-destructive/5 shadow-sm mt-8">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 text-destructive font-semibold mb-2">
                  <AlertCircle className="h-5 w-5" />
                  Processing Failed
                </div>
                <p className="text-sm text-destructive/90">{mutation.error.message}</p>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {mutation.isSuccess && mutation.data && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <Card className="border-success/50 bg-success/5 overflow-hidden shadow-md mt-8">
              <div className="bg-success text-success-foreground p-3 text-center text-sm font-bold tracking-widest">
                ANALYSIS COMPLETE
              </div>
              <CardContent className="p-8 text-center space-y-4">
                <h3 className="text-2xl font-bold text-foreground">
                  Ensemble Prediction
                </h3>
                <motion.div 
                  className="text-7xl font-black text-success py-4"
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: "spring", stiffness: 200, damping: 15 }}
                >
                  {(mutation.data.ensemble.probability * 100).toFixed(1)}%
                </motion.div>
                <p className="text-muted-foreground uppercase text-sm font-semibold tracking-wider">
                  Probability of Parkinson's
                </p>
                <div className="w-full bg-muted rounded-full h-2 mt-6 overflow-hidden max-w-sm mx-auto">
                  <motion.div
                    className="h-full rounded-full bg-success"
                    initial={{ width: 0 }}
                    animate={{ width: `${(mutation.data.ensemble.probability * 100)}%` }}
                    transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
                  />
                </div>
                <div className="text-xs text-muted-foreground mt-8 max-w-sm mx-auto leading-relaxed border-t border-success/20 pt-4">
                  {mutation.data.disclaimer}
                </div>

                <div className="mt-4 text-left max-w-xl mx-auto">
                  {/* For AudioPage, we pass an empty object for features for now, or we could pass the actual extracted features if they were returned in the API, but since the LLM explain schema only expects what it receives, we can pass what we have. wait, mutation.data doesn't return the raw features right now. It just returns per_model. Let's pass empty record. */}
                  <LLMExplanation 
                    features={{}} 
                    probability={mutation.data.ensemble.probability} 
                    inputMode="audio" 
                  />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
