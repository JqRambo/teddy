#!/usr/bin/env python3
import os, sys, re, shutil, subprocess, tarfile, urllib.request
from pathlib import Path

BASE_URL = "https://www.as.arizona.edu/~hubeny/tlusty208-package"
PACKAGES = ["tl208-s54.tar.gz", "linelist.tar.gz", "irondata.tar.gz", "optables.tar.gz"]
MARK_START, MARK_END = "# >>> tlusty config >>>", "# <<< tlusty config <<<"

def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd}\n{r.stderr}")

def download(url, dest):
    if dest.exists():
        return
    if shutil.which("wget"):
        subprocess.run(f"wget -q --show-progress -O {dest} {url}", shell=True, check=True)
    else:
        urllib.request.urlretrieve(url, dest)

def extract(tar_path, dest_dir):
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=dest_dir)

def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/tlusty").resolve()

    print("[1/6] Checking compiler", end=" ")
    if not shutil.which("gfortran"):
        print("failed")
        print("gfortran not found, run: sudo apt-get install gfortran")
        sys.exit(1)
    print("ok")

    print("[2/6] Downloading")
    root.mkdir(parents=True, exist_ok=True)
    for pkg in PACKAGES:
        download(f"{BASE_URL}/{pkg}", root / pkg)

    print("[3/6] Extracting", end=" ")
    for pkg in PACKAGES:
        extract(root / pkg, root)
    print("done")

    print("[4/6] Configuring environment", end=" ")
    envs = {
        "TL208": str(root),
        "TLUSTY": f"{root}/tl208-s54",
        "LINELIST": f"{root}/linelist",
        "IRON": f"{root}/irondata",
        "OPTABLES": f"{root}/optables",
    }
    bashrc = Path.home() / ".bashrc"
    content = bashrc.read_text() if bashrc.exists() else ""
    block = "\n".join([MARK_START] + [f"export {k}={v}" for k, v in envs.items()] + [MARK_END])
    pat = re.compile(re.escape(MARK_START) + ".*?" + re.escape(MARK_END), re.DOTALL)
    bashrc.write_text(pat.sub(block, content) if pat.search(content) else content.rstrip() + "\n\n" + block + "\n")
    for k, v in envs.items():
        os.environ[k] = v
    print("done")

    print("[5/6] Compiling...")
    run("gfortran -o list2bin.exe list2bin.f", cwd=envs["LINELIST"])
    run("./Bin", cwd=envs["LINELIST"])
    for script in ("./Linklist", "./Linkiron", "./Linkopta"):
        run(script, cwd=f"{envs['TLUSTY']}/data")
    run("gfortran -fno-automatic -mcmodel=large -O3 -o tlusty.exe tlusty208.f", cwd=f"{envs['TLUSTY']}/tlusty")
    run("gfortran -fno-automatic -mcmodel=large -o synspec.exe synspec54.f", cwd=f"{envs['TLUSTY']}/synspec")
    print("      done")

    print("[6/6] Running tests...")
    for test in ("tlusty", "synspec"):
        try:
            run("./R1", cwd=f"{envs['TLUSTY']}/tests/{test}/hhe")
            print(f"      {test} passed")
        except RuntimeError:
            print(f"      {test} failed")

    print("\nDone. Run: source ~/.bashrc")

if __name__ == "__main__":
    main()
