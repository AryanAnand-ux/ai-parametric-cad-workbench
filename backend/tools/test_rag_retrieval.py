import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from services.rag_service import RAGService

queries = [
    "aluminum CPU heatsink with fin array and mounting holes",
    "brushless electric motor stator casing with cooling ribs and flange",
    "spur gear blank with hub, keyway, and lightening holes",
    "single groove v-belt pulley with 38 degree v-groove",
    "weld neck pipe flange with raised face and 8 bolt circle",
    "supersonic rocket conical de laval nozzle",
    "dual-fork 2-axis robotic arm wrist clevis bracket",
    "variable displacement hydraulic pump swashplate cradle"
]

print("=" * 70)
print(f"TESTING RAG RETRIEVAL WITH 100 EXAMPLES IN CHROMADB")
print("=" * 70)

for q in queries:
    res = RAGService.retrieve(q, k=1)
    if res:
        match = res[0]
        print(f"QUERY: '{q}'")
        print(f"  -> MATCH: {match['description']}")
        print(f"  -> SIMILARITY: {match['similarity']:.4f}")
        print("-" * 70)
    else:
        print(f"QUERY: '{q}' -> NO MATCH ABOVE THRESHOLD\n" + "-" * 70)

print("RAG Retrieval Test Complete!")
