"""
RAG Index Builder for Fertility Knowledge Base
Processes PDFs and creates FAISS index for fast retrieval
"""

import os
from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    StorageContext,
    load_index_from_storage,
    Settings
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
import argparse

def build_rag_index(docs_dir="./fertility_docs", index_dir="./faiss_index"):
    """
    Build RAG index from fertility documents
    
    Args:
        docs_dir: Directory containing fertility PDFs/text files
        index_dir: Directory to save FAISS index
    """
    
    print("🔨 Building RAG Index for Fertility Knowledge Base")
    print(f"📁 Documents directory: {docs_dir}")
    print(f"💾 Index will be saved to: {index_dir}")
    
    # Configure embedding model
    print("\n1️⃣ Loading embedding model...")
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )
    
    # Configure chunking
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50
    
    # Load documents
    print("\n2️⃣ Loading documents...")
    if not os.path.exists(docs_dir):
        print(f"❌ Error: Directory {docs_dir} not found!")
        print("Please add your fertility PDFs to this directory.")
        return
    
    documents = SimpleDirectoryReader(
        docs_dir,
        recursive=True,
        required_exts=[".pdf", ".txt", ".md"]
    ).load_data()
    
    print(f"✅ Loaded {len(documents)} documents")
    
    # Create index
    print("\n3️⃣ Creating vector index...")
    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True
    )
    
    # Save index
    print(f"\n4️⃣ Saving index to {index_dir}...")
    os.makedirs(index_dir, exist_ok=True)
    index.storage_context.persist(persist_dir=index_dir)
    
    print("\n✅ RAG index built successfully!")
    print(f"📊 Stats:")
    print(f"   - Documents: {len(documents)}")
    print(f"   - Index location: {index_dir}")
    
    # Test retrieval
    print("\n5️⃣ Testing retrieval...")
    retriever = index.as_retriever(similarity_top_k=3)
    test_query = "What is a normal AMH level for a 32-year-old woman?"
    results = retriever.retrieve(test_query)
    
    print(f"\nTest query: '{test_query}'")
    print(f"Retrieved {len(results)} relevant chunks:")
    for i, node in enumerate(results, 1):
        print(f"\n   Chunk {i} (score: {node.score:.4f}):")
        print(f"   {node.text[:150]}...")
    
    return index

def load_existing_index(index_dir="./faiss_index"):
    """Load previously built index"""
    print(f"📂 Loading existing index from {index_dir}...")
    
    # Configure embedding model (must match building config)
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )
    
    # Load index
    storage_context = StorageContext.from_defaults(persist_dir=index_dir)
    index = load_index_from_storage(storage_context)
    
    print("✅ Index loaded successfully!")
    return index

def main():
    parser = argparse.ArgumentParser(description="Build or load RAG index")
    parser.add_argument(
        "--docs_dir",
        type=str,
        default="./fertility_docs",
        help="Directory containing fertility documents"
    )
    parser.add_argument(
        "--index_dir",
        type=str,
        default="./faiss_index",
        help="Directory to save/load index"
    )
    parser.add_argument(
        "--load",
        action="store_true",
        help="Load existing index instead of building"
    )
    
    args = parser.parse_args()
    
    if args.load:
        index = load_existing_index(args.index_dir)
    else:
        index = build_rag_index(args.docs_dir, args.index_dir)

if __name__ == "__main__":
    main()