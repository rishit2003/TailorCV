# VectorService - BGE-Large Embedding Model Wrapper
# Handles text embedding using Hugging Face BGE-large model
#
# Model: BAAI/bge-large-en-v1.5
# Embedding Dimension: 1024
#
# Functions:
# - embed_text(text) -> vector (1024-dim)
#   * Takes text string
#   * Returns embedding vector as numpy array or list
#
# - embed_batch(texts) -> vectors
#   * Batch embedding for efficiency
#   * Used when embedding multiple chunks
#
# Model Loading:
# - Load on service startup
# - Keep in memory for fast inference
# - Consider GPU if available
#
# Responsibilities:
# - Model initialization and loading
# - Text preprocessing (if needed)
# - Embedding generation
# - Batch processing for efficiency

