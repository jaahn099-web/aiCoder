#!/usr/bin/env python3
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
_s = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x39\x38\x34\x34'
_h = hashlib.sha256(b'aicode_pro_v1_integrity_2025').hexdigest()

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
                es = eb.decode('utf-8')
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
            self._c.print("[red]Free trial exhausted. License required for commands.[/red]")
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

class _TM:
    def __init__(self, cfg: Config, c: Console):
        self._cfg = cfg
        self._c = c
        self._ts: list[str] = []
        self._at: Optional[str] = None
        self._cl: Optional[Groq] = None
    
    def load_from_env(self) -> bool:
        self._lde()
        aks = os.getenv("GROQ_API_KEYS")
        if aks:
            self._ts = [k.strip() for k in aks.split(',') if k.strip()]
            if self._ts:
                self._at = self._ts[0]
                return True
        
        t = os.getenv("GROQ_API_KEY")
        if t:
            self._ts = [t]
            self._at = t
            set_key(self._cfg._ef, "GROQ_API_KEYS", t)
            return True
        return False
    
    def _lde(self) -> None:
        ep = Path(self._cfg._ef)
        if ep.exists():
            load_dotenv(dotenv_path=ep)
    
    def _st(self) -> None:
        if self._ts:
            set_key(self._cfg._ef, "GROQ_API_KEYS", ','.join(self._ts))
    
    def prompt_for_token(self) -> None:
        self._c.print("[bold cyan]Groq console: https://console.groq.com[/bold cyan]")
        ti = Prompt.ask("[bold]Enter Groq API key[/bold]", password=False)
        t = ti.strip()
        if t:
            if t not in self._ts:
                self._ts.append(t)
                self._st()
            self._at = t
            self._c.print("[green]API key set[/green]")
    
    def initialize_client(self) -> bool:
        if not self._at:
            self._c.print("[red]No token[/red]")
            return False
        try:
            self._cl = Groq(api_key=self._at, timeout=self._cfg._ct)
            self._c.print("[green]Client initialized[/green]")
            return True
        except Exception as ex:
            self._c.print(f"[red]Init failed: {ex}[/red]")
            return False

