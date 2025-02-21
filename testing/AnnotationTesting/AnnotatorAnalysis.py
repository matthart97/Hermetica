import json
import matplotlib.pyplot as plt
import os

# Load the annotation results
annotations_file = "chebi_annotations.json"  # Ensure this file exists before running the script

if not os.path.exists(annotations_file):
    print(f"Error: {annotations_file} not found. Please generate annotations first.")
    exit()

with open(annotations_file, "r", encoding="utf-8") as f:
    results = json.load(f)

# Initialize counters
total_sentences = len(results)
sentences_with_annotations = 0
total_annotations = 0
annotations_per_sentence = []

# Evaluate the results
for item in results:
    sentence = item["original_sentence"]
    annotations = item["annotations"]

    if annotations:
        sentences_with_annotations += 1
        total_annotations += len(annotations)

    annotations_per_sentence.append(len(annotations))

# Compute key metrics
coverage = (sentences_with_annotations / total_sentences) * 100

# Ensure we have valid data before plotting
if total_sentences == 0:
    print("No sentences found in the dataset.")
    exit()

# 📊 Histogram: Distribution of Annotations per Sentence
plt.figure(figsize=(10, 5))
plt.hist(annotations_per_sentence, bins=range(0, max(annotations_per_sentence) + 2), alpha=0.7, edgecolor='black')
plt.xlabel("Number of Annotations per Sentence")
plt.ylabel("Frequency")
plt.title("Distribution of Annotations per Sentence")
plt.xticks(range(0, max(annotations_per_sentence) + 1))
plt.grid(axis='y', linestyle='--', alpha=0.7)
histogram_path = "annotations_histogram.png"
plt.savefig(histogram_path)  # Save image
plt.close()

# 📊 Pie Chart: Sentences with vs. without Annotations
plt.figure(figsize=(6, 6))
labels = ["Sentences with Annotations", "Sentences without Annotations"]
sizes = [sentences_with_annotations, total_sentences - sentences_with_annotations]
colors = ['skyblue', 'lightcoral']
plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140, wedgeprops={"edgecolor": "black"})
plt.title("Percentage of Sentences with Annotations")
piechart_path = "annotations_piechart.png"
plt.savefig(piechart_path)  # Save image
plt.close()

# Print results summary
print("\n===== Annotation Metrics =====")
print(f"Total Sentences: {total_sentences}")
print(f"Sentences with at least one annotation: {sentences_with_annotations} ({coverage:.2f}%)")
print(f"Total Annotations Found: {total_annotations}")
print(f"Mean Annotations per Sentence: {total_annotations / total_sentences:.2f}")

print(f"\n📊 Graphs Saved:")
print(f"   - Histogram: {histogram_path}")
print(f"   - Pie Chart: {piechart_path}")
