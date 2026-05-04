"""One-off script to fetch and embed missing place pages."""
import time
from hw3.ingestor import mediawiki_extract, save_pages, build_chunks, load_pages, initialize_registry
from hw3.vector_store import VectorManager

initialize_registry()
vm = VectorManager()

missing_places = [
    'Eiffel Tower', 'Great Wall of China', 'Taj Mahal', 'Grand Canyon',
    'Machu Picchu', 'Colosseum', 'Petra', 'Forbidden City', 'Niagara Falls', 'Acropolis of Athens'
]

fetched = []
for title in missing_places:
    print(f'Fetching: {title}', end=' ', flush=True)
    for attempt in range(4):
        try:
            p = mediawiki_extract(title, category='place')
            fetched.append(p)
            print(f'OK ({len(p.extract)} chars)')
            time.sleep(1.5)
            break
        except Exception as e:
            print(f'ERR attempt {attempt+1}: {str(e)[:80]}')
            time.sleep(3 * (attempt + 1))

if fetched:
    save_pages(fetched)
    chunks = build_chunks(fetched)
    vm.upsert_chunks(chunks)
    print(f'\nAdded: {len(fetched)} pages, {len(chunks)} chunks embedded.')

pages = load_pages()
places = [p for p in pages if p.category == 'place']
people = [p for p in pages if p.category == 'person']
print(f'Total: {len(people)} people, {len(places)} places, {len(pages)} pages total')
print('Places:', [p.title for p in places])
