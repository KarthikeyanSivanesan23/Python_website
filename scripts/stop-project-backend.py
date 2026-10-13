"""Send Ctrl+C only to an isolated, ownership-verified Windows Django console.

No taskkill/TerminateProcess fallback. If the console contains unrelated processes,
or cannot be attached, ask the operator to use the backend's original console.
"""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = str(Path(__file__).resolve().parent.parent).lower()


def powershell_json(command):
    result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', command], capture_output=True, text=True, timeout=10, check=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def main():
    if sys.platform != 'win32':
        raise SystemExit('This helper is for Windows. Use Ctrl+C in the backend terminal.')
    listeners = powershell_json('@(Get-NetTCPConnection -State Listen -LocalPort 8001 -ErrorAction SilentlyContinue | ForEach-Object { $_.OwningProcess } | Sort-Object -Unique) | ConvertTo-Json -Compress')
    if not listeners:
        print('No backend is listening on port 8001.')
        return
    pids = listeners if isinstance(listeners, list) else [listeners]
    if len(pids) != 1:
        raise SystemExit('Ambiguous port ownership; no process was signaled.')
    target = int(pids[0])

    def check_owner(pid):
        process = powershell_json(f'Get-CimInstance Win32_Process -Filter "ProcessId = {pid}" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress')
        command = (process or {}).get('CommandLine', '').lower().replace('/', '\\')
        return ROOT.replace('/', '\\') in command and 'manage.py' in command and 'runserver' in command

    if not check_owner(target):
        raise SystemExit(f'PID {target} is not a verified project Django server. No process was signaled.')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.AttachConsole.argtypes = [wintypes.DWORD]
    kernel.GetConsoleProcessList.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD]
    kernel.GenerateConsoleCtrlEvent.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.FreeConsole()
    if not kernel.AttachConsole(target):
        raise SystemExit(f'Cannot attach to the verified backend console (Windows error {ctypes.get_last_error()}). Use Ctrl+C in its original terminal; no forced termination attempted.')
    try:
        buffer = (wintypes.DWORD * 64)()
        count = kernel.GetConsoleProcessList(buffer, 64)
        if count == 0 or count > 64:
            raise SystemExit('Cannot verify all console owners. No signal sent.')
        console_pids = list(buffer[:count])
        if target not in console_pids or any(pid != os.getpid() and not check_owner(pid) for pid in console_pids):
            raise SystemExit('The backend shares a console with an unrelated process. No signal sent. Use its original terminal.')
        kernel.SetConsoleCtrlHandler(None, True)
        if not kernel.GenerateConsoleCtrlEvent(0, 0):  # CTRL_C_EVENT to the verified isolated console
            raise SystemExit(f'Ctrl+C delivery failed ({ctypes.get_last_error()}). No forced termination attempted.')
        time.sleep(1)
    finally:
        kernel.FreeConsole()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        alive = powershell_json(f'Get-Process -Id {target} -ErrorAction SilentlyContinue | Select-Object Id | ConvertTo-Json -Compress; exit 0')
        if not alive:
            print(f'Verified project backend PID {target} exited after Ctrl+C. PostgreSQL and unrelated processes were not signaled.')
            return
        time.sleep(.5)
    raise SystemExit('The verified backend did not exit within 10 seconds. No forced termination attempted.')


if __name__ == '__main__':
    main()
