from sklearn.metrics import confusion_matrix, precision_score, recall_score, accuracy_score

# 1. Define your test dataset results
# 1 = Error exists, 0 = Sentence is grammatically correct
y_true = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1]  # Actual labels (human gold standard)
y_pred = [1, 0, 0, 1, 0, 1, 1, 0, 1, 0]  # What your Gemini GrammarCheckService predicted

# 2. Compute the Confusion Matrix components
tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

print("--- Confusion Matrix Breakdown ---")
print(f"True Positives (TP): {tp}")
print(f"False Positives (FP): {fp}")
print(f"False Negatives (FN): {fn}")
print(f"True Negatives (TN): {tn}")

# 3. Calculate Evaluation Metrics for your Thesis Report
accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred)
sensitivity = recall_score(y_true, y_pred) # Sensitivity / Recall

print("\n--- Evaluation Metrics ---")
print(f"Accuracy:    {accuracy:.2f}")
print(f"Precision:   {precision:.2f}")
print(f"Sensitivity: {sensitivity:.2f}")