import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
import json
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
import os

def ks_stat(y_true, y_score):
    order = np.argsort(y_score)
    y = np.array(y_true)[order]
    if y.sum()==0 or (len(y)-y.sum())==0:
        return 0.0
    cum_pos = np.cumsum(y) / y.sum()
    cum_neg = np.cumsum(1 - y) / (len(y)-y.sum())
    return float(np.max(np.abs(cum_pos - cum_neg)))

def eval_all(y_true, y_score):
    out = {
        "roc_auc": float(roc_auc_score(y_true, y_score)),
        "pr_auc": float(average_precision_score(y_true, y_score)),
        "brier": float(brier_score_loss(y_true, y_score)),
        "ks": ks_stat(y_true, y_score)
    }
    return out

def save_metrics_plot(y_true, y_score, outdir="reports/figures", suffix=None):
    """Save model evaluation plots
    
    Args:
        y_true: True labels
        y_score: Predicted scores
        outdir: Output directory for plots
        suffix: Optional suffix for filenames (e.g., model version)
    """
    os.makedirs(outdir, exist_ok=True)
    
    # Add suffix to filenames if provided
    if suffix:
        calibration_filename = f"calibration_{suffix}.png"
        roc_filename = f"roc_{suffix}.png"
        pr_filename = f"pr_{suffix}.png"
    else:
        calibration_filename = "calibration.png"
        roc_filename = "roc.png"
        pr_filename = "pr.png"
    
    # Calibration plot
    prob_true, prob_pred = calibration_curve(y_true, y_score, n_bins=10, strategy='quantile')
    plt.figure()
    plt.plot(prob_pred, prob_true, marker='o')
    plt.plot([0,1],[0,1],'--')
    plt.xlabel("Predicted")
    plt.ylabel("Observed")
    plt.title(f"Calibration{' - ' + suffix if suffix else ''}")
    plt.savefig(os.path.join(outdir, calibration_filename), dpi=150)
    plt.close()

    # ROC curve
    from sklearn.metrics import RocCurveDisplay, PrecisionRecallDisplay
    plt.figure()
    RocCurveDisplay.from_predictions(y_true, y_score)
    plt.title(f"ROC Curve{' - ' + suffix if suffix else ''}")
    plt.savefig(os.path.join(outdir, roc_filename), dpi=150)
    plt.close()

    # Precision-Recall curve
    plt.figure()
    PrecisionRecallDisplay.from_predictions(y_true, y_score)
    plt.title(f"Precision-Recall Curve{' - ' + suffix if suffix else ''}")
    plt.savefig(os.path.join(outdir, pr_filename), dpi=150)
    plt.close()
