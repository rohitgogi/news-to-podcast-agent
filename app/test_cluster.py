from app.cluster import cluster_articles
import numpy as np

# mock embeddings (2 similar, 1 different)
embeddings = np.array([
    [0.9, 0.1, 0.2],   # story A
    [0.88, 0.12, 0.18],# same story A (almost identical)
    [0.1, 0.8, 0.5],   # story B (very different)
])

# generated tests
articles = [
    {"title": "FAA cuts flights due to shutdown", "text": "FAA orders airlines to reduce flights due to government shutdown."},
    {"title": "Government shutdown impacts air travel", "text": "Airlines are cutting flights because of the ongoing shutdown."},
    {"title": "New AI model released", "text": "OpenAI released GPT-4o Mini for faster reasoning tasks."}
]

clusters = cluster_articles(embeddings, articles)

print(f"number of clusters: {len(clusters)}")
for i, c in enumerate(clusters, 1):
    print(f"\nCluster {i}: {[a['title'] for a in c]}")