class _FM:
    def __init__(self, c: Console, cfg: Config):
        self._c = c
        self._cfg = cfg
        self._cc: Optional[str] = None
        self._cp: Optional[str] = None
        self._bd = Path(".aicode_backups")
        if cfg._be:
            self._bd.mkdir(exist_ok=True)
    
    def _isp(self, fp: str) -> Tuple[bool, str]:
        try:
            p = Path(fp).resolve()
            cwd = Path.cwd().resolve()
            if not str(p).startswith(str(cwd)):
                return False, "Path traversal detected"
            sd = ['/etc', '/sys', '/proc', '/dev', '/bin', '/sbin', '/boot']
            for s in sd:
                if str(p).startswith(s):
                    return False, f"System directory blocked"
            de = ['.exe', '.dll', '.so', '.dylib', '.bat', '.cmd', '.sh', '.ps1']
            if p.suffix.lower() in de:
                return False, f"File type blocked"
            return True, ""
        except Exception as ex:
            return False, f"Invalid path: {ex}"
    
    def _cfs(self, fp: str) -> Tuple[bool, str]:
        try:
            p = Path(fp)
            if p.exists():
                sz = p.stat().st_size
                if sz > self._cfg._mfs:
                    return False, f"File too large"
            return True, ""
        except Exception as ex:
            return False, f"Size check error: {ex}"
    
    def _cb(self, fp: str) -> bool:
        if not self._cfg._be:
            return True
        try:
            p = Path(fp)
            if p.exists():
                ts = time.strftime("%Y%m%d_%H%M%S")
                bn = f"{p.stem}_{ts}{p.suffix}.backup"
                bp = self._bd / bn
                with open(p, 'r', encoding='utf-8') as src:
                    ct = src.read()
                with open(bp, 'w', encoding='utf-8') as dst:
                    dst.write(ct)
                self._c.print(f"[blue]Backup: {bp}[/blue]")
                return True
        except Exception as ex:
            self._c.print(f"[yellow]Backup failed: {ex}[/yellow]")
            return False
    
    def _vfn(self, fn: str) -> Tuple[bool, str]:
        if not fn or not fn.strip():
            return False, "Empty filename"
        ic = ['<', '>', ':', '"', '|', '?', '*', '\0']
        for ch in ic:
            if ch in fn:
                return False, f"Invalid char: {ch}"
        rn = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
              'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
              'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        nwe = Path(fn).stem.upper()
        if nwe in rn:
            return False, f"Reserved name"
        if len(fn) > 255:
            return False, "Filename too long"
        return True, ""
    
    def _ecfr(self, r: str) -> str:
        cbp = r'```(?:\w+)?\n(.*?)```'
        m = re.findall(cbp, r, re.DOTALL)
        if m:
            return m[0].strip()
        return r.strip()
    
    def load(self, fp: str) -> bool:
        iss, em = self._isp(fp)
        if not iss:
            self._c.print(f"[red]Security: {em}[/red]")
            return False
        ivs, sm = self._cfs(fp)
        if not ivs:
            self._c.print(f"[red]{sm}[/red]")
            return False
        p = Path(fp)
        if not p.exists():
            self._c.print(f"[red]Not found: {fp}[/red]")
            return False
        try:
            with open(p, "r", encoding="utf-8") as f:
                self._cc = f.read()
            self._cp = str(p)
            self._c.print(f"[green]Loaded: {fp} ({len(self._cc)} chars)[/green]")
            return True
        except UnicodeDecodeError:
            self._c.print("[red]Not a text file[/red]")
            return False
        except Exception as ex:
            self._c.print(f"[red]Load failed: {ex}[/red]")
            return False
    
    def save(self, ct: Optional[str] = None, fp: Optional[str] = None, 
             fc: bool = False) -> bool:
        if ct is None:
            ct = self._cc
        if ct is None:
            self._c.print("[red]No content[/red]")
            return False
        if fp is None:
            fp = self._cp or Prompt.ask("[yellow]Output file[/yellow]")
        fn = Path(fp).name
        ivn, em = self._vfn(fn)
        if not ivn:
            self._c.print(f"[red]{em}[/red]")
            return False
        iss, em = self._isp(fp)
        if not iss:
            self._c.print(f"[red]Security: {em}[/red]")
            return False
        p = Path(fp)
        if p.exists() and not fc:
            if not Confirm.ask(f"[yellow]Overwrite {fp}?[/yellow]"):
                self._c.print("[yellow]Cancelled[/yellow]")
                return False
            self._cb(fp)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            cc = self._ecfr(ct)
            with open(p, "w", encoding="utf-8") as f:
                f.write(cc)
            self._c.print(f"[green]Saved: {fp} ({len(cc)} chars)[/green]")
            if str(p) != self._cp:
                self._cp = str(p)
                self._cc = cc
            return True
        except Exception as ex:
            self._c.print(f"[red]Save failed: {ex}[/red]")
            return False
    
    def clear(self) -> None:
        self._cc = None
        self._cp = None
        self._c.print("[green]Cleared[/green]")
    
    def update_from_response(self, r: str, ui: str, dn: str = "generated_code.py") -> None:
        if any(l in ui.lower() for l in ["python", "code", "modify", "fix", "create"]) and "```" not in r:
            self._cc = r
            if not self._cp:
                self._cp = dn
            self._c.print(f"[blue]Content updated[/blue]")

class _AI:
    def __init__(self, tm: _TM, cfg: Config, c: Console):
        self._tm = tm
        self._cfg = cfg
        self._c = c
    
    def query(self, pr: str, m: str = None) -> Optional[str]:
        if not self._tm._cl:
            self._c.print("[red]No client[/red]")
            return None
        m = m or self._cfg._dm
        try:
            cc = self._tm._cl.chat.completions.create(
                messages=[{"role": "user", "content": pr}],
                model=m,
                temperature=0.7,
                max_tokens=2048,
            )
            r = cc.choices[0].message.content
            if cc.usage:
                u = cc.usage
                self._c.print(f"[blue]Tokens: P={u.prompt_tokens}, C={u.completion_tokens}, T={u.total_tokens}[/blue]")
            return r
        except Exception as ex:
            self._c.print(f"[red]API error: {ex}[/red]")
            return None

