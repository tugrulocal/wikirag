"""CLI runner for ingesting Wikipedia pages into SQLite + Chroma.

Usage:
    python -m hw3.ingest_runner            # ingest default 20 people + 20 places
    python -m hw3.ingest_runner --rebuild  # wipe Chroma and rebuild from scratch
"""

from __future__ import annotations

import argparse
import sys
import time

from hw3.ingestor import (
    build_chunks,
    build_corpus,
    initialize_registry,
    load_chunks,
    load_pages,
)
from hw3.vector_store import VectorManager, rebuild_index


def _bar(done: int, total: int, width: int = 40) -> str:
    filled = int(width * done / max(total, 1))
    return f"[{'█' * filled}{'░' * (width - filled)}] {done}/{total}"


def run(force_rebuild: bool = False) -> None:
    print("=" * 60)
    print("  HW3 — Local Wikipedia RAG Ingest Runner")
    print("=" * 60)

    # ── 1. SQLite init ──────────────────────────────────────────
    initialize_registry()
    existing_pages = load_pages()
    existing_chunks = load_chunks()
    print(f"\n[DB] Mevcut: {len(existing_pages)} sayfa, {len(existing_chunks)} chunk")

    if existing_pages and not force_rebuild:
        print("[DB] Zaten veri var. --rebuild bayrağıyla sıfırdan yapmak için tekrar çalıştır.")
        print("     Chroma index durumu kontrol ediliyor...")
        vm = VectorManager()
        count = vm.collection.count()
        if count == 0:
            print("[Chroma] Index boş — mevcut chunk'lardan index yeniden oluşturuluyor...")
            chunks = load_chunks()
            t0 = time.perf_counter()
            n = vm.upsert_chunks(chunks)
            print(f"[Chroma] {n} chunk embed edildi ({time.perf_counter()-t0:.1f}s)")
        else:
            print(f"[Chroma] {count} vektör zaten mevcut. Hiçbir şey değiştirilmedi.")
        _print_summary()
        return

    # ── 2. Wikipedia çekme ─────────────────────────────────────
    from hw3.config import DEFAULT_PEOPLE, DEFAULT_PLACES
    from hw3.ingestor import mediawiki_extract
    from hw3.models import PageRecord

    all_targets = [(title, "person") for title in DEFAULT_PEOPLE] + \
                  [(title, "place") for title in DEFAULT_PLACES]
    total = len(all_targets)

    print(f"\n[Ingest] {total} sayfa Wikipedia'dan çekilecek...")
    corpus: list[PageRecord] = []
    failed: list[str] = []

    for idx, (title, category) in enumerate(all_targets, start=1):
        label = f"  {'👤' if category == 'person' else '📍'} {title:<35}"
        print(f"\r{_bar(idx, total)}  {label}", end="", flush=True)
        # Retry up to 3 times with exponential backoff (handles Wikipedia rate limits)
        for attempt in range(3):
            try:
                page = mediawiki_extract(title, category=category)
                corpus.append(page)
                break
            except Exception as exc:
                if attempt < 2:
                    wait = 2 ** attempt * 2  # 2s, 4s
                    time.sleep(wait)
                else:
                    failed.append(f"{title}: {exc}")
        time.sleep(0.5)  # polite delay between pages

    print()  # newline after progress bar

    if failed:
        print(f"\n[WARN] {len(failed)} sayfa çekilemedi:")
        for f in failed:
            print(f"  ✗ {f}")

    # ── 3. SQLite kayıt ────────────────────────────────────────
    from hw3.ingestor import save_pages, build_chunks as _build_chunks
    save_pages(corpus)
    print(f"\n[DB] {len(corpus)} sayfa SQLite'a yazıldı.")

    # ── 4. Chunk ───────────────────────────────────────────────
    print("[Chunk] Metinler parçalanıyor...")
    chunks = _build_chunks(corpus)
    print(f"[Chunk] {len(chunks)} chunk oluşturuldu.")

    # ── 5. Embedding + Chroma ──────────────────────────────────
    vm = VectorManager()
    if force_rebuild:
        print("[Chroma] Koleksiyon sıfırlanıyor...")
        vm.reset()

    print(f"[Embed] {len(chunks)} chunk Ollama nomic-embed-text ile embed ediliyor...")
    print("        (Bu biraz zaman alabilir, M4 Pro'da ~2-3 dakika beklenir.)\n")

    batch_size = 10
    total_chunks = len(chunks)
    embedded = 0
    t0 = time.perf_counter()

    for batch_start in range(0, total_chunks, batch_size):
        batch = chunks[batch_start:batch_start + batch_size]
        vm.upsert_chunks(batch)
        embedded += len(batch)
        elapsed = time.perf_counter() - t0
        eta = (elapsed / embedded) * (total_chunks - embedded) if embedded else 0
        print(
            f"\r  {_bar(embedded, total_chunks)}  {elapsed:.0f}s geçti, ~{eta:.0f}s kaldı",
            end="",
            flush=True,
        )

    print(f"\n\n[Embed] Tamamlandı! Toplam süre: {time.perf_counter()-t0:.1f}s")

    # ── 6. Özet ────────────────────────────────────────────────
    _print_summary()


def _print_summary() -> None:
    from hw3.ingestor import load_pages, load_chunks
    from hw3.vector_store import VectorManager

    pages = load_pages()
    chunks = load_chunks()
    vm = VectorManager()
    vec_count = vm.collection.count()

    people = [p for p in pages if p.category == "person"]
    places = [p for p in pages if p.category == "place"]

    print("\n" + "=" * 60)
    print("  Özet")
    print("=" * 60)
    print(f"  Sayfalar  : {len(pages)} ({len(people)} kişi, {len(places)} yer)")
    print(f"  Chunk'lar : {len(chunks)}")
    print(f"  Vektörler : {vec_count}")
    print("=" * 60)

    if len(pages) < 40:
        print(f"\n  ⚠️  UYARI: Ödev en az 20 kişi + 20 yer istiyor (şu an {len(pages)}/40)")
    else:
        print(f"\n  ✅ Kapsam tamam: {len(people)}/20 kişi, {len(places)}/20 yer")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HW3 Wikipedia ingest runner")
    parser.add_argument("--rebuild", action="store_true", help="Chroma'yı sıfırlayıp sıfırdan build et")
    args = parser.parse_args()
    run(force_rebuild=args.rebuild)
