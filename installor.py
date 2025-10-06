#!/usr/bin/env python3
"""
Aicode Pro - One-Time Installer
Installs all dependencies and sets up the application
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class AicodeInstaller:
    def __init__(self):
        self.console_width = 70
        self.is_termux = os.path.exists('/data/data/com.termux')
        self.python_cmd = 'python3' if platform.system() != 'Windows' else 'python'
    
    def print_banner(self):
        banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║              █████╗ ██╗ ██████╗ ██████╗ ██████╗ ███████╗         ║
║             ██╔══██╗██║██╔════╝██╔═══██╗██╔══██╗██╔════╝         ║
║             ███████║██║██║     ██║   ██║██║  ██║█████╗           ║
║             ██╔══██║██║██║     ██║   ██║██║  ██║██╔══╝           ║
║             ██║  ██║██║╚██████╗╚██████╔╝██████╔╝███████╗         ║
║             ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝         ║
║                                                                   ║
║                    PRODUCTION INSTALLER v1.0                      ║
║                    Developer: RegexMan Woo                        ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def print_step(self, step_num, message):
        print(f"\n[{step_num}/6] {message}")
        print("-" * self.console_width)
    
    def run_command(self, cmd, check=True):
        """Run shell command and return success status"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=check,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
    
    def check_python_version(self):
        """Check if Python version is 3.7+"""
        self.print_step(1, "Checking Python version...")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            print(f"❌ Python 3.7+ required. Found: {version.major}.{version.minor}")
            return False
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    
    def check_pip(self):
        """Check if pip is installed"""
        self.print_step(2, "Checking pip installation...")
        success, output = self.run_command(f"{self.python_cmd} -m pip --version", check=False)
        if not success:
            print("❌ pip not found. Installing pip...")
            if self.is_termux:
                self.run_command("pkg install python-pip -y")
            else:
                print("Please install pip manually: https://pip.pypa.io/en/stable/installation/")
                return False
        print("✓ pip is installed")
        return True
    
    def install_dependencies(self):
        """Install required Python packages"""
        self.print_step(3, "Installing dependencies...")
        
        dependencies = [
            "groq",
            "rich",
            "python-dotenv"
        ]
        
        print("Installing packages:")
        for dep in dependencies:
            print(f"  - {dep}...")
        
        deps_str = " ".join(dependencies)
        
        if self.is_termux:
            # Termux-specific installation
            print("\n📱 Termux detected - using optimized installation...")
            success, output = self.run_command(
                f"{self.python_cmd} -m pip install {deps_str} --no-cache-dir",
                check=False
            )
        else:
            # Standard installation
            success, output = self.run_command(
                f"{self.python_cmd} -m pip install {deps_str}",
                check=False
            )
        
        if not success:
            print(f"❌ Installation failed:\n{output}")
            return False
        
        print("✓ All dependencies installed successfully")
        return True
    
    def create_aicode_script(self):
        """Create the main aicode_pro.py script"""
        self.print_step(4, "Creating Aicode Pro script...")
        
        script_content = '''#!/usr/bin/env python3

import os
import sys
import time
import json
import base64
import hmac
import hashlib
import re
from typing import Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import date
from groq import Groq
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from dotenv import load_dotenv, set_key
import argparse

# Integrity check
_s = b\'\\x89\\x50\\x4e\\x47\\x0d\\x0a\\x1a\\x0a\\x39\\x38\\x34\\x34\'
_h = hashlib.sha256(b\'aicode_pro_v1_integrity_2025\').hexdigest()

def _v(c):
    return hmac.compare_digest(
        hashlib.sha256(c.encode() if isinstance(c, str) else c).hexdigest(),
        _h
    )

@dataclass
class Config:
    _ef: str = ".env"
    _dm: str = "llama-3.3-70b-versatile"
    _ct: float = 30.0
    _mfs: int = 1_000_000
    _be: bool = True

class _LM:
    def __init__(self, c: Console):
        self._c = c
        self._s = _s[-4:]
        self._l = False
        self._ed: Optional[date] = None
        self._rf = 0
        self._ll()
        if not self._l:
            self._lu()
    
    def _ll(self) -> None:
        lp = Path(".aicode_license")
        if lp.exists():
            try:
                t = lp.read_text().strip()
                e = self._vt(t)
                if e and e >= date.today():
                    self._l = True
                    self._ed = e
                    self._c.print(f"[green]Licensed until {e.isoformat()}[/green]")
                    up = Path(".aicode_usage.json")
                    if up.exists():
                        up.unlink()
                else:
                    lp.unlink()
                    self._c.print("[yellow]License expired[/yellow]")
            except Exception as ex:
                self._c.print(f"[red]License error: {ex}[/red]")
    
    def _vt(self, t: str) -> Optional[date]:
        try:
            d = base64.urlsafe_b64decode(t.encode())
            if len(d) < 32:
                return None
            eb = d[:-32]
            m = d[-32:]
            em = hmac.new(self._s, eb, hashlib.sha256).digest()
            if hmac.compare_digest(m, em):
                es = eb.decode(\'utf-8\')
                return date.fromisoformat(es)
        except:
            pass
        return None
    
    def _lu(self) -> None:
        up = Path(".aicode_usage.json")
        if up.exists():
            try:
                with open(up, "r") as f:
                    d = json.load(f)
                    pu = d.get("prompts_used", 0)
                    self._rf = max(0, 5 - pu)
            except:
                self._rf = 5
        else:
            self._rf = 5
        self._c.print(f"[blue]Free prompts: {self._rf}[/blue]")
    
    def _su(self) -> None:
        up = Path(".aicode_usage.json")
        pu = 5 - self._rf
        try:
            with open(up, "w") as f:
                json.dump({"prompts_used": pu}, f)
        except Exception as ex:
            self._c.print(f"[red]Save error: {ex}[/red]")
    
    def reset(self, p: str) -> bool:
        if p != self._s.decode():
            self._c.print("[red]Invalid password[/red]")
            return False
        lp = Path(".aicode_license")
        if lp.exists():
            lp.unlink()
        up = Path(".aicode_usage.json")
        if up.exists():
            up.unlink()
        self._ll()
        self._lu()
        self._c.print("[green]Reset complete[/green]")
        return True
    
    def use_prompt(self) -> bool:
        if self._l:
            return True
        if self._rf > 0:
            self._rf -= 1
            self._su()
            self._c.print(f"[blue]Free prompts remaining: {self._rf}[/blue]")
            return True
        else:
            self._c.print("[red]Free trial exhausted. License required.[/red]")
            self._c.print("[bold cyan]Contact: https://www.facebook.com/share/178Nt8BnuP/[/bold cyan]")
            self._c.print("[bold cyan]Telegram: t.me/JadXHex[/bold cyan]")
            t = Prompt.ask("[bold]Enter license token[/bold]", password=False).strip()
            if t:
                e = self._vt(t)
                if e and e >= date.today():
                    try:
                        with open(".aicode_license", "w") as f:
                            f.write(t)
                        self._l = True
                        self._ed = e
                        self._c.print(f"[green]License activated until {e.isoformat()}[/green]")
                        up = Path(".aicode_usage.json")
                        if up.exists():
                            up.unlink()
                        return True
                    except Exception as ex:
                        self._c.print(f"[red]Save error: {ex}[/red]")
                else:
                    self._c.print("[red]Invalid token[/red]")
            return False
    
    def check_licensed(self) -> bool:
        return self._l

# [REST OF THE CODE CONTINUES - truncated for brevity in installer]
# The full aicode_pro.py content would go here
'''
        
        try:
            with open("aicode_pro.py", "w", encoding="utf-8") as f:
                # Write the placeholder - user should replace with full script
                f.write("# Aicode Pro will be created here\n")
                f.write("# Please paste the full obfuscated script content\n")
            
            print("✓ Created aicode_pro.py (placeholder)")
            print("⚠️  Please replace aicode_pro.py content with the full obfuscated script")
            return True
        except Exception as e:
            print(f"❌ Failed to create script: {e}")
            return False
    
    def create_launcher(self):
        """Create convenient launcher scripts"""
        self.print_step(5, "Creating launcher scripts...")
        
        # Bash launcher for Linux/Termux/Mac
        bash_launcher = f"""#!/bin/bash
{self.python_cmd} aicode_pro.py "$@"
"""
        
        # Batch launcher for Windows
        batch_launcher = f"""@echo off
{self.python_cmd} aicode_pro.py %*
"""
        
        try:
            # Create bash launcher
            with open("aicode", "w") as f:
                f.write(bash_launcher)
            os.chmod("aicode", 0o755)
            print("✓ Created 'aicode' launcher (Unix)")
            
            # Create batch launcher for Windows
            with open("aicode.bat", "w") as f:
                f.write(batch_launcher)
            print("✓ Created 'aicode.bat' launcher (Windows)")
            
            return True
        except Exception as e:
            print(f"❌ Failed to create launchers: {e}")
            return False
    
    def create_env_template(self):
        """Create .env template file"""
        self.print_step(6, "Creating configuration template...")
        
        env_template = """# Aicode Pro Configuration
# Get your Groq API key from: https://console.groq.com

# Add your Groq API key(s) here (comma-separated for multiple keys)
GROQ_API_KEYS=your_groq_api_key_here

# You can also use single key format (will be auto-migrated)
# GROQ_API_KEY=your_groq_api_key_here
"""
        
        try:
            if not Path(".env").exists():
                with open(".env", "w") as f:
                    f.write(env_template)
                print("✓ Created .env template")
            else:
                print("✓ .env file already exists (not overwriting)")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env: {e}")
            return False
    
    def print_success_message(self):
        """Print installation success message with instructions"""
        success_msg = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║                  ✓ INSTALLATION SUCCESSFUL!                       ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

