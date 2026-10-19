"""Download and prepare full PaySim and CICIDS2017 datasets."""
from __future__ import annotations
import csv, gzip, shutil, sys, urllib.request, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
PAYSIM_URL = "https://huggingface.co/datasets/kohdified/synthetic-financial-data/resolve/main/paysim.csv"
CICIDS_URL = "https://huggingface.co/datasets/bencorn/CICIDS2017/resolve/main/csvs/MachineLearningCSV.zip"
PREVIEW_ROWS = 5_000
BANKSIM_URL = "https://raw.githubusercontent.com/niravdedhiya/Fraud-Detection-BankSim/main/data/bs140513_032310.csv"
IEEE_OPENML_URL = "https://data.openml.org/datasets/0004/46858/dataset_46858.pq"
IEEE_FEATURES = (["TransactionDT", "TransactionAmt", "ProductCD", "card1", "card2",
                  "card4", "card6", "P_emaildomain", "DeviceType", "dist1"]
                 + [f"C{i}" for i in range(1, 15)]
                 + [f"D{i}" for i in range(1, 16)]
                 + [f"M{i}" for i in range(1, 10)]
                 + [f"V{i}" for i in range(1, 51)])

def download(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size:
        print(f"[SKIP] {destination.name} exists")
        return
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Fraud-Detection dataset downloader"})
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    print(f"[OK] {destination.name} ({destination.stat().st_size:,} bytes)")

def _valid_gzip(path: Path, target: str) -> bool:
    try:
        with gzip.open(path, "rt", encoding="utf-8-sig", errors="replace", newline="") as stream:
            return target in (next(csv.reader(stream), []))
    except (OSError, EOFError, gzip.BadGzipFile):
        return False

def _merge_cicids(archive: Path, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".part")
    rows = 0; expected = None
    with zipfile.ZipFile(archive) as bundle, temporary.open("wb") as raw_out:
        with gzip.GzipFile(fileobj=raw_out, mode="wb", mtime=0) as compressed:
            import io
            text_out = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
            writer = None
            for member in bundle.infolist():
                if member.is_dir() or not member.filename.lower().endswith(".csv"): continue
                with bundle.open(member) as raw:
                    reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""))
                    header = next(reader, None)
                    if not header: continue
                    header = [item.strip() for item in header]
                    if expected is None:
                        expected = header; writer = csv.writer(text_out); writer.writerow(expected)
                    elif header != expected:
                        raise RuntimeError(f"CSV schema mismatch: {member.filename}")
                    for row in reader:
                        if row: writer.writerow(row); rows += 1
                print(f"  added {member.filename}")
            text_out.flush(); text_out.detach()
    if rows == 0 or "Label" not in (expected or []):
        temporary.unlink(missing_ok=True); raise RuntimeError("Merged CICIDS gzip is empty or missing Label")
    temporary.replace(destination)
    print(f"[OK] {destination.name}: {rows:,} rows")

def _make_preview(full: Path, preview: Path, target: str) -> None:
    import pandas as pd
    # Reservoir sampling gives a deterministic, bounded preview without loading the full file.
    import random
    rng = random.Random(42); pools = {0: [], 1: []}; counts = {0: 0, 1: 0}
    with gzip.open(full, "rt", encoding="utf-8-sig", errors="replace", newline="") as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames
        for row in reader:
            value = (row.get(target) or "").strip()
            label = int(value.upper() != "BENIGN") if target == "Label" else int(float(value or 0) != 0)
            counts[label] += 1; pool = pools[label]
            if len(pool) < PREVIEW_ROWS: pool.append(row)
            else:
                index = rng.randrange(counts[label])
                if index < PREVIEW_ROWS: pool[index] = row
    total = sum(counts.values())
    quotas = {label: min(len(pool), int(PREVIEW_ROWS * counts[label] / total)) for label, pool in pools.items()}
    while sum(quotas.values()) < min(PREVIEW_ROWS, total):
        eligible = [label for label, pool in pools.items() if quotas[label] < len(pool)]
        if not eligible: break
        label = max(eligible, key=lambda key: counts[key] - quotas[key]); quotas[label] += 1
    rows = [row for label, pool in pools.items() for row in pool[:quotas[label]]]; rng.shuffle(rows)
    temporary = preview.with_suffix(preview.suffix + ".part")
    with temporary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    temporary.replace(preview)
    print(f"[OK] {preview.name}: {len(rows):,}-row preview; full data preserved in {full.name}")

