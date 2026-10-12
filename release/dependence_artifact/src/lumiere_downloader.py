"""
Downloads LUMIERE (Figshare-hosted) tabular + imaging data.

Tabular data (readme, RANO ratings, demographics, completeness — ~250KB total)
is small and downloaded directly. Imaging is a single 32.5GB zip
(Imaging-v202211.zip); this module can either download it in full (fine now
that /blue has 1.6TB free — verify live before relying on that) or extract a
subset of members via HTTP range requests without downloading the whole
archive (kept as the lower-footprint option for constrained-storage reruns).

Download targets and article/file IDs live in config/lumiere.py, re-resolved
here from the Figshare API at runtime (IDs are a cached fallback, not assumed
permanent).
"""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import requests

import config.lumiere as lcfg

FIGSHARE_API = "https://api.figshare.com/v2/articles"


def _data_dir() -> Path:
    return Path(lcfg.LUMIERE_DATA_DIR)


def resolve_article(name: str) -> dict:
    """Re-resolve an article's current file id/download_url from the Figshare
    API, falling back to the cached constants in config/lumiere.py if the API
    call fails (e.g. no outbound internet on this node)."""
    cached = lcfg.FIGSHARE_ARTICLES[name]
    try:
        r = requests.get(f"{FIGSHARE_API}/{cached['article_id']}", timeout=30)
        r.raise_for_status()
        files = r.json().get("files", [])
        if files:
            f = files[0]
            return {
                "article_id": cached["article_id"],
                "file_id": f["id"],
                "filename": f["name"],
                "download_url": f.get(
                    "download_url", f"https://ndownloader.figshare.com/files/{f['id']}"
                ),
                "size": f.get("size"),
            }
    except requests.RequestException as e:
        print(f"  [warn] Figshare API lookup failed for '{name}': {e}")
    return {
        **cached,
        "download_url": f"https://ndownloader.figshare.com/files/{cached['file_id']}",
    }


def verify_license_and_access() -> None:
    """Fetch collection metadata and print license/access terms — an explicit,
    logged access-verification step rather than an assumption."""
    r = requests.get(
        f"https://api.figshare.com/v2/collections/5904905/articles", timeout=30
    )
    r.raise_for_status()
    articles = r.json()
    print(f"LUMIERE collection: {len(articles)} articles found via Figshare API.")
    for a in articles:
        print(f"  [{a['id']}] {a['title']}")
    readme = resolve_article("readme")
    print(f"\nReadme: {readme['filename']} ({readme.get('size', '?')} bytes) — {readme['download_url']}")
    print(
        "License: LUMIERE collection is restricted to non-commercial use "
        "(per Figshare listing); confirm on the live collection page before "
        "any data leaves the login node for external sharing."
    )


def _download(url: str, dest: Path, chunk_size: int = 1 << 20) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)
    return dest


def download_tabular(force: bool = False) -> dict[str, Path]:
    """Download the 4 small tabular/readme files. Returns name -> local path."""
    out_dir = _data_dir() / "tabular"
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for name in ("readme", "rano_ratings", "demographics", "completeness"):
        info = resolve_article(name)
        dest = out_dir / info["filename"]
        if dest.exists() and not force:
            print(f"  cached: {dest}")
        else:
            print(f"Downloading {info['filename']} ({info.get('size', '?')} bytes)…")
            _download(info["download_url"], dest)
            print(f"  -> {dest}")
        result[name] = dest
    return result


def _check_storage_or_abort(min_free_gb: float = 40.0) -> None:
    usage = shutil.disk_usage(_data_dir().parent if _data_dir().exists() else Path("."))
    free_gb = usage.free / (1 << 30)
    print(f"  /blue free space: {free_gb:.1f} GB")
    if free_gb < min_free_gb:
        raise RuntimeError(
            f"Only {free_gb:.1f}GB free on /blue — aborting download (need >= "
            f"{min_free_gb}GB safety margin). Check `df -h` / group storage before retrying."
        )


def list_zip_entries(force: bool = False) -> list[str]:
    """List members of the remote imaging zip via HTTP range requests,
    without downloading the archive body — reads only the central directory.
    Cached to tabular/zip_index.json since it doesn't change between runs."""
    cache = _data_dir() / "tabular" / "zip_index.json"
    if cache.exists() and not force:
        return json.loads(cache.read_text())

    import fsspec

    info = resolve_article("imaging")
    print(f"Opening remote zip via range requests: {info['download_url']}")
    with fsspec.open(info["download_url"], mode="rb") as f:
        with zipfile.ZipFile(f) as zf:
            names = zf.namelist()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(names, indent=2))
    print(f"  {len(names)} entries -> {cache}")
    return names


def extract_members(member_names: list[str], dest_dir: Path, force: bool = False) -> list[Path]:
    """Extract specific members from the remote zip via ranged reads (no full
    download). Use after list_zip_entries() has been used to identify the
    exact members needed for the selected patients."""
    import fsspec

    info = resolve_article("imaging")
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_paths = []
    with fsspec.open(info["download_url"], mode="rb") as f:
        with zipfile.ZipFile(f) as zf:
            for name in member_names:
                out_path = dest_dir / Path(name).name
                if out_path.exists() and not force:
                    out_paths.append(out_path)
                    continue
                print(f"  extracting {name} -> {out_path}")
                with zf.open(name) as src, open(out_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                out_paths.append(out_path)
    return out_paths


def download_imaging_full(force: bool = False) -> Path:
    """Full download + extract of the 32.5GB imaging archive. Simpler and more
    robust than range-based extraction, viable now that /blue has ample free
    space (verified 85% used / 1.6TB free as of 2026-08-26 — re-check live
    before relying on this)."""
    _check_storage_or_abort(min_free_gb=40.0)
    info = resolve_article("imaging")
    raw_dir = _data_dir() / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    zip_path = raw_dir / info["filename"]
    extract_dir = _data_dir() / "imaging"

    if not zip_path.exists() or force:
        print(f"Downloading {info['filename']} ({info.get('size', '?')} bytes) — this is ~32.5GB, will take a while…")
        _download(info["download_url"], zip_path)
    else:
        print(f"  cached: {zip_path}")

    if not extract_dir.exists() or force:
        print(f"Extracting {zip_path.name} -> {extract_dir}…")
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
    else:
        print(f"  already extracted: {extract_dir}")
    return extract_dir


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="LUMIERE data access/download")
    p.add_argument("--verify-access", action="store_true")
    p.add_argument("--tabular", action="store_true")
    p.add_argument("--list-zip", action="store_true")
    p.add_argument("--download-imaging-full", action="store_true")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    if args.verify_access:
        verify_license_and_access()
    if args.tabular:
        download_tabular(force=args.force)
    if args.list_zip:
        names = list_zip_entries(force=args.force)
        print(f"First 20 entries:\n" + "\n".join(names[:20]))
    if args.download_imaging_full:
        download_imaging_full(force=args.force)
