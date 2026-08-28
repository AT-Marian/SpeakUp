from sklearn.metrics import confusion_matrix

def evaluate_thesis_metrics():
    # ---------------------------------------------------------
    # TEST DATASET FOR YOUR THESIS REPORT
    # 1 = Error exists (Positive class)
    # 0 = Correct sentence (Negative class)
    # ---------------------------------------------------------
    # Replace these numbers with the actual results from testing 
    # your SpeakUp GrammarCheckService against your test sentences!
    y_true = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1]
    y_pred = [1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1]

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    # Mathematical formulas matching your supervisor's confusion matrix picture
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0  # Also known as Recall
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0

    print("==================================================")
    print("     SPEAKUP THESIS CONFUSION MATRIX METRICS      ")
    print("==================================================")
    print(f"True Positives  (TP) : {tp}")
    print(f"False Positives (FP) : {fp}  [Type I Error]")
    print(f"False Negatives (FN) : {fn}  [Type II Error]")
    print(f"True Negatives  (TN) : {tn}")
    print("--------------------------------------------------")
    print(f"Precision     = TP / (TP + FP)       = {precision:.4f} ({precision*100:.2f}%)")
    print(f"Sensitivity   = TP / (TP + FN)       = {sensitivity:.4f} ({sensitivity*100:.2f}%)")
    print(f"Specificity   = TN / (TN + FP)       = {specificity:.4f} ({specificity*100:.2f}%)")
    print(f"Accuracy      = (TP+TN) / Total      = {accuracy:.4f} ({accuracy*100:.2f}%)")
    print("==================================================")

if __name__ == "__main__":
    evaluate_thesis_metrics()