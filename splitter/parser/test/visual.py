import chromadb
from chromadb.config import Settings
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# Path to Chroma vectorstore
DB_PATH = "/home/cm36/Updated-LLM-Project/vectorstores/KG/chunk_size_high"

# Initialize Chroma client
client = chromadb.PersistentClient(path=DB_PATH)

# Collection name
collection_name = "kg1"

# Function to retrieve embeddings and metadata
def retrieve_embeddings_and_metadata_from_chroma():
    try:
        collection = client.get_collection(name=collection_name)
        print(f"Collection '{collection_name}' accessed successfully in {DB_PATH}.")

        results = collection.peek(limit=10000)  # Retrieve more data
        if results and 'embeddings' in results and 'metadatas' in results:
            embeddings = np.array(results['embeddings'])
            metadata = results['metadatas']
            print(f"Retrieved {len(embeddings)} embeddings and metadata from the collection.")
            return embeddings, metadata
        else:
            print(f"No embeddings or metadata found in the collection '{collection_name}'")
            return None, None

    except Exception as e:
        print(f"Error accessing collection '{collection_name}': {e}")
        return None, None

# Retrieve embeddings and metadata
embeddings, metadata = retrieve_embeddings_and_metadata_from_chroma()

if embeddings is not None and embeddings.shape[0] > 1:
    # Standardize embeddings before clustering
    scaler = StandardScaler()
    normalized_embeddings = scaler.fit_transform(embeddings)

    # Reduce dimensions using t-SNE for visualization
    tsne = TSNE(n_components=2, perplexity=30, learning_rate=200, random_state=42)
    reduced_embeddings = tsne.fit_transform(normalized_embeddings)

    # Perform K-means clustering
    n_clusters = 15  # Adjust clusters as needed
    kmeans = KMeans(n_clusters=n_clusters, init='k-means++', max_iter=500, random_state=42)
    labels = kmeans.fit_predict(normalized_embeddings)

    # Assign cluster labels based on metadata
    cluster_labels = {}
    cluster_color_map = {}
    unique_colors = plt.cm.viridis(np.linspace(0, 1, n_clusters))

    for cluster_id in range(n_clusters):
        cluster_metadata = [metadata[i].get("document_title", "Unknown") for i in range(len(metadata)) if labels[i] == cluster_id]
        most_common_label = Counter(cluster_metadata).most_common(1)[0][0]
        cluster_labels[cluster_id] = most_common_label
        cluster_color_map[most_common_label] = unique_colors[cluster_id]  # Assign colors based on cluster

    # Visualization
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(
        reduced_embeddings[:, 0],
        reduced_embeddings[:, 1],
        c=labels,
        cmap='viridis',
        alpha=0.6,
        edgecolors="black"
    )

    plt.title("K-means Clustering of Embeddings (Labeled by Metadata)", fontsize=14)
    plt.xlabel("t-SNE Dimension 1", fontsize=12)
    plt.ylabel("t-SNE Dimension 2", fontsize=12)

    # Create a legend mapping colors to document titles
    legend_patches = [plt.Line2D([0], [0], marker='o', color='w', label=label, 
                                  markersize=8, markerfacecolor=color) 
                      for label, color in cluster_color_map.items()]

    # Move the legend outside of the plot (to the right)
    plt.legend(handles=legend_patches, title="Document Titles", loc="upper left", bbox_to_anchor=(1.05, 1), fontsize=6)

    plt.colorbar(scatter, label="Cluster")
    plt.grid(True)

    # Save plot
    output_path = "/home/cm36/Updated-LLM-Project/embedding_clusters_with_labels.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")  # Ensure legend is fully visible
    plt.show()

    print(f"Cluster visualization with labels saved as '{output_path}'")

else:
    print("No embeddings available for clustering and visualization.")
