import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rag_service import RAGService

if __name__ == "__main__":
    added = RAGService.build_index(force_rebuild=False)
    print(f"Successfully added {added} new examples.")
    print(f"Total collection size: {RAGService.index_size()} examples.")