📋 NEXT STEPS:

1. Get Groq API Key (FREE):
   Visit: https://console.groq.com
   Sign up and create your API key

2. Configure Aicode Pro:
   Edit the .env file and add your Groq API key:
   GROQ_API_KEYS=your_actual_api_key_here

3. Run Aicode Pro:
"""
        
        if platform.system() == "Windows":
            run_cmd = "   python aicode_pro.py\n   OR\n   aicode.bat"
        else:
            run_cmd = "   python3 aicode_pro.py\n   OR\n   ./aicode"
        
        license_info = """
4. License Information:
   - Free Tier: 5 prompts for testing
   - Full License: Unlimited prompts + file management
   
   Get license at:
   Facebook: https://www.facebook.com/share/178Nt8BnuP/
   Telegram: t.me/JadXHex

💡 FEATURES:
   ✓ AI-powered code generation
   ✓ Automatic file backups
   ✓ Production-grade security
   ✓ Multi-API key support
   ✓ Interactive coding assistant

⚠️  IMPORTANT: Replace the aicode_pro.py placeholder with the
    full obfuscated script content!

Happy coding! 🚀
"""
        
        print(success_msg)
        print(run_cmd)
        print(license_info)
    
    def install(self):
        """Main installation process"""
        self.print_banner()
        
        print("\n🚀 Starting Aicode Pro installation...\n")
        
        # Check Python version
        if not self.check_python_version():
            return False
        
        # Check pip
        if not self.check_pip():
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            return False
        
        # Create main script
        if not self.create_aicode_script():
            return False
        
        # Create launchers
        if not self.create_launcher():
            return False
        
        # Create .env template
        if not self.create_env_template():
            return False
        
        # Print success message
        self.print_success_message()
        
        return True

def main():
    """Entry point"""
    installer = AicodeInstaller()
    
    try:
        success = installer.install()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
