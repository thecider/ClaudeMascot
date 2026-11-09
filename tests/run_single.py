# 하나만 실행: 평소엔 이미 켜져 있으면 바로 끝, 업데이트로 켜졌으면(--updated) 옛 프로세스가 끝날 때까지 잠깐 기다린다
import ctypes
import importlib.machinery
import importlib.util
import os
import sys
import threading
import time

loader = importlib.machinery.SourceFileLoader("claude_mascot", sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mascot", "claude_mascot.pyw"))
spec = importlib.util.spec_from_loader("claude_mascot", loader)
cm = importlib.util.module_from_spec(spec)
loader.exec_module(cm)
k32 = ctypes.windll.kernel32
k32.CreateMutexW.restype = ctypes.c_void_p
k32.CloseHandle.argtypes = [ctypes.c_void_p]
name = "Local\\ClaudeMascotSingleTest"
results = []


def check(label, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", label, info, flush=True)


held = k32.CreateMutexW(None, False, name)  # 다른(옛) 인스턴스가 잡고 있는 상태
check("이미 켜져 있으면 기다리지 않고 실패", cm.single_instance(name, 0) is None)
threading.Timer(1.0, lambda: k32.CloseHandle(ctypes.c_void_p(held))).start()
started = time.monotonic()
got = cm.single_instance(name, 5)
check("옛 것이 끝나면 기다렸다가 잡는다", got is not None and 0.8 < time.monotonic() - started < 5, round(time.monotonic() - started, 2))
print("ALL", "PASS" if all(results) else "FAIL")
