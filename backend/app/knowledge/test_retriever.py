
from app.db.session import SessionLocal
from app.knowledge.retriever import retrieve_chunks


def main():
    query = input("Enter a product or growth question: ").strip()

    if not query:
        print("Please enter a question.")
        return

    with SessionLocal() as db:
        results = retrieve_chunks(db, query, top_k=5)

    if not results:
        print("\nNo matching transcript passages found.")
        return

    for number, result in enumerate(results, start=1):
        print(f"\n{'=' * 70}")
        print(f"Result {number} | Relevance score: {result.score:g}")
        print(f"Episode: {result.episode_title}")
        print(f"Guest: {result.guest or 'Not specified'}")
        print(f"Date: {result.episode_date or 'Not specified'}")
        print(f"Source file: {result.source_file}")
        print(f"Chunk index: {result.chunk_index}")
        print(f"\nPassage:\n{result.content[:1200]}")


if __name__ == "__main__":
    main()
