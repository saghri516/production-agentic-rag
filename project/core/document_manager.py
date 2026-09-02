from pathlib import Path
import shutil
import config
from utils import pdfs_to_markdowns, clear_directory_contents


class DocumentManager:

    def __init__(self, rag_system):
        self.rag_system = rag_system
        self.markdown_dir = Path(config.MARKDOWN_DIR)
        self.markdown_dir.mkdir(parents=True, exist_ok=True)

    def add_documents(self, document_paths, progress_callback=None):
        if not document_paths:
            print("[DocumentManager] No document paths received — nothing to add.")
            return 0, 0

        document_paths = [document_paths] if isinstance(document_paths, str) else document_paths
        document_paths = [p for p in document_paths if p and Path(p).suffix.lower() in [".pdf", ".md"]]

        if not document_paths:
            print("[DocumentManager] No .pdf or .md files found in the provided paths.")
            return 0, 0

        # Dedup against what is ACTUALLY indexed (parent store), not just whether a
        # leftover .md file happens to exist on disk. A stale .md file from a
        # previous session (e.g. left behind if Clear All didn't fully run, or if
        # the file was manually deleted from docs/ but not from markdown_docs/)
        # would otherwise cause a real upload to be silently skipped forever.
        existing_sources = set(self.rag_system.parent_store.list_sources())
        print(f"[DocumentManager] Currently indexed sources: {sorted(existing_sources) or '(none)'}")

        added = 0
        skipped = 0

        for i, doc_path in enumerate(document_paths):
            source_path = Path(doc_path)
            source_name = source_path.name
            doc_name = source_path.stem
            md_path = self.markdown_dir / f"{doc_name}.md"

            print(f"[DocumentManager] --- Processing {source_name} ({i + 1}/{len(document_paths)}) ---")

            if progress_callback:
                progress_callback((i + 1) / len(document_paths), f"Processing {source_name}")

            expected_source_name = source_name if source_path.suffix.lower() == ".pdf" else source_name
            if expected_source_name in existing_sources or source_path.stem + ".pdf" in existing_sources:
                print(f"[DocumentManager] SKIPPED — '{source_name}' is already indexed. "
                      f"Use Clear All first if you want to re-index it.")
                skipped += 1
                continue

            parent_ids = []
            try:
                if source_path.suffix.lower() == ".md":
                    print(f"[DocumentManager] Copying markdown file to {md_path}")
                    shutil.copy(source_path, md_path)
                else:
                    print(f"[DocumentManager] Converting PDF to markdown: {source_path} -> {md_path}")
                    # overwrite=True: we already confirmed above (via existing_sources)
                    # that this document is NOT currently indexed, so any stale .md
                    # file left over on disk from a previous session must be replaced,
                    # not silently reused.
                    pdfs_to_markdowns(str(source_path), overwrite=True)

                if not md_path.exists():
                    raise FileNotFoundError(
                        f"Expected markdown file was not created at {md_path} after conversion."
                    )
                print(f"[DocumentManager] Markdown ready: {md_path} "
                      f"({md_path.stat().st_size} bytes)")

                print(f"[DocumentManager] Chunking {md_path}...")
                parent_chunks, child_chunks = self.rag_system.chunker.create_chunks_single(
                    md_path,
                    source_name=source_path.name,
                )
                print(f"[DocumentManager] Chunking produced "
                      f"{len(parent_chunks)} parent chunks, {len(child_chunks)} child chunks")

                if not child_chunks:
                    raise ValueError("No child chunks were created.")

                parent_ids = [parent_id for parent_id, _ in parent_chunks]

                print(f"[DocumentManager] Saving {len(parent_chunks)} parent chunks to parent store...")
                self.rag_system.parent_store.save_many(parent_chunks)

                print(f"[DocumentManager] Indexing {len(child_chunks)} child chunks into Qdrant "
                      f"collection '{self.rag_system.collection_name}'...")
                collection = self.rag_system.vector_db.get_collection(self.rag_system.collection_name)
                collection.add_documents(child_chunks)

                print(f"[DocumentManager] SUCCESS — '{source_name}' added "
                      f"({len(parent_chunks)} parents, {len(child_chunks)} children).")
                added += 1

            except Exception as e:
                print(f"[DocumentManager] ERROR processing {doc_path}: {e!r}")
                if parent_ids:
                    print(f"[DocumentManager] Rolling back {len(parent_ids)} parent chunk(s) "
                          f"already written for this document.")
                    self.rag_system.parent_store.delete_many(parent_ids)
                if md_path.exists():
                    print(f"[DocumentManager] Removing partially created markdown file {md_path}")
                    md_path.unlink()
                skipped += 1

        print(f"[DocumentManager] === Done: {added} added, {skipped} skipped ===")
        return added, skipped

    def get_markdown_files(self):
        sources = self.rag_system.parent_store.list_sources()
        if sources:
            return sources
        return sorted(p.name for p in self.markdown_dir.glob("*.md"))

    def clear_all(self):
        print("[DocumentManager] Clear All requested.")
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.rag_system.vector_db.delete_collection(self.rag_system.collection_name)

        clear_directory_contents(self.markdown_dir)
        remaining = list(self.markdown_dir.glob("*"))
        if remaining:
            print(f"[DocumentManager] WARNING — markdown_docs/ still has "
                  f"{len(remaining)} item(s) after clear: {[p.name for p in remaining]}")
        else:
            print("[DocumentManager] markdown_docs/ is now empty.")

        self.rag_system.parent_store.clear_store()

        self.rag_system.vector_db.create_collection(self.rag_system.collection_name)
        print("[DocumentManager] Clear All complete.")