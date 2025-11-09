from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
import numpy as np

def cluster_articles(embeddings, articles, threshold=0.6):
    """
    Group similar articles based on embedding similarity.
    Returns a list of clusters, where each cluster is a list of article dicts.
    """
    if len(embeddings) <= 1:
        return [articles]

    # compute similarity matrix
    sims = cosine_similarity(embeddings)
    
    # cluster based on similarity threshold
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=1 - threshold,  # convert similarity to distance
        metric="cosine",
        linkage="average"
    )
    labels = clustering.fit_predict(embeddings)

    # group by cluster
    clusters = {}
    for label, article in zip(labels, articles):
        clusters.setdefault(label, []).append(article)

    return list(clusters.values())