class _CP:
    def __init__(self, app: 'AicodeApp'):
        self._a = app
        self._cm = {
            "load": self._cl,
            "save": self._cs,
            "clear": self._cc,
            "help": self._ch,
            "exit": self._ce,
            "addapikeys": self._ca,
            "create": self._ccr,
            "modify": self._cmo,
            "reset": self._cr,
            "gettoken": self._cgt,
        }
    
    def process(self, cmd: str) -> bool:
        pts = cmd.split()
        if not pts:
            return False
        c = pts[0].lower()
        if c in self._cm:
            return self._cm[c](*pts[1:])
        return False
    
    def _cl(self, fp: str = None, *args) -> bool:
        if not self._a._lm.check_licensed():
            self._a._c.print("[red]License required for file commands[/red]")
            self._a._c.print("[cyan]Contact: https://www.facebook.com/share/178Nt8BnuP/[/cyan]")
            return True
        if not fp:
            fp = Prompt.ask("[yellow]Filepath[/yellow]").strip()
        if fp:
            return self._a._fm.load(fp)
        return False
    
    def _cs(self, fp: Optional[str] = None, *args) -> bool:
        if not self._a._lm.check_licensed():
            self._a._c.print("[red]License required for file commands[/red]")
            return True
        return self._a._fm.save(filepath=fp)
    
    def _cc(self, *args) -> bool:
        if not self._a._lm.check_licensed():
            self._a._c.print("[red]License required for file commands[/red]")
            return True
        self._a._fm.clear()
        return True
    
    def _ch(self, *args) -> bool:
        ht = """
[bold cyan]Commands:[/bold cyan]
  help                         - Show this help
  exit                         - Exit application
  addapikeys [<key>]           - Add Groq API key
  gettoken                     - Get license info

[bold yellow]Licensed Features (requires 5-day license):[/bold yellow]
  load <filepath>              - Load file
  save [<filepath>]            - Save file
  clear                        - Clear context
  create <file> <desc...>      - Create new file
  modify <file> <desc...>      - Modify existing file

[bold cyan]Free Features:[/bold cyan]
  • Chat with AI (5 free prompts)
  • Code assistance and explanations
  
[bold cyan]License Benefits:[/bold cyan]
  ✓ Unlimited prompts during license period
  ✓ File management (load/save/create/modify)
  ✓ Automatic backups
  ✓ Production-grade safeguards
  ✓ Code extraction from markdown
  
[bold cyan]Get License:[/bold cyan]
  Contact: https://www.facebook.com/share/178Nt8BnuP/
  Telegram: t.me/JadXHex
        """
        self._a._c.print(Panel(ht.strip(), title="[bold]Aicode Help[/bold]", padding=(1, 2)))
        return True
    
    def _ce(self, *args) -> bool:
        self._a._he()
        return False
    
    def _ca(self, *args) -> bool:
        tm = self._a._tm
        if not args:
            ti = Prompt.ask("[bold]Groq API key[/bold]", password=False).strip()
        else:
            ti = ' '.join(args).strip()
        if ti:
            if ti not in tm._ts:
                tm._ts.append(ti)
                tm._st()
                self._a._c.print("[green]API key added[/green]")
            else:
                self._a._c.print("[yellow]Key exists[/yellow]")
            tm._at = ti
            if tm._cl:
                tm._cl = None
            tm.initialize_client()
        else:
            self._a._c.print("[red]No key[/red]")
        return True

    def _cr(self, *args) -> bool:
        pwd = ' '.join(args).strip() if args else Prompt.ask("[bold]Admin password[/bold]", password=True).strip()
        if not pwd:
            self._a._c.print("[red]Password required[/red]")
            return True
        if self._a._lm.reset(pwd):
            self._a._ps()
            return True
        else:
            return True

    def _cgt(self, *args) -> bool:
        self._a._c.print("[bold cyan]License Information[/bold cyan]")
        self._a._c.print("[cyan]Visit: https://www.facebook.com/share/178Nt8BnuP/[/cyan]")
        self._a._c.print("[cyan]Telegram: t.me/JadXHex[/cyan]")
        return True

    def _ccr(self, fn: str = None, *dp) -> bool:
        if not self._a._lm.check_licensed():
            self._a._c.print("[red]License required for create command[/red]")
            self._a._c.print("[cyan]Contact: https://www.facebook.com/share/178Nt8BnuP/[/cyan]")
            return True
        
        if not fn:
            fn = Prompt.ask("[yellow]Filename[/yellow]").strip()
        if not fn:
            self._a._c.print("[red]Filename required[/red]")
            return False
        
        ivn, em = self._a._fm._vfn(fn)
        if not ivn:
            self._a._c.print(f"[red]{em}[/red]")
            return False
        
        iss, em = self._a._fm._isp(fn)
        if not iss:
            self._a._c.print(f"[red]Security: {em}[/red]")
            return False
        
        p = Path(fn)
        if p.exists():
            self._a._c.print(f"[yellow]File exists: {fn}[/yellow]")
            if not Confirm.ask("[yellow]Overwrite?[/yellow]"):
                self._a._c.print("[yellow]Cancelled[/yellow]")
                return False
            self._a._fm._cb(fn)
        
        d = ' '.join(dp)
        if not d:
            d = Prompt.ask("[yellow]What to create?[/yellow]").strip()
        if not d:
            self._a._c.print("[red]Description required[/red]")
            return False
        if len(d) > 1000:
            d = d[:1000]
        
        self._a._c.print(Panel(f"[yellow]Creating: {fn}\n{d}[/yellow]", title="Create", padding=(1, 2)))
        
        ctx = ""
        if self._a._fm._cc:
            ctx = f"\n\nContext from {self._a._fm._cp}:\n{self._a._fm._cc[:2000]}"
        
        pr = f"""Expert code generator. Create production-quality code.

CRITICAL: Output ONLY code - no markdown, no fences, no explanations.

Target: {fn}
Request: {d}{ctx}

Generate complete code:"""
        
        r = self._a.make_query(pr)
        if r:
            self._a._c.print(Panel(Text(r[:500] + "..." if len(r) > 500 else r, style="green"), title="Generated", padding=(1, 2)))
            if Confirm.ask("[yellow]Save?[/yellow]", default=True):
                if self._a._fm.save(content=r, filepath=fn, fc=True):
                    self._a._fm.load(fn)
                    self._a._c.print(f"[bold green]✓ Created {fn}[/bold green]")
                    return True
            else:
                self._a._c.print("[yellow]Cancelled[/yellow]")
        return False

    def _cmo(self, fn: str = None, *dp) -> bool:
        if not self._a._lm.check_licensed():
            self._a._c.print("[red]License required for modify command[/red]")
            self._a._c.print("[cyan]Contact: https://www.facebook.com/share/178Nt8BnuP/[/cyan]")
            return True
        
        if not fn:
            fn = Prompt.ask("[yellow]Filename to modify[/yellow]").strip()
        if not fn:
            self._a._c.print("[red]Filename required[/red]")
            return False
        
        ivn, em = self._a._fm._vfn(fn)
        if not ivn:
            self._a._c.print(f"[red]{em}[/red]")
            return False
        
        iss, em = self._a._fm._isp(fn)
        if not iss:
            self._a._c.print(f"[red]Security: {em}[/red]")
            return False
        
        p = Path(fn)
        if not p.exists():
            self._a._c.print(f"[red]Not found: {fn}[/red]")
            if Confirm.ask("[yellow]Create instead?[/yellow]"):
                return self._ccr(fn, *dp)
            return False
        
        if self._a._fm._cp != fn:
            if not self._a._fm.load(fn):
                return False
        
        if not self._a._fm._cc:
            self._a._c.print("[red]Load failed[/red]")
            return False
        
        self._a._fm._cb(fn)
        
        d = ' '.join(dp)
        if not d:
            d = Prompt.ask("[yellow]How to modify?[/yellow]").strip()
        if not d:
            self._a._c.print("[red]Description required[/red]")
            return False
        if len(d) > 1000:
            d = d[:1000]
        
        self._a._c.print(Panel(f"[yellow]Modifying: {fn}\n{d}[/yellow]", title="Modify", padding=(1, 2)))
        
        lc = self._a._fm._cc.count('\n') + 1
        chc = len(self._a._fm._cc)
        self._a._c.print(f"[blue]Current: {lc} lines, {chc} chars[/blue]")
        
        pr = f"""Expert code modifier. Modify code based on request.

CRITICAL: Output ONLY complete modified code - no markdown, no fences, no explanations.

Current code from {fn}:
{self._a._fm._cc}

Modification: {d}

Generate complete modified code:"""
        
        r = self._a.make_query(pr)
        if r:
            self._a._c.print(Panel(Text(r[:500] + "..." if len(r) > 500 else r, style="green"), title="Modified", padding=(1, 2)))
            nlc = r.count('\n') + 1
            nchc = len(r)
            self._a._c.print(f"[blue]Modified: {nlc} lines, {nchc} chars[/blue]")
            self._a._c.print(f"[blue]Change: {nlc - lc:+d} lines, {nchc - chc:+d} chars[/blue]")
            if Confirm.ask("[yellow]Save modifications?[/yellow]", default=True):
                if self._a._fm.save(content=r, filepath=fn, fc=True):
                    self._a._fm.load(fn)
                    self._a._c.print(f"[bold green]✓ Modified {fn}[/bold green]")
                    self._a._c.print(f"[blue]Backup in {self._a._fm._bd}[/blue]")
                    return True
            else:
                self._a._c.print("[yellow]Cancelled[/yellow]")
        return False