def _prepare_banksim() -> None:
    raw = DATA_DIR / "banksim_source.csv"
    full = DATA_DIR / "banksim_full.csv.gz"
    if not _valid_gzip(full, "fraud"):
        download(BANKSIM_URL, raw)
        temporary = full.with_suffix(full.suffix + ".part")
        with raw.open("rb") as source, temporary.open("wb") as output:
            with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as zipped:
                shutil.copyfileobj(source, zipped)
        if not _valid_gzip(temporary, "fraud"):
            temporary.unlink(missing_ok=True)
            raise RuntimeError("BankSim source is invalid or missing fraud target")
        temporary.replace(full)
    _make_preview(full, DATA_DIR / "banksim.csv", "fraud")

def _prepare_ieee() -> None:
    full = DATA_DIR / "ieee_full.csv.gz"
    if not _valid_gzip(full, "isFraud"):
        import pandas as pd
        parquet = DATA_DIR / "ieee_openml.parquet"
        download(IEEE_OPENML_URL, parquet)
        columns = ["isFraud", *IEEE_FEATURES]
        frame = pd.read_parquet(parquet, columns=columns)
        if len(frame) != 590_540 or int(pd.to_numeric(frame["isFraud"]).sum()) != 20_663:
            raise RuntimeError("OpenML IEEE-CIS data failed row/label validation")
        temporary = full.with_suffix(full.suffix + ".part")
        frame.to_csv(temporary, index=False, compression={"method": "gzip", "mtime": 0})
        temporary.replace(full)
    _make_preview(full, DATA_DIR / "ieee.csv", "isFraud")

def main() -> int:
    try:
        paysim = DATA_DIR / "paysim_full.csv.gz"
        if not _valid_gzip(paysim, "isFraud"):
            raw = DATA_DIR / "paysim_download.csv"
            download(PAYSIM_URL, raw)
            temporary = paysim.with_suffix(paysim.suffix + ".part")
            with raw.open("rb") as source, temporary.open("wb") as target:
                with gzip.GzipFile(fileobj=target, mode="wb", mtime=0) as zipped: shutil.copyfileobj(source, zipped)
            if not _valid_gzip(temporary, "isFraud"): raise RuntimeError("PaySim CSV is invalid or missing isFraud")
            temporary.replace(paysim); raw.unlink(missing_ok=True)
        if not _valid_gzip(paysim, "isFraud"): raise RuntimeError("PaySim gzip validation failed")
        _make_preview(paysim, DATA_DIR / "paysim.csv", "isFraud")
        archive = DATA_DIR / "MachineLearningCSV.zip"
        if not archive.exists() or not zipfile.is_zipfile(archive):
            archive.unlink(missing_ok=True); download(CICIDS_URL, archive)
        if zipfile.ZipFile(archive).testzip() is not None: raise RuntimeError("CICIDS archive failed CRC validation")
        cicids = DATA_DIR / "cicids_full.csv.gz"
        if not _valid_gzip(cicids, "Label"): _merge_cicids(archive, cicids)
        if not _valid_gzip(cicids, "Label"): raise RuntimeError("CICIDS gzip validation failed")
        _make_preview(cicids, DATA_DIR / "cicids.csv", "Label")
        _prepare_banksim()
        _prepare_ieee()
    except Exception as exc:
        print(f"[ERROR] Dataset preparation failed: {exc}", file=sys.stderr); return 1
    print("All four datasets and IDE-friendly previews are ready. BankSim is the published simulator dataset; IEEE-CIS is the full labeled OpenML mirror.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
