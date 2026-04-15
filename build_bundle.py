import base64
import json
from pathlib import Path

ROOT = Path(__file__).parent
GAME_HTML = ROOT / "game.html"
POSTS_DIR = ROOT / "posts"
OUTPUT = ROOT / "SwedAI_Adventure_SINGLE_FILE.html"

# folders (relative to ROOT) that should NOT be bundled
SKIP_DIRS = {"backups"}


def to_data_uri(path: Path):
    ext = path.suffix.lower()

    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }

    if ext not in mime_map:
        return None

    mime = mime_map[ext]
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


def should_skip(path: Path) -> bool:
    """Return True if path is inside any skipped directory."""
    try:
        rel_parts = path.relative_to(ROOT).parts
    except ValueError:
        return False
    return any(part in SKIP_DIRS for part in rel_parts)


def collect_all_images():
    allowed_ext = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    asset_map = {}

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        # ✅ skip backups folder entirely
        if "backups" in path.parts:
            continue

        # skip the output file itself
        if path.name.endswith("_SINGLE_FILE.html"):
            continue

        ext = path.suffix.lower()
        if ext not in allowed_ext:
            continue

        rel = path.relative_to(ROOT).as_posix()
        uri = to_data_uri(path)
        if uri:
            asset_map[rel] = uri
            asset_map[rel.lower()] = uri

    return asset_map


def load_threads():
    index = json.loads((POSTS_DIR / "index.json").read_text(encoding="utf-8"))

    threads = []
    for entry in index["threads"]:
        file_path = POSTS_DIR / entry["file"]
        data = json.loads(file_path.read_text(encoding="utf-8"))

        if "id" not in data or not data["id"]:
            data["id"] = entry["id"]

        threads.append(data)

    return {"threads": threads}


def main():
    print("ROOT =", ROOT.resolve())
    print("GAME_HTML =", GAME_HTML.resolve())
    print("OUTPUT =", OUTPUT.resolve())

    print("Collecting images...")
    assets = collect_all_images()
    print("Collected image count:", len(assets))

    print("Has exact key elements/slide1.png:", "elements/slide1.png" in assets)

    for k in sorted(assets):
        if "slide" in k.lower():
            print("Collected slide asset:", k)

    print("Loading threads...")
    threads_data = load_threads()

    html = GAME_HTML.read_text(encoding="utf-8")

    injection = f"""
<script>
const ASSET_DATA = {json.dumps(assets)};
const THREADS_DATA = {json.dumps(threads_data)};
</script>
"""

    insert_pos = html.find("<script>")
    if insert_pos == -1:
        raise RuntimeError("Couldn't find <script> tag in game.html to inject ASSET_DATA/THREADS_DATA")

    final_html = html[:insert_pos] + injection + html[insert_pos:]

    OUTPUT.write_text(final_html, encoding="utf-8")

    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"Done. Output: {OUTPUT.name}")
    print(f"Final size: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()