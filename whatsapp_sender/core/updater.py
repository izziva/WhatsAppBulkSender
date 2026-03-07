import httpx
import sys
import os
import platform
import zipfile
import shutil
import subprocess
from tkinter import messagebox
from packaging import version
from rich.progress import Progress
from rich import print

GITHUB_REPO = "izziva/WhatsAppBulkSender"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def get_platform_asset_name():
    """Determines the asset name based on the operating system."""
    os_type = platform.system().lower()
    if os_type == "windows":
        return "whatsapp_sender-windows.exe"
    elif os_type == "darwin":  # macOS
        return "whatsapp_sender-macos.zip"
    else:
        return None

def check_for_updates(current_version_str, gui_mode=False):
    """Checks for new updates on GitHub."""
    print("[cyan]Checking for updates...[/cyan]")
    try:
        with httpx.Client() as client:
            response = client.get(API_URL)
            response.raise_for_status()
            latest_release = response.json()
            latest_version_str = latest_release["tag_name"].lstrip('v')

            current_version = version.parse(current_version_str)
            latest_version = version.parse(latest_version_str)

            if latest_version > current_version:
                print(f"[green]New version available: {latest_version_str}[/green]")
                if gui_mode:
                    if messagebox.askyesno("Update Available", f"A new version ({latest_version_str}) is available. Do you want to update?"):
                        download_and_apply_update(latest_release)
                else:
                    if input("Do you want to update? (y/n): ").lower() == 'y':
                        download_and_apply_update(latest_release)
            else:
                print("[green]You are on the latest version.[/green]")

    except httpx.RequestError as e:
        print(f"[red]Error checking for updates: {e}[/red]")
    except Exception as e:
        print(f"[red]An unexpected error occurred during update check: {e}[/red]")


def download_and_apply_update(release_info):
    """Downloads and applies the update."""
    asset_name = get_platform_asset_name()
    if not asset_name:
        print("[red]Unsupported OS for automatic updates.[/red]")
        return

    asset = next((a for a in release_info["assets"] if a["name"] == asset_name), None)

    if not asset:
        print(f"[red]Could not find asset for your OS: {asset_name}[/red]")
        return

    download_url = asset["browser_download_url"]
    file_size = asset["size"]

    try:
        print(f"[cyan]Downloading {asset_name}...[/cyan]")
        temp_zip_path = os.path.join(os.path.dirname(sys.executable), "temp_update.zip")
        temp_exe_path = sys.executable + ".new"

        with httpx.stream("GET", download_url, follow_redirects=True) as response:
            response.raise_for_status()
            download_path = temp_zip_path if asset_name.endswith(".zip") else temp_exe_path
            with Progress() as progress:
                task = progress.add_task("[green]Downloading...", total=file_size)
                with open(download_path, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))

        print("[green]Download complete.[/green]")

        if platform.system().lower() == "darwin":
            apply_macos_update(temp_zip_path)
        else:
            os.chmod(temp_exe_path, 0o755)
            apply_windows_update(temp_exe_path)

    except httpx.RequestError as e:
        print(f"[red]Error downloading update: {e}[/red]")
    except Exception as e:
        print(f"[red]An unexpected error occurred during download: {e}[/red]")

def apply_windows_update(temp_path):
    """Applies the update on Windows using a fully detached helper script."""
    executable_path = sys.executable
    update_script_path = os.path.join(os.path.dirname(executable_path), "update.bat")

    script_content = (
        "@echo off\n"
        "echo Waiting for application to close...\n"
        "timeout /t 3 /nobreak\n"
        "echo Replacing executable...\n"
        f'move /y "{temp_path}" "{executable_path}"\n'
        "echo Update complete. Starting new version...\n"
        f'start \"\" "{executable_path}"\n'
        f'del "{update_script_path}"\n'
    )

    with open(update_script_path, "w") as f:
        f.write(script_content)

    # DETACHED_PROCESS: removes the child from the parent's console/job object
    # CREATE_NEW_PROCESS_GROUP: gives the child its own process group so it
    # is not terminated when the Python parent exits.
    creation_flags = (
        subprocess.DETACHED_PROCESS
        | subprocess.CREATE_NEW_PROCESS_GROUP
    )

    subprocess.Popen(
        ["cmd.exe", "/C", update_script_path],
        creationflags=creation_flags,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    sys.exit(0)

def apply_macos_update(zip_path):
    """Applies the update on macOS."""
    app_path = os.path.abspath(os.path.join(sys.executable, "..", "..", ".."))
    if not app_path.endswith(".app"):
        print(f"[red]Could not determine .app path. Found: {app_path}[/red]")
        return

    extract_dir = os.path.join(os.path.dirname(zip_path), "update_extracted")

    print(f"[cyan]Unzipping update to {extract_dir}...[/cyan]")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    # Find the .app bundle in the extracted files
    new_app_name = next((item for item in os.listdir(extract_dir) if item.endswith(".app")), None)
    if not new_app_name:
        print("[red]No .app bundle found in the update archive.[/red]")
        return

    new_app_path = os.path.join(extract_dir, new_app_name)

    print(f"[cyan]Replacing old application at {app_path}...[/cyan]")
    try:
        shutil.rmtree(app_path)
        shutil.move(new_app_path, app_path)
        os.remove(zip_path)
        print("[green]Update successful. Please restart the application.[/green]")
        sys.exit(0)
    except Exception as e:
        print(f"[red]Failed to apply macOS update: {e}[/red]")

if __name__ == '__main__':
    # For testing purposes
    check_for_updates("0.1.0")
