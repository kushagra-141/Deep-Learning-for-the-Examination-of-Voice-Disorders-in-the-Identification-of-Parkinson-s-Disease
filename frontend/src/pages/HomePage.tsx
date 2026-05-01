import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Mic, BarChart2, FlaskConical, Shield, ChevronRight, Activity } from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Card, CardContent } from "../components/ui/card";

const STATS = [
  { label: "Subjects", value: "31" },
  { label: "Recordings", value: "195" },
  { label: "Features", value: "22" },
  { label: "Classifiers", value: "8" },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    icon: Mic,
    title: "Record or Enter Features",
    desc: "Speak a sustained 'aahh' vowel for 5-10 seconds, or enter 22 acoustic voice features manually.",
    href: "/audio",
    cta: "Go to Audio →",
  },
  {
    step: "02",
    icon: FlaskConical,
    title: "Acoustic Feature Extraction",
    desc: "Our Praat engine extracts jitter, shimmer, harmonicity, and nonlinear dynamics from your voice.",
    href: null,
    cta: null,
  },
  {
    step: "03",
    icon: BarChart2,
    title: "Ensemble Classification",
    desc: "8 independently trained classifiers vote on the result. Soft-voting aggregates the final probability.",
    href: "/dashboard",
    cta: "See Analytics →",
  },
];

const FEATURES = [
  { icon: Shield, title: "Medical Disclaimer", desc: "Every result includes a prominently displayed disclaimer. Research only — never a diagnosis." },
  { icon: Activity, title: "Live Ensemble", desc: "8 models (KNN, SVM, LightGBM, XGBoost, Random Forest…) contribute to every prediction." },
  { icon: FlaskConical, title: "Oxford Dataset", desc: "Trained on 195 recordings from 31 subjects via the University of Oxford / NCVS collaboration." },
];

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* ── Hero ─────────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-background via-background to-primary/5 border-b">
        {/* Decorative blobs */}
        <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-primary/5 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-20 -left-20 h-72 w-72 rounded-full bg-primary/5 blur-3xl pointer-events-none" />

        <div className="container relative py-24 md:py-36 flex flex-col items-center text-center max-w-4xl mx-auto space-y-8">
          <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <Badge variant="outline" className="mb-4 text-xs px-4 py-1 rounded-full border-primary/30 text-primary">
              <span className="mr-1.5 h-2 w-2 rounded-full bg-primary inline-block animate-pulse" />
              Research Tool — Not a Medical Device
            </Badge>
          </motion.div>

          <motion.h1
            className="text-5xl md:text-7xl font-extrabold tracking-tighter text-balance leading-none"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            Voice-Based{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-teal-400">
              Parkinson's
            </span>{" "}
            Detection
          </motion.h1>

          <motion.p
            className="text-xl text-muted-foreground max-w-2xl text-balance"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            An ensemble of 8 machine learning classifiers trained on acoustic voice biomarkers to assist
            research into early detection of Parkinson's disease.
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row gap-4"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Button asChild size="lg" className="h-12 px-8 text-base font-semibold rounded-full shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-shadow">
              <Link to="/audio">
                <Mic className="mr-2 h-5 w-5" />
                Record Your Voice
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="h-12 px-8 text-base font-semibold rounded-full">
              <Link to="/predict">
                Enter Features Manually
                <ChevronRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </motion.div>

          {/* Stats strip */}
          <motion.div
            className="grid grid-cols-4 divide-x divide-border border rounded-2xl overflow-hidden bg-card w-full max-w-lg mx-auto mt-8"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            {STATS.map((s) => (
              <div key={s.label} className="flex flex-col items-center py-4">
                <span className="text-2xl font-black text-primary">{s.value}</span>
                <span className="text-xs text-muted-foreground">{s.label}</span>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── How it Works ─────────────────────────────────────────────────────── */}
      <section className="container py-24 max-w-5xl mx-auto">
        <motion.div
          className="text-center mb-16 space-y-3"
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <Badge variant="outline">How it Works</Badge>
          <h2 className="text-3xl font-bold tracking-tight">From voice to verdict in seconds</h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            A fully automated pipeline powered by Oxford Praat acoustic analysis and scikit-learn.
          </p>
        </motion.div>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-8"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {HOW_IT_WORKS.map((item) => (
            <motion.div key={item.step} variants={itemVariants}>
              <Card className="h-full hover:shadow-md hover:border-primary/20 transition-all duration-300 group">
                <CardContent className="p-6 flex flex-col gap-4 h-full">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-black text-primary/40 tabular-nums">{item.step}</span>
                    <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors duration-300">
                      <item.icon className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
                    <p className="text-muted-foreground text-sm leading-relaxed">{item.desc}</p>
                  </div>
                  {item.cta && item.href && (
                    <Link to={item.href} className="text-primary text-sm font-medium hover:underline flex items-center gap-1 mt-2">
                      {item.cta}
                    </Link>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── Features ─────────────────────────────────────────────────────────── */}
      <section className="bg-muted/30 border-y py-24">
        <div className="container max-w-5xl mx-auto">
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            {FEATURES.map((f) => (
              <motion.div key={f.title} variants={itemVariants} className="flex gap-4">
                <div className="shrink-0 mt-1 p-2 h-fit rounded-lg bg-primary/10 text-primary">
                  <f.icon className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">{f.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────────────── */}
      <section className="container py-24 max-w-3xl mx-auto text-center space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="space-y-6"
        >
          <h2 className="text-4xl font-extrabold tracking-tight">Ready to analyze?</h2>
          <p className="text-muted-foreground">
            Start with a 5-second voice recording or manually enter extracted acoustic features.
          </p>
          <div className="flex justify-center gap-4 flex-wrap">
            <Button asChild size="lg" className="rounded-full px-8">
              <Link to="/audio"><Mic className="mr-2 h-4 w-4" />Try Audio Mode</Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="rounded-full px-8">
              <Link to="/dashboard"><BarChart2 className="mr-2 h-4 w-4" />View Analytics</Link>
            </Button>
          </div>
        </motion.div>
      </section>
    </div>
  );
}
