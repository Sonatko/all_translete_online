import ctypes
from ctypes import wintypes
import subprocess
import sys
import os

# Windows Job Object API constants
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JobObjectExtendedLimitInformation = 9

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
        ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]

class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]

class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoCounters", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryLimit", ctypes.c_size_t),
        ("PeakJobMemoryLimit", ctypes.c_size_t),
    ]

def main():
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        print("[ERROR] Failed to create Job Object", file=sys.stderr)
        sys.exit(1)

    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

    success = kernel32.SetInformationJobObject(
        job,
        JobObjectExtendedLimitInformation,
        ctypes.byref(info),
        ctypes.sizeof(info)
    )
    if not success:
        print("[ERROR] Failed to set Job Object information", file=sys.stderr)
        sys.exit(1)

    # Arguments passed to server
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_dir = os.path.join(script_dir, "..", "bin", "llama_server")
    exe_path = os.path.join(server_dir, "llama-server.exe")

    args = [
        exe_path,
        "-m", os.path.join("models", "llama-3.2-3b-instruct-q4_k_m.gguf"),
        "-c", "2048",
        "-t", "8",
        "--prio", "2",
        "--cache-reuse", "64",
        "-fa", "on",
        "--load-mode", "mmap+mlock",
        "--temp", "0.1",
        "-n", "128",
        "--port", "8080",
        "--host", "127.0.0.1"
    ]

    # Pre-cleanup any rogue existing processes
    os.system("taskkill /F /IM llama-server.exe >nul 2>&1")

    # Start child process
    proc = subprocess.Popen(args, cwd=server_dir)

    # Assign to Job Object
    assign_ok = kernel32.AssignProcessToJobObject(job, int(proc._handle))
    if not assign_ok:
        print("[ERROR] Failed to assign process to Job Object", file=sys.stderr)

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    main()
