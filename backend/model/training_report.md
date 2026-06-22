# AI Voice Detection - Training Report

**Generated:** 2026-06-22 11:09:53

**Best Model:** Random Forest


## Dataset Information

- **Total Samples:** 1000
- **Human Samples:** 500
- **AI Samples:** 500
- **Feature Dimensions:** 69
- **Train/Test Split:** 80/20

## Features Extracted (69 Dimensions)

| Category | Dimensions | Description |
|----------|------------|-------------|
| MFCC (mean + std) | 26 | Spectral envelope shape |
| Spectral Centroid (mean + std) | 2 | Spectral brightness center |
| Spectral Bandwidth (mean + std) | 2 | Width of spectral distribution |
| Zero Crossing Rate (mean + std) | 2 | Temporal crossing frequency |
| RMS Energy (mean + std) | 2 | Amplitude strength |
| Chroma (mean) | 12 | Harmonic pitch class energy |
| Pitch (mean, var, range, jitter, shimmer) | 5 | Fundamental frequency metrics |
| Spectral Contrast (mean + std of 6 bands) | 12 | Subband energy dynamic range |
| Spectral Roll-off (mean + std) | 2 | High frequency energy threshold |
| Voice Stability | 1 | Micro-perturbation resistance factor |
| Prosody score | 1 | Pitch variability ratio |
| Speaking Rate | 1 | Syllables/peaks per second |
| Pause frequency | 1 | Ratio of silent frames |
| **Total Features** | **69** | |

## Feature Importance Analysis (Top 15 Features)

| Rank | Feature Index / Name | Importance Score |
|------|---------------------|------------------|
| 1 | contrast_std_3 | 0.09538 |
| 2 | contrast_std_0 | 0.08594 |
| 3 | pause_frequency | 0.08509 |
| 4 | contrast_std_4 | 0.08097 |
| 5 | rolloff_std | 0.07788 |
| 6 | prosody_score | 0.06804 |
| 7 | contrast_std_1 | 0.06584 |
| 8 | contrast_std_2 | 0.06372 |
| 9 | contrast_std_5 | 0.06031 |
| 10 | mfcc_std_4 | 0.04732 |
| 11 | mfcc_std_2 | 0.04175 |
| 12 | mfcc_std_8 | 0.02745 |
| 13 | mfcc_std_6 | 0.02691 |
| 14 | mfcc_std_3 | 0.02342 |
| 15 | mfcc_std_5 | 0.02157 |

## Model Comparison

| Model | Accuracy | Precision | Recall | F1 Score | Train Time |
|-------|----------|-----------|--------|----------|------------|
| Random Forest ⭐ | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.70s |
| XGBoost | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.18s |
| LightGBM | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.14s |
| Gradient Boosting | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.07s |

## Best Model: Random Forest

### Classification Report

```
              precision    recall  f1-score   support

       Human       1.00      1.00      1.00       100
          AI       1.00      1.00      1.00       100

    accuracy                           1.00       200
   macro avg       1.00      1.00      1.00       200
weighted avg       1.00      1.00      1.00       200

```

### Confusion Matrix

```
                Predicted Human    Predicted AI
Actual Human           100                0
Actual AI                0              100
```

### ROC Curve Data

- **AUC Score:** 1.0000

## Calibrated Decision Thresholds

- **Likely AI Generated Voice:** Probability >= 0.55

- **Uncertain / Mixed Signals:** 0.30 <= Probability < 0.55

- **Likely Human Voice:** Probability < 0.30