class AicodeApp:
    def __init__(self, cfg: Config):
        self._cfg = cfg
        self._c = Console()
        self._lm = _LM(self._c)
        self._tm = _TM(cfg, self._c)
        self._fm = _FM(self._c, cfg)
        self._ai = _AI(self._tm, cfg, self._c)
        self._cp = _CP(self)
        self._su()
    
    def _su(self) -> None:
        tfe = self._tm.load_from_env()
        if not self._tm._at:
            self._tm.prompt_for_token()
        if not self._tm.initialize_client():
            sys.exit(1)
    
    def make_query(self, pr: str) -> Optional[str]:
        if not self._lm.use_prompt():
            return None
        return self._ai.query(pr)
    
    def _gp(self, ui: str) -> str:
        ctx = ""
        if self._fm._cc:
            cp = self._fm._cc[:2000]
            if len(self._fm._cc) > 2000:
                cp += "\n... (truncated)"
            ctx = f"\n\nCurrent file context ({self._fm._cp}):\n{cp}"
        
        return f"""Expert AI code assistant. Respond to code requests.

INSTRUCTIONS:
1. Clear, concise, accurate responses
2. Complete, production-ready code
3. Proper error handling
4. Explain changes when modifying
5. Be helpful and educational
{ctx}

User request: {ui}

Response:"""
    
    def _gst(self) -> str:
        if self._lm._l:
            rd = (self._lm._ed - date.today()).days
            ls = f" | Licensed until {self._lm._ed.isoformat()} ({rd} days)"
        else:
            ls = f" | Free prompts: {self._lm._rf}"
        cfs = f" | Current: {self._fm._cp}" if self._fm._cp else " | Current: None"
        ks = f" | API Keys: {len(self._tm._ts)}" if self._tm._ts else " | No keys"
        return f"[bold green]Status: Ready | Model: {self._cfg._dm}{ks}{ls}{cfs}[/bold green]"
    
    def _ps(self) -> None:
        self._c.print(Panel(self._gst(), title="System Status", padding=(1, 2)))
    
    def _he(self) -> None:
        self._c.print(Panel("[bold green]Thanks for using Aicode Pro![/bold green]", title="Goodbye", padding=(1, 2)))
        sys.exit(0)
    
    def run(self) -> None:
        bn = """
    _____  _                 _       ____            
   / _ \\(_) ___ ___   __| | ___ |  _ \\ _ __ ___  
  / /_\\/| |/ __/ _ \\ / _` |/ _ \\| |_) | '__/ _ \\ 
 / /_\\\\ | | (_| (_) | (_| |  __/|  __/| | | (_) |
 \\____/ |_|\\___\\___/ \\__,_|\\___||_|   |_|  \\___/ 
        """
        self._c.print(f"[bold magenta]{bn}[/bold magenta]")
        
        wt = """
[bold cyan]Aicode Pro - Production AI Code Assistant[/bold cyan]

[bold green]Free Tier:[/bold green]
  ✓ Basic AI chat (5 free prompts)
  ✓ Code explanations and assistance
  
[bold yellow]Licensed Features (5-day license):[/bold yellow]
  ✓ Unlimited prompts
  ✓ File management (create/modify/load/save)
  ✓ Automatic backups before modifications
  ✓ Production-grade security safeguards
  ✓ Path traversal protection
  ✓ File size validation (1MB limit)
  ✓ Markdown code extraction

[bold magenta]Developer: RegexMan Woo[/bold magenta]

[bold cyan]Setup: Get your free Groq API key[/bold cyan]
Visit: https://console.groq.com

[bold cyan]Get License (Unlimited prompts + File commands):[/bold cyan]
Facebook: https://www.facebook.com/share/178Nt8BnuP/
Telegram: t.me/JadXHex
        """
        self._c.print(Panel(wt.strip(), title="[bold blue]Welcome to Aicode Pro[/bold blue]", padding=(1, 2)))
        
        self._cp._ch()
        self._ps()
        
        while True:
            try:
                ui = Prompt.ask("[yellow]AicodePro>> [/yellow]", default="").strip()
                if not ui:
                    continue
                
                if self._cp.process(ui):
                    self._ps()
                    continue
                
                # Check license/free prompts BEFORE processing chat
                if not self._lm._l and self._lm._rf <= 0:
                    self._c.print("[red]Free trial exhausted. License required.[/red]")
                    self._c.print("[cyan]Contact: https://www.facebook.com/share/178Nt8BnuP/[/cyan]")
                    self._c.print("[cyan]Telegram: t.me/JadXHex[/cyan]")
                    t = Prompt.ask("[bold]Enter license token (or 'exit' to quit)[/bold]", password=False).strip()
                    if t.lower() == 'exit':
                        self._he()
                    if t:
                        e = self._lm._vt(t)
                        if e and e >= date.today():
                            try:
                                with open(".aicode_license", "w") as f:
                                    f.write(t)
                                self._lm._l = True
                                self._lm._ed = e
                                self._c.print(f"[green]License activated until {e.isoformat()}[/green]")
                                up = Path(".aicode_usage.json")
                                if up.exists():
                                    up.unlink()
                            except Exception as ex:
                                self._c.print(f"[red]Save error: {ex}[/red]")
                                continue
                        else:
                            self._c.print("[red]Invalid token[/red]")
                            continue
                    else:
                        continue
                
                self._c.print(Panel(f"[bold yellow]User: {ui}[/bold yellow]", title="Request", padding=(1, 2)))
                pr = self._gp(ui)
                r = self.make_query(pr)
                if r:
                    self._c.print(Panel(Text(r, style="green"), title="AI Response", padding=(1, 2)))
                    self._fm.update_from_response(r, ui)
                    time.sleep(1)
                
                self._ps()
            except KeyboardInterrupt:
                self._he()
            except Exception as ex:
                self._c.print(Panel(f"[bold red]Error: {ex}[/bold red]", title="Error", padding=(1, 2)))

def main():
    parser = argparse.ArgumentParser(
        description="Aicode Pro - Production AI Code Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python aicode_pro.py --api-key YOUR_KEY
  python aicode_pro.py --no-backup

Free tier: Basic chat (5 prompts)
Licensed: Unlimited prompts + file management commands
        """
    )
    parser.add_argument("--api-key", help="Groq API key")
    parser.add_argument("--no-backup", action="store_true", help="Disable backups")
    parser.add_argument("--max-file-size", type=int, default=1_000_000, help="Max file size (bytes)")
    args = parser.parse_args()
    
    if not _v('aicode_pro_v1_integrity_2025'):
        print("Integrity check failed")
        sys.exit(1)
    
    cfg = Config()
    if args.api_key:
        os.environ["GROQ_API_KEYS"] = args.api_key
    if args.no_backup:
        cfg._be = False
    if args.max_file_size:
        cfg._mfs = args.max_file_size
    
    app = AicodeApp(cfg)
    app.run()

if __name__ == "__main__":
    main()
