import shutil
import subprocess
import sys
from importlib.resources import files
from pathlib import Path


def install_xdg() -> None:
    apps_dir = Path.home() / ".local/share/applications"
    mime_dir = Path.home() / ".local/share/mime/packages"
    apps_dir.mkdir(parents=True, exist_ok=True)
    mime_dir.mkdir(parents=True, exist_ok=True)

    data = files("graphysio") / "data"

    # Resolve the installed graphysio executable so the desktop file works
    # regardless of venv or install prefix.
    exec_path = shutil.which("graphysio")
    if exec_path is None:
        candidate = Path(sys.executable).parent / "graphysio"
        exec_path = str(candidate) if candidate.exists() else "graphysio"

    desktop_text = (data / "graphysio.desktop").read_text()
    desktop_text = desktop_text.replace("Exec=graphysio %f", f"Exec={exec_path} %f", 1)
    desktop_dest = apps_dir / "graphysio.desktop"
    desktop_dest.write_text(desktop_text)

    mime_text = (data / "graphysio-mimetypes.xml").read_text()
    mime_dest = mime_dir / "graphysio.xml"
    mime_dest.write_text(mime_text)

    subprocess.run(["update-mime-database", str(mime_dir.parent)], check=False)
    subprocess.run(["update-desktop-database", str(apps_dir)], check=False)

    print("Desktop integration installed.")
    print(f"  Desktop entry: {desktop_dest}")
    print(f"  MIME types:    {mime_dest}")
    print(f"  Exec:          {exec_path}")
