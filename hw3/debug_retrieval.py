from hw3.vector_store import VectorManager
from hw3.rag import route_intent

vm = VectorManager()

queries = [
    ('Who is Albert Einstein?', ['person']),
    ('Where is the Eiffel Tower located?', ['place']),
    ('Tell me about Isaac Newton', ['person']),
]

print("=== RETRIEVAL RESULTS ===")
for q, cats in queries:
    print(f'\nQuery: {q}')
    print(f'Categories: {cats}')
    # VectorManager.search() is correct, it adds 'search_query: ' prefix
    results = vm.search(q, categories=cats, top_k=5)
    for r in results:
        print(f'  [{r.category}] score={r.score:.4f} title={r.title}')
        print(f'    text: {r.text[:80]}...')
