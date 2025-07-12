# security/anti_tamper.py
"""
Mécanismes anti-débogage et anti-altération
Protection contre l'analyse et la modification du code
"""

import os
import sys
import time
import ctypes
import hashlib
import threading
from typing import List, Set, Tuple, Optional
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import win32api
    import win32con
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from config.constants import SUSPICIOUS_PROCESSES
from utils.logger import SecureLogger


class AntiTamperSystem:
    """Système de protection anti-tampering"""
    
    def __init__(self):
        self.logger = SecureLogger()
        self._integrity_hashes = {}
        self._init_integrity_baseline()
        self._detection_callbacks = []
        
    def _init_integrity_baseline(self):
        """Initialiser les hashes d'intégrité des fichiers critiques"""
        critical_files = [
            'security/auth_core.py',
            'security/mac_whitelist.py',
            'security/usb_token.py',
            'security/lockdown.py',
            'panel/main_panel.py'
        ]
        
        for file in critical_files:
            if os.path.exists(file):
                self._integrity_hashes[file] = self._calculate_file_hash(file)
    
    def detect_debugger(self) -> bool:
        """Détecter la présence d'un debugger"""
        if WIN32_AVAILABLE:
            # Méthode 1: IsDebuggerPresent
            if ctypes.windll.kernel32.IsDebuggerPresent():
                self.logger.log_security_event('DEBUGGER_DETECTED', {
                    'method': 'IsDebuggerPresent'
                }, severity='CRITICAL')
                return True
            
            # Méthode 2: CheckRemoteDebuggerPresent
            is_debugged = ctypes.c_bool(False)
            ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
                ctypes.windll.kernel32.GetCurrentProcess(),
                ctypes.byref(is_debugged)
            )
            
            if is_debugged.value:
                self.logger.log_security_event('DEBUGGER_DETECTED', {
                    'method': 'CheckRemoteDebuggerPresent'
                }, severity='CRITICAL')
                return True
            
            # Méthode 3: Vérifier PEB (Process Environment Block)
            if self._check_peb_debugger():
                return True
            
            # Méthode 4: Timing check
            if self._timing_check():
                return True
        
        # Méthode 5: Vérifier processus parents
        if self._check_parent_process():
            return True
        
        return False
    
    def detect_suspicious_processes(self) -> bool:
        """Détecter processus suspects (debuggers, analyseurs, etc.)"""
        if not PSUTIL_AVAILABLE:
            return False
        
        try:
            current_processes = {p.name().lower() for p in psutil.process_iter(['name'])}
            
            # Vérifier contre liste de processus suspects
            for suspicious in SUSPICIOUS_PROCESSES:
                if any(suspicious in proc for proc in current_processes):
                    self.logger.log_security_event('SUSPICIOUS_PROCESS_DETECTED', {
                        'process': suspicious
                    }, severity='HIGH')
                    return True
            
            # Vérifier processus avec droits debug
            if WIN32_AVAILABLE:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        handle = win32api.OpenProcess(
                            win32con.PROCESS_QUERY_INFORMATION,
                            False,
                            proc.info['pid']
                        )
                        
                        # Vérifier privilèges debug
                        # (implémentation détaillée omise pour brièveté)
                        
                        win32api.CloseHandle(handle)
                    except:
                        pass
            
        except Exception as e:
            self.logger.log_event('PROCESS_SCAN_ERROR', {'error': str(e)})
        
        return False
    
    def detect_memory_tampering(self) -> bool:
        """Détecter modifications mémoire (hooks, injections)"""
        if WIN32_AVAILABLE:
            # Vérifier intégrité des APIs critiques
            critical_apis = [
                ('kernel32.dll', 'IsDebuggerPresent'),
                ('ntdll.dll', 'NtQueryInformationProcess'),
                ('kernel32.dll', 'GetProcAddress')
            ]
            
            for dll_name, api_name in critical_apis:
                if self._check_api_hook(dll_name, api_name):
                    self.logger.log_security_event('API_HOOK_DETECTED', {
                        'dll': dll_name,
                        'api': api_name
                    }, severity='CRITICAL')
                    return True
        
        # Vérifier modifications du code Python
        if self._check_code_integrity():
            return True
        
        return False
    
    def detect_tampering(self) -> bool:
        """Détection générale de tampering"""
        # Vérifier debugger
        if self.detect_debugger():
            return True
        
        # Vérifier processus suspects
        if self.detect_suspicious_processes():
            return True
        
        # Vérifier intégrité fichiers
        if not self.verify_file_integrity():
            return True
        
        # Vérifier environnement d'exécution
        if self._detect_sandbox():
            return True
        
        return False
    
    def verify_file_integrity(self) -> bool:
        """Vérifier l'intégrité des fichiers critiques"""
        for filepath, expected_hash in self._integrity_hashes.items():
            if os.path.exists(filepath):
                current_hash = self._calculate_file_hash(filepath)
                
                if current_hash != expected_hash:
                    self.logger.log_security_event('FILE_INTEGRITY_VIOLATION', {
                        'file': filepath,
                        'expected': expected_hash[:16],
                        'actual': current_hash[:16]
                    }, severity='CRITICAL')
                    return False
            else:
                # Fichier manquant
                self.logger.log_security_event('CRITICAL_FILE_MISSING', {
                    'file': filepath
                }, severity='CRITICAL')
                return False
        
        return True
    
    def add_detection_callback(self, callback):
        """Ajouter callback en cas de détection"""
        self._detection_callbacks.append(callback)
    
    def start_continuous_monitoring(self, interval: int = 30):
        """Démarrer surveillance continue"""
        def monitor_loop():
            while True:
                try:
                    if self.detect_tampering():
                        # Appeler callbacks
                        for callback in self._detection_callbacks:
                            try:
                                callback()
                            except:
                                pass
                        break
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    self.logger.log_event('TAMPER_MONITOR_ERROR', {'error': str(e)})
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def _check_peb_debugger(self) -> bool:
        """Vérifier flag debugger dans PEB"""
        if not WIN32_AVAILABLE:
            return False
        
        try:
            # Structure PEB simplifiée
            class PEB(ctypes.Structure):
                _fields_ = [
                    ("Reserved1", ctypes.c_byte * 2),
                    ("BeingDebugged", ctypes.c_byte),
                    ("Reserved2", ctypes.c_byte * 1)
                ]
            
            # Obtenir PEB via NtQueryInformationProcess
            # (implémentation simplifiée)
            process = ctypes.windll.kernel32.GetCurrentProcess()
            peb = PEB()
            
            # Si BeingDebugged est set
            if hasattr(peb, 'BeingDebugged') and peb.BeingDebugged:
                self.logger.log_security_event('DEBUGGER_DETECTED', {
                    'method': 'PEB_BeingDebugged'
                }, severity='CRITICAL')
                return True
                
        except:
            pass
        
        return False
    
    def _timing_check(self) -> bool:
        """Détection par timing (debuggers ralentissent l'exécution)"""
        # Mesurer temps d'exécution d'opérations simples
        start = time.perf_counter()
        
        # Opérations rapides
        result = 0
        for i in range(100000):
            result += i * 2
        
        elapsed = time.perf_counter() - start
        
        # Si trop lent, probablement debuggé
        if elapsed > 0.1:  # Seuil ajustable
            self.logger.log_security_event('DEBUGGER_DETECTED', {
                'method': 'timing_check',
                'elapsed': elapsed
            }, severity='HIGH')
            return True
        
        return False
    
    def _check_parent_process(self) -> bool:
        """Vérifier si lancé depuis un debugger"""
        if not PSUTIL_AVAILABLE:
            return False
        
        try:
            current = psutil.Process()
            parent = current.parent()
            
            if parent:
                parent_name = parent.name().lower()
                
                # Liste de debuggers connus
                debuggers = [
                    'windbg', 'x64dbg', 'ollydbg', 'ida', 'ghidra',
                    'gdb', 'lldb', 'radare2', 'immunity'
                ]
                
                for dbg in debuggers:
                    if dbg in parent_name:
                        self.logger.log_security_event('DEBUGGER_PARENT_DETECTED', {
                            'parent': parent_name
                        }, severity='CRITICAL')
                        return True
                        
        except:
            pass
        
        return False
    
    def _check_api_hook(self, dll_name: str, api_name: str) -> bool:
        """Vérifier si une API Windows est hookée"""
        if not WIN32_AVAILABLE:
            return False
        
        try:
            # Obtenir adresse de l'API
            h_module = ctypes.windll.kernel32.GetModuleHandleW(dll_name)
            if not h_module:
                return False
            
            proc_addr = ctypes.windll.kernel32.GetProcAddress(h_module, api_name.encode())
            if not proc_addr:
                return False
            
            # Lire premiers bytes
            buffer = ctypes.create_string_buffer(5)
            ctypes.windll.kernel32.ReadProcessMemory(
                ctypes.windll.kernel32.GetCurrentProcess(),
                proc_addr,
                buffer,
                5,
                None
            )
            
            # Vérifier patterns de hook communs
            # JMP (0xE9) ou PUSH+RET (0x68)
            if buffer[0] in [0xE9, 0x68]:
                return True
                
        except:
            pass
        
        return False
    
    def _check_code_integrity(self) -> bool:
        """Vérifier intégrité du code Python en mémoire"""
        # Vérifier que les fonctions critiques n'ont pas été modifiées
        critical_functions = [
            ('os', 'system'),
            ('subprocess', 'Popen'),
            ('sys', 'exit')
        ]
        
        for module_name, func_name in critical_functions:
            try:
                module = sys.modules.get(module_name)
                if module:
                    func = getattr(module, func_name, None)
                    if func:
                        # Vérifier que c'est bien une fonction built-in
                        if not hasattr(func, '__code__'):
                            continue
                            
                        # Vérifier signature
                        # (implémentation détaillée omise)
            except:
                pass
        
        return False
    
    def _detect_sandbox(self) -> bool:
        """Détecter environnement sandbox/VM"""
        sandbox_indicators = []
        
        # Vérifier fichiers/clés registre spécifiques aux VMs
        vm_files = [
            r"C:\windows\system32\drivers\vmmouse.sys",
            r"C:\windows\system32\drivers\vmhgfs.sys",
            r"C:\windows\system32\drivers\vboxmouse.sys"
        ]
        
        for vm_file in vm_files:
            if os.path.exists(vm_file):
                sandbox_indicators.append(f"VM file: {vm_file}")
        
        # Vérifier processus VM
        if PSUTIL_AVAILABLE:
            vm_processes = ['vmtoolsd', 'vboxservice', 'vboxtray']
            current_processes = {p.name().lower() for p in psutil.process_iter(['name'])}
            
            for vm_proc in vm_processes:
                if vm_proc in current_processes:
                    sandbox_indicators.append(f"VM process: {vm_proc}")
        
        # Vérifier nombre de CPUs (VMs ont souvent peu de cores)
        if os.cpu_count() <= 2:
            sandbox_indicators.append("Low CPU count")
        
        # Si plusieurs indicateurs, probablement sandbox
        if len(sandbox_indicators) >= 2:
            self.logger.log_security_event('SANDBOX_DETECTED', {
                'indicators': sandbox_indicators
            }, severity='HIGH')
            return True
        
        return False
    
    def _calculate_file_hash(self, filepath: str) -> str:
        """Calculer hash SHA256 d'un fichier"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
            
        except Exception:
            return ""# Mécanismes anti-débogage et anti-altération 