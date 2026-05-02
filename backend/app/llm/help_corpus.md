# Parkinson's Voice Detection — Help Corpus

> Authoritative answers for the in-app help bot. The bot may not state anything
> outside this corpus; if it doesn't know, it says so and points to /about.

## What is this app?
A research demonstration that classifies a voice recording as more or less
consistent with patterns observed in the UCI Parkinson's voice dataset (195
recordings, 22 acoustic features). It is **not** a diagnostic device.

## Is this a diagnosis?
No. The output is a probability from a small machine-learning ensemble trained
on a public research dataset. It cannot be used to diagnose, screen for, or
rule out Parkinson's disease. Always consult a qualified neurologist for
medical concerns.

## How do I use the Predict page?
Open `/predict` and either click "Load Sample" to fill the form with a random
dataset row, or enter your own 22 acoustic features and click "Run Prediction".
The result card shows the ensemble probability, per-model breakdown, and the
top SHAP contributors that drove the score.

## How do I use the Audio page?
Open `/audio`, click "Start Recording", read the prompt aloud for ~3 seconds,
then click "Stop". The backend extracts 22 acoustic features from the audio
and runs the same ensemble. On iOS Safari, file upload is the supported
fallback because of microphone permission quirks.

## How do I use the Batch page?
Open `/batch`, drag in a CSV containing the 22 feature columns (header row
required). The job runs server-side and you can download a CSV with the
predictions appended once it completes. Maximum 10,000 rows / 2 MB per file.

## What is jitter?
Jitter measures cycle-to-cycle variation in the fundamental frequency of the
voice. Higher jitter often correlates with vocal-fold instability. The dataset
exposes several jitter variants: `MDVP:Jitter(%)`, `MDVP:Jitter(Abs)`,
`MDVP:RAP`, `MDVP:PPQ`, `Jitter:DDP`.

## What is shimmer?
Shimmer measures cycle-to-cycle variation in amplitude (loudness). Higher
shimmer can indicate breathiness or instability. Variants: `MDVP:Shimmer`,
`MDVP:Shimmer(dB)`, `Shimmer:APQ3`, `Shimmer:APQ5`, `MDVP:APQ`, `Shimmer:DDA`.

## What is HNR / NHR?
- **HNR** (Harmonics-to-Noise Ratio): how harmonic the voice is, in dB.
  Higher = cleaner.
- **NHR** (Noise-to-Harmonics Ratio): the inverse-ish of HNR, lower is
  cleaner.

## What are the nonlinear features?
- **RPDE** (Recurrence Period Density Entropy): regularity of vocal cycles.
- **DFA** (Detrended Fluctuation Analysis): scaling exponent of stochastic
  self-similarity in voice noise.
- **spread1, spread2, D2, PPE**: nonlinear measures of fundamental-frequency
  variation. PPE (Pitch Period Entropy) is often the strongest single feature
  for this dataset.

## What's the difference between the models?
The app trains nine classifiers (k-NN, SVM, Decision Tree, Bagging, LightGBM,
AdaBoost, Random Forest, XGBoost, and a PCA→Random-Forest pipeline). The
ensemble is a soft-vote average of their probabilities. Different models
trade off precision and recall differently — see `/dashboard` for live metrics.

## Why is one model called "primary"?
SHAP values are computed for one tree-based primary model (LightGBM by
default) because tree explainers are fast and exact. The ensemble probability
itself is averaged across all nine.

## Where does the data come from?
The UCI Parkinson's voice dataset (Little et al., 2007) — 195 recordings, 31
subjects, 22 acoustic features. It is small, demographically narrow, and
collected in a single research lab; results do not generalise to all voices,
languages, or recording conditions.

## What do you do with my voice?
Audio is processed on the backend to extract the 22 features and is not
retained. Feature values may be sent to the LLM provider as part of the
chat context — they are acoustic measurements, not raw audio.

## Why does the chat sometimes say it can't help?
The chat is grounded only in your prediction and the dataset. Off-topic or
medical-advice requests are refused on purpose. For app questions, this help
bot is the right tool.

## Where can I learn more?
Open `/about` for the dataset reference, model details, limitations, and the
research paper this work derives from.
