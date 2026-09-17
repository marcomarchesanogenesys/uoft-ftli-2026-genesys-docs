#!/usr/bin/env python3
"""Download the project datasets -- TEXT AND METADATA ONLY, no audio.

Works on Windows, macOS and Linux with nothing but a Python 3.8+ install.
No pip installs, no git, no shell tools -- Python standard library only.

    python3 scripts/download_data.py              # the three core datasets
    python3 scripts/download_data.py --all        # core + the optional Twitter set
    python3 scripts/download_data.py --only abcd  # just one
    python3 scripts/download_data.py --list       # show what would be fetched
    python3 scripts/download_data.py --init-env   # create .env for Kaggle creds

Skipping audio is what makes this practical: the four datasets are ~55 GB with
audio and about 600 MB without it.

Already-downloaded files are skipped, so re-running resumes a partial download.

The three core datasets are public HTTP and need no account. The Twitter set
(twcs) is OPTIONAL: it lives on Kaggle and needs a free API token, which goes in
a .env file in the repo root (run --init-env to create it). It is the only one of
the four with real production traffic, real dates and per-agent identity, so it is
worth the two minutes -- the script explains how to get the token and never
blocks on it.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import io
import json
import os
import shutil
import ssl
import sys
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "uoft-ftli-dataset-downloader"}
WORKERS = 8

# Deliberately ASCII-only output: the default Windows console encoding still
# mangles non-ASCII, and a UnicodeEncodeError while printing a progress line is a
# miserable way to lose a download.
OK, BAD, ARROW = "[ok]", "[!!]", "->"


# ------------------------------------------------------------------ utilities


# Set once at startup by ensure_ca_bundle(). None means "use Python's default",
# which is correct on every platform that ships a working CA bundle.
SSL_CONTEXT: ssl.SSLContext | None = None

# Where the OS keeps its CA bundle. python.org macOS builds do not consult the
# system keychain and ship no bundle of their own until you run their
# Install Certificates.command -- the single most common reason a fresh machine
# cannot download anything. Rather than make students fix their Python install,
# find a bundle that is already on disk.
CA_BUNDLES = (
    "/etc/ssl/cert.pem",                               # macOS base system
    "/opt/homebrew/etc/ca-certificates/cert.pem",       # Homebrew (Apple silicon)
    "/usr/local/etc/ca-certificates/cert.pem",          # Homebrew (Intel)
    "/etc/ssl/certs/ca-certificates.crt",               # Debian, Ubuntu
    "/etc/pki/tls/certs/ca-bundle.crt",                 # Fedora, RHEL
    "/etc/ssl/ca-bundle.pem",                           # openSUSE
)


def default_certs_work() -> bool:
    """True if Python already has a CA bundle it can verify against."""
    p = ssl.get_default_verify_paths()
    if p.cafile and Path(p.cafile).exists():
        return True
    if p.capath:
        d = Path(p.capath)
        if d.is_dir() and any(d.iterdir()):
            return True
    return False


def ensure_ca_bundle() -> None:
    """Point SSL_CONTEXT at a usable CA bundle if Python has none of its own.

    Called once, before any downloads, so the worker threads all share one
    context and the explanation is printed at most once.
    """
    global SSL_CONTEXT
    if default_certs_work():
        return

    try:  # certifi is not a dependency, but it is often already installed.
        import certifi

        bundle = certifi.where()
    except ImportError:
        bundle = next((c for c in CA_BUNDLES if Path(c).exists()), None)

    if bundle:
        SSL_CONTEXT = ssl.create_default_context(cafile=bundle)
        print(f"     note: using the system CA bundle at {bundle}")
        print("     (this Python install ships none of its own)")
        return

    raise SystemExit(cert_help())


def cert_help() -> str:
    """Last-resort message when no CA bundle exists anywhere on the machine."""
    msg = f"\n{BAD} No CA certificates found, so HTTPS cannot be verified.\n\n"
    if sys.platform == "darwin":
        v = f"{sys.version_info.major}.{sys.version_info.minor}"
        msg += "     Run this once, then re-run the download:\n"
        msg += f'       "/Applications/Python {v}/Install Certificates.command"\n'
        msg += "     (Adjust the version if that path does not exist.)\n"
    elif sys.platform.startswith("linux"):
        msg += "     Install your distro's CA bundle:\n"
        msg += "       sudo apt install ca-certificates\n"
    else:
        msg += "     Reinstall Python from python.org, which bundles certificates.\n"
    return msg


def http_get(url: str, headers: dict | None = None, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as r:
            return r.read()
    except urllib.error.HTTPError as e:  # subclass of URLError -- must come first
        raise RuntimeError(f"HTTP {e.code} for {url}") from None
    except urllib.error.URLError as e:
        # urlopen wraps the cert failure, so `except ssl.SSLCertVerificationError`
        # here would never fire -- the real error arrives as URLError.reason.
        if isinstance(e.reason, ssl.SSLCertVerificationError):
            # ensure_ca_bundle() runs first, so reaching here means the bundle
            # it found is itself too old or incomplete for this host.
            raise SystemExit(cert_help())
        raise RuntimeError(f"{e.reason} for {url}") from None


def download_many(jobs: list[tuple[str, Path]], label: str) -> int:
    """Fetch (url, dest) pairs in parallel, skipping files that already exist."""
    todo = [(u, d) for u, d in jobs if not (d.exists() and d.stat().st_size > 0)]
    skipped = len(jobs) - len(todo)
    if skipped:
        print(f"     {skipped} already present, skipping")
    if not todo:
        return 0

    done = failed = 0

    def one(job):
        url, dest = job
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(http_get(url))

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(one, j): j for j in todo}
        for f in as_completed(futures):
            url, dest = futures[f]
            try:
                f.result()
                done += 1
                if done % 250 == 0 or done == len(todo):
                    print(f"     {label}: {done}/{len(todo)}")
            except Exception as e:  # noqa: BLE001 - report and keep going
                failed += 1
                print(f"     {BAD} {dest.name}: {e}")
    if failed:
        print(f"     {BAD} {failed} file(s) failed -- re-run to retry just those")
    return failed


def github_text_files(repo: str, branch: str, prefixes: tuple[str, ...]) -> list[str]:
    """List non-audio files under the given path prefixes, via one API call."""
    tree = json.loads(
        http_get(f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1")
    )
    if tree.get("truncated"):
        print(f"     {BAD} GitHub tree listing was truncated; some files may be missed")
    return [
        b["path"]
        for b in tree["tree"]
        if b["type"] == "blob"
        and b["path"].startswith(prefixes)
        and not b["path"].lower().endswith((".wav", ".mp3", ".flac", ".ogg", ".m4a"))
    ]


# ------------------------------------------------------------------ datasets


def get_harper(dry: bool) -> int:
    """HarperValleyBank -- transcripts + metadata only (skips 2.7 GB of audio)."""
    repo, branch = "cricketclub/gridspace-stanford-harper-valley", "master"
    out = ROOT / "01-harper-valley-bank"
    print("\n[1/4] HarperValleyBank  (CC BY 4.0)")
    paths = github_text_files(repo, branch, ("data/transcript/", "data/metadata/"))
    paths += ["README.md", "LICENSE"]
    print(f"     {len(paths)} text files (~25 MB); audio skipped")
    if dry:
        return 0
    base = f"https://raw.githubusercontent.com/{repo}/{branch}/"
    return download_many([(base + p, out / p) for p in paths], "harper")


def get_abcd(dry: bool) -> int:
    """ABCD -- the corpus plus its companion label files."""
    repo, branch = "asappresearch/abcd", "master"
    out = ROOT / "02-abcd"
    files = [
        "data/abcd_v1.1.json.gz",
        "data/abcd_sample.json",
        "data/guidelines.json",
        "data/kb.json",
        "data/ontology.json",
        "data/utterances.json",
        "README.md",
        "LICENSE",
    ]
    print("\n[2/4] ABCD  (MIT)")
    print(f"     {len(files)} files (~43 MB, expands to ~160 MB)")
    if dry:
        return 0
    base = f"https://raw.githubusercontent.com/{repo}/{branch}/"
    failed = download_many([(base + f, out / f) for f in files], "abcd")

    gz, plain = out / "data/abcd_v1.1.json.gz", out / "data/abcd_v1.1.json"
    if gz.exists() and not plain.exists():
        print("     decompressing abcd_v1.1.json.gz ...")
        with gzip.open(gz, "rb") as fh, plain.open("wb") as o:
            shutil.copyfileobj(fh, o)
        print(f"     {OK} abcd_v1.1.json ({plain.stat().st_size / 1e6:.0f} MB)")
    return failed


def get_apptek(dry: bool) -> int:
    """AppTek -- the diarization + test metadata (skips 52 GB of audio)."""
    ds = "apptek-com/apptek_callcenter_dialogues"
    out = ROOT / "04-apptek"
    print("\n[3/4] AppTek Call-Centre Dialogues  (CC BY-SA 4.0)")
    info = json.loads(http_get(f"https://huggingface.co/api/datasets/{ds}"))
    files = [
        s["rfilename"]
        for s in info["siblings"]
        if not s["rfilename"].lower().endswith((".wav", ".mp3", ".flac"))
    ]
    print(f"     {len(files)} text files (~23 MB); 52 GB of audio skipped")
    if dry:
        return 0
    base = f"https://huggingface.co/datasets/{ds}/resolve/main/"
    return download_many([(base + f, out / f) for f in files], "apptek")


def load_env_file() -> None:
    """Load KEY=VALUE pairs from the repo-root .env into the environment.

    Hand-rolled on purpose: python-dotenv is a pip install away and this script
    has none. Real environment variables always win over the file, so
    `KAGGLE_KEY=... python3 scripts/download_data.py --all` still overrides it.
    """
    path = ROOT / ".env"
    if not path.exists():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"{BAD} could not read .env: {e}")
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key.startswith("export "):  # tolerate `export FOO=bar`
            key = key[len("export "):].strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        # Unfilled template lines (FOO=) must not mask ~/.kaggle/kaggle.json.
        if key and val and key not in os.environ:
            os.environ[key] = val


def init_env() -> int:
    """Copy .env.example to .env so only two values need filling in."""
    example, dest = ROOT / ".env.example", ROOT / ".env"
    if not example.exists():
        print(f"{BAD} .env.example is missing -- re-clone the repo to restore it.")
        return 1
    if dest.exists():
        print(f"{OK} .env already exists -- leaving it alone (nothing overwritten).")
    else:
        shutil.copyfile(example, dest)
        print(f"{OK} created .env from .env.example")
    print(ENV_HOWTO)
    return 0


def kaggle_credentials() -> tuple[str, str] | None:
    """Look for Kaggle credentials in all three supported places."""
    u, k = os.environ.get("KAGGLE_USERNAME"), os.environ.get("KAGGLE_KEY")
    if u and k:
        return u, k
    for p in (
        Path(os.environ.get("KAGGLE_CONFIG_DIR", "")) / "kaggle.json"
        if os.environ.get("KAGGLE_CONFIG_DIR")
        else None,
        Path.home() / ".kaggle" / "kaggle.json",
    ):
        if p and p.exists():
            try:
                d = json.loads(p.read_text())
                if d.get("username") and d.get("key"):
                    return d["username"], d["key"]
            except (ValueError, OSError):
                pass
    return None


TWCS_WHY = """
     WHY IT IS WORTH GETTING
     Of the four datasets this is the only one that is real production traffic
     rather than recorded role-play, and the only one with:
       * real dates -- three months of them, so change over time is measurable
       * per-agent identity -- 2,232 (brand, agent) pairs from reply sign-offs,
         788 of which have 100+ messages spanning 42+ days
       * 2.8M messages across 108 brands
     The other three datasets have no dates at all, so anything involving
     "improving over time" can only be done with real data here.

     Trade-offs to know: messages are short (~114 characters), public and async,
     and the licence is CC BY-NC-SA 4.0 (non-commercial, share-alike).
