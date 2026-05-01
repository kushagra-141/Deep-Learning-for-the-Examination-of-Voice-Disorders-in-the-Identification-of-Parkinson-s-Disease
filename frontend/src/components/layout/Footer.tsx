import { Heart, Activity } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border bg-muted/40 py-8">
      <div className="container flex flex-col items-center justify-between gap-6 md:h-16 md:flex-row">
        <div className="flex flex-col items-center gap-2 md:items-start">
          <div className="flex items-center gap-2 font-semibold text-foreground">
            <Activity className="h-4 w-4 text-primary" />
            Parkinson's AI
          </div>
          <p className="text-center text-xs leading-loose text-muted-foreground md:text-left max-w-md">
            Built for research and educational demonstration. Not for clinical diagnosis. 
            All voice data is processed ephemerally and never permanently stored.
          </p>
        </div>
        
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-muted/80 text-xs">
            Made with <Heart className="h-3 w-3 text-destructive fill-destructive" /> by Kushagra
          </div>
          <span className="text-border hidden sm:inline">|</span>
          <a 
            href="https://github.com/Kushagra-141/Deep-Learning-for-the-Examination-of-Voice-Disorders-in-the-Identification-of-Parkinson-s-Disease" 
            target="_blank" 
            rel="noreferrer"
            className="hover:text-foreground hover:underline underline-offset-4 transition-colors"
          >
            Source Code
          </a>
        </div>
      </div>
    </footer>
  );
}
