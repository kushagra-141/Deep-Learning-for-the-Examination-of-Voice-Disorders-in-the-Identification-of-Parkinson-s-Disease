import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";

const FEATURE_GLOSSARY = [
  { name: "MDVP:Fo(Hz)", desc: "Average vocal fundamental frequency" },
  { name: "MDVP:Fhi(Hz)", desc: "Maximum vocal fundamental frequency" },
  { name: "MDVP:Flo(Hz)", desc: "Minimum vocal fundamental frequency" },
  { name: "MDVP:Jitter(%)", desc: "MDVP jitter in percentage" },
  { name: "MDVP:Jitter(Abs)", desc: "MDVP absolute jitter in microseconds" },
  { name: "MDVP:RAP", desc: "MDVP relative amplitude perturbation" },
  { name: "MDVP:PPQ", desc: "Five-point period perturbation quotient" },
  { name: "Jitter:DDP", desc: "Average absolute difference of differences between jitter cycles" },
  { name: "MDVP:Shimmer", desc: "MDVP local shimmer" },
  { name: "MDVP:Shimmer(dB)", desc: "MDVP local shimmer in dB" },
  { name: "Shimmer:APQ3", desc: "Three-point amplitude perturbation quotient" },
  { name: "Shimmer:APQ5", desc: "Five-point amplitude perturbation quotient" },
  { name: "MDVP:APQ", desc: "11-point amplitude perturbation quotient" },
  { name: "Shimmer:DDA", desc: "Average absolute differences between the amplitudes of consecutive periods" },
  { name: "NHR", desc: "Noise-to-harmonics ratio" },
  { name: "HNR", desc: "Harmonics-to-noise ratio" },
  { name: "RPDE", desc: "Recurrence period density entropy" },
  { name: "DFA", desc: "Detrended fluctuation analysis" },
  { name: "spread1", desc: "Nonlinear measure of fundamental frequency variation 1" },
  { name: "spread2", desc: "Nonlinear measure of fundamental frequency variation 2" },
  { name: "D2", desc: "Correlation dimension" },
  { name: "PPE", desc: "Pitch period entropy" }
];

export default function AboutPage() {
  return (
    <div className="container py-12 max-w-4xl mx-auto space-y-12">
      <div className="space-y-4 text-center">
        <Badge variant="outline" className="mb-2">Project Documentation</Badge>
        <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">About the Project</h1>
        <p className="text-xl text-muted-foreground text-balance">
          A machine learning architecture exploring the correlation between acoustic voice dimensions and Parkinson's disease.
        </p>
      </div>

      <div className="prose prose-stone dark:prose-invert max-w-none">
        <Card className="shadow-sm border-primary/10">
          <CardHeader>
            <CardTitle>Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-muted-foreground leading-relaxed">
            <p>
              This application implements a multi-model ensemble system designed to classify acoustic voice recordings into healthy and Parkinson's disease profiles. It is built strictly for **educational and research purposes** and demonstrates full-stack machine learning deployment paradigms.
            </p>
            <p>
              The system uses 9 distinct classifiers (ranging from Random Forests and XGBoost to Support Vector Machines) stacked into a meta-ensemble. It automatically calibrates probabilities using Isotonic Regression and provides real-time interpretability via SHAP (SHapley Additive exPlanations).
            </p>
          </CardContent>
        </Card>

        <h2 className="text-2xl font-bold mt-12 mb-4 tracking-tight">The Dataset</h2>
        <p className="text-muted-foreground mb-6">
          The models are trained on the "Parkinson's Disease Classification" dataset originally created by Max Little of the University of Oxford, in collaboration with the National Centre for Voice and Speech, Denver, Colorado.
        </p>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 list-none p-0">
          <li className="bg-muted/30 p-4 rounded-lg border border-border">
            <strong className="block text-foreground mb-1">Subjects</strong>
            <span className="text-sm text-muted-foreground">31 people (23 with Parkinson's, 8 healthy).</span>
          </li>
          <li className="bg-muted/30 p-4 rounded-lg border border-border">
            <strong className="block text-foreground mb-1">Recordings</strong>
            <span className="text-sm text-muted-foreground">195 sustained vowel 'a' phonations (6 per subject).</span>
          </li>
        </ul>

        <h2 className="text-2xl font-bold mt-12 mb-4 tracking-tight">Feature Glossary</h2>
        <p className="text-muted-foreground mb-4">
          The application extracts 22 distinct acoustic dimensions. These are categorized into Frequency, Jitter, Shimmer, Harmonicity, and Nonlinear metrics.
        </p>
        
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm text-left">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-3 font-semibold w-1/3">Feature Identifier</th>
                <th className="px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {FEATURE_GLOSSARY.map((feat) => (
                <tr key={feat.name} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-primary">{feat.name}</td>
                  <td className="px-4 py-3 text-muted-foreground">{feat.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h2 className="text-2xl font-bold mt-12 mb-4 tracking-tight text-destructive">Limitations & Disclaimer</h2>
        <Card className="border-destructive/20 bg-destructive/5 mb-8">
          <CardContent className="p-6 space-y-4 text-sm text-destructive/90">
            <p><strong>This software is not a medical device.</strong> It must never be used to diagnose, treat, or monitor any clinical condition.</p>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong>Dataset Bias:</strong> The training dataset consists of only 31 individuals from a specific geographic and demographic slice. It does not perfectly generalize to the global population.</li>
              <li><strong>Class Imbalance:</strong> With only 8 healthy subjects in the reference data, the models exhibit a bias toward higher recall at the expense of precision.</li>
              <li><strong>Acoustic Limitations:</strong> Voice degradation can be caused by hundreds of non-Parkinsonian conditions (e.g., laryngitis, smoking, general aging) which the models cannot distinguish from PD.</li>
            </ul>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