"""

TWCS_HOWTO = """
     HOW TO GET A FREE API TOKEN (about two minutes)
       1. python3 scripts/download_data.py --init-env
          Creates .env in the repo root. It is gitignored.
       2. Sign in or sign up at https://www.kaggle.com
       3. Go to https://www.kaggle.com/settings
       4. Under "API", click "Create New Token" -- a kaggle.json file downloads.
          Open it in any text editor; it holds your username and key.
       5. Put both into .env:
            KAGGLE_USERNAME=your-username
            KAGGLE_KEY=your-key
       6. Re-run:  python3 scripts/download_data.py --all

     Already have ~/.kaggle/kaggle.json from another project? That works too --
     it is still checked, and real environment variables win over both.

     Prefer not to make an account? Download it by hand instead -- open
       https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
     click Download, unzip, and put twcs.csv at
       03-twitter-twcs/twcs.csv
"""

ENV_HOWTO = """
     NEXT -- put your Kaggle credentials in .env (about two minutes)
       1. Sign in or sign up at https://www.kaggle.com
       2. Go to https://www.kaggle.com/settings
       3. Under "API", click "Create New Token" -- a kaggle.json file downloads.
          Open it in any text editor; it holds your username and key.
       4. Edit .env and fill in the two blanks:
            KAGGLE_USERNAME=your-username
            KAGGLE_KEY=your-key
       5. Run:  python3 scripts/download_data.py --all

     .env is gitignored -- your key cannot be committed by accident.
     This is only for the optional Twitter dataset. The three core datasets
     need no account, so you can skip all of this and just run:
       python3 scripts/download_data.py
"""


def get_twcs(dry: bool) -> int:
    """Customer Support on Twitter -- needs Kaggle credentials."""
    out = ROOT / "03-twitter-twcs"
    dest = out / "twcs.csv"
    print("\n[4/4] Customer Support on Twitter  (CC BY-NC-SA 4.0)")
    if dest.exists() and dest.stat().st_size > 0:
        print(f"     {OK} already present ({dest.stat().st_size / 1e6:.0f} MB)")
        return 0
    print("     1 file (~490 MB)")
    if dry:
        return 0

    creds = kaggle_credentials()
    if not creds:
        print(f"     {BAD} no Kaggle credentials found.")
        print(TWCS_HOWTO)
        return 1

    user, key = creds
    auth = base64.b64encode(f"{user}:{key}".encode()).decode()
    url = (
        "https://www.kaggle.com/api/v1/datasets/download/"
        "thoughtvector/customer-support-on-twitter"
    )
    print("     downloading from Kaggle (this one is large, please wait) ...")
    try:
        blob = http_get(url, headers={"Authorization": f"Basic {auth}"}, timeout=1800)
    except RuntimeError as e:
        print(f"     {BAD} {e}")
        print(TWCS_HOWTO)
        return 1

    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        name = next((n for n in z.namelist() if n.lower().endswith("twcs.csv")), None)
        if not name:
            print(f"     {BAD} twcs.csv not found inside the Kaggle archive")
            return 1
        with z.open(name) as src, dest.open("wb") as o:
            shutil.copyfileobj(src, o)
    print(f"     {OK} twcs.csv ({dest.stat().st_size / 1e6:.0f} MB)")
    return 0


DATASETS = {
    "harper": get_harper,
    "abcd": get_abcd,
    "apptek": get_apptek,
    "twcs": get_twcs,
}

# The core three need no account. twcs is optional -- see TWCS_WHY.
CORE = ["harper", "abcd", "apptek"]
OPTIONAL = ["twcs"]


# ------------------------------------------------------------------ main


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Download project datasets (text and metadata only, no audio)."
    )
    ap.add_argument(
        "--only",
        help="comma-separated subset: " + ", ".join(DATASETS),
        default=None,
    )
    ap.add_argument(
        "--all",
        action="store_true",
        help="also fetch the optional Twitter set (needs a free Kaggle token)",
    )
    ap.add_argument("--list", action="store_true", help="show what would be downloaded")
    ap.add_argument(
        "--init-env",
        action="store_true",
        help="create .env from .env.example for your Kaggle credentials, then exit",
    )
    args = ap.parse_args()

    if sys.version_info < (3, 8):
        raise SystemExit(f"{BAD} Python 3.8 or newer required (found {sys.version.split()[0]})")

    if args.init_env:
        return init_env()

    load_env_file()

    if args.only:
        chosen = [c.strip().lower() for c in args.only.split(",") if c.strip()]
    else:
        chosen = CORE + (OPTIONAL if args.all else [])
    unknown = [c for c in chosen if c not in DATASETS]
    if unknown:
        raise SystemExit(f"{BAD} unknown dataset(s): {', '.join(unknown)}")

    print("=" * 68)
    print("FTLI x Genesys -- dataset download (text and metadata only)")
    print("=" * 68)
    if not args.list:
        print(f"     core: {', '.join(CORE)}"
              + ("  + optional: twcs" if "twcs" in chosen else "  (twcs not requested)"))
    if args.list:
        print("\nDRY RUN -- nothing will be written\n")

    ensure_ca_bundle()

    failures = 0
    for name in chosen:
        try:
            failures += DATASETS[name](args.list)
        except Exception as e:  # noqa: BLE001 - one dataset failing shouldn't stop the rest
            print(f"     {BAD} {name} failed: {e}")
            failures += 1

    print("\n" + "=" * 68)
    if args.list:
        print("Dry run complete.")
    elif failures:
        print(f"{BAD} Finished with {failures} problem(s). Re-run to retry -- "
              "completed files are skipped.")
    else:
        print(f"{OK} All requested datasets downloaded.")
        print("\nNext: python3 curated/build/build_curated.py")

    # Always surface the optional dataset if it is not actually on disk.
    if not args.list and not (ROOT / "03-twitter-twcs" / "twcs.csv").exists():
        print("\n" + "-" * 68)
        print("OPTIONAL DATASET NOT INSTALLED: Customer Support on Twitter (twcs)")
        print("-" * 68)
        print(TWCS_WHY)
        print(TWCS_HOWTO)
    print("=" * 68)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
