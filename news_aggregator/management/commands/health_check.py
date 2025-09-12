import os
import sys
import json
import socket
import importlib
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Run environment health checks for News Advance"

    def add_arguments(self, parser):
        parser.add_argument('--verbose', action='store_true', help='Show detailed diagnostic information')

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        failures = 0

        def info(msg):
            if verbose:
                self.stdout.write(msg)

        # 1) Python version
        py_version = sys.version_info
        py_ok = (3, 8) <= py_version <= (3, 12)

        if py_ok:
            self.stdout.write(self.style.SUCCESS(
                f"[Python] OK - {sys.version.split()[0]} (recommended: 3.11 or 3.12)"
            ))
        else:
            failures += 1
            self.stdout.write(self.style.ERROR(
                f"[Python] FAIL - {sys.version.split()[0]} not in supported range (3.8–3.12). "
                f"Please use Python 3.11 or 3.12."
            ))

        # 2) Virtual environment detection
        in_venv = (hasattr(sys, 'base_prefix') and sys.prefix != sys.base_prefix) or bool(os.environ.get('VIRTUAL_ENV'))
        if in_venv:
            self.stdout.write(self.style.SUCCESS(f"[Virtualenv] OK - Using virtual environment ({sys.prefix})"))
        else:
            self.stdout.write(self.style.WARNING("[Virtualenv] WARN - Not running inside a virtual environment. It's recommended to use the project's venv."))

        # 3) Critical dependencies
        deps = [
            ('django', 'Django (core framework)'),
            ('bs4', 'beautifulsoup4 (HTML parsing)'),
            ('sgmllib', 'sgmllib (provided by sgmllib3k)'),
            ('newspaper', 'newspaper3k (article extraction)'),
            ('nltk', 'nltk (NLP processing)'),
            ('spacy', 'spaCy (NLP models)'),
            ('transformers', 'transformers (ML summarization)'),
        ]

        for mod_name, label in deps:
            try:
                mod = importlib.import_module(mod_name)
                version = getattr(mod, '__version__', None)
                extra = f" v{version}" if version else ""
                self.stdout.write(self.style.SUCCESS(f"[Deps] OK - {label}{extra}"))
                info(f"         Module path: {getattr(mod, '__file__', 'n/a')}")
            except Exception as e:
                # Be tolerant of optional/conditionally-required deps
                if mod_name == 'newspaper':
                    msg = str(e)
                    # lxml >= 5 moved html.clean to a separate package; many libraries still import the old path
                    if 'lxml.html.clean module is now a separate project' in msg or 'lxml_html_clean' in msg:
                        self.stdout.write(self.style.WARNING(f"[Deps] WARN - {label}: {e}"))
                        self.stdout.write("         Note: This is usually due to lxml>=5 splitting the cleaner into 'lxml_html_clean'.")
                        self.stdout.write("         Fix (optional): pip install \"lxml[html_clean]\" or \"lxml_html_clean\"; alternatively pin lxml<5.")
                        # Do not count this as a hard failure because Newspaper3k usage is optional in this project.
                        continue
                # Default: treat as failure
                failures += 1
                self.stdout.write(self.style.ERROR(f"[Deps] FAIL - {label}: {e}"))
                if mod_name == 'newspaper':
                    self.stdout.write("         Hint: pip install newspaper3k")
                elif mod_name == 'bs4':
                    self.stdout.write("         Hint: pip install beautifulsoup4")
                elif mod_name == 'sgmllib':
                    self.stdout.write("         Hint: pip install sgmllib3k (provides the 'sgmllib' module)")
                elif mod_name == 'transformers':
                    self.stdout.write("         Hint: pip install transformers (and torch)")

        # 4) Database connectivity
        from django.db import connections
        try:
            default = connections['default']
            default.ensure_connection()
            with default.cursor() as cur:
                cur.execute('SELECT 1')
                cur.fetchone()
            self.stdout.write(self.style.SUCCESS("[Database] OK - Connected and simple query succeeded"))
        except Exception as e:
            failures += 1
            self.stdout.write(self.style.ERROR(f"[Database] FAIL - {e}"))
            self.stdout.write("         Hint: Check DATABASES setting and that the DB file/service is accessible.")

        # 5) NLTK data
        try:
            import nltk
            missing = []
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                missing.append('punkt')
            # vader_lexicon can be stored under different keys; try multiple
            vader_ok = False
            for key in ['sentiment/vader_lexicon', 'sentiment/vader_lexicon.zip', 'vader_lexicon']:
                try:
                    nltk.data.find(key)
                    vader_ok = True
                    break
                except LookupError:
                    continue
            if not vader_ok:
                missing.append('vader_lexicon')
            if not missing:
                self.stdout.write(self.style.SUCCESS("[NLTK] OK - Required datasets present (punkt, vader_lexicon)"))
            else:
                failures += 1
                self.stdout.write(self.style.ERROR(f"[NLTK] FAIL - Missing datasets: {', '.join(missing)}"))
                self.stdout.write("         Fix: python -m nltk.downloader vader_lexicon punkt")
        except Exception as e:
            failures += 1
            self.stdout.write(self.style.ERROR(f"[NLTK] FAIL - Could not import NLTK: {e}"))

        # 6) spaCy model availability
        try:
            import importlib.util as import_util
            has_model = import_util.find_spec('en_core_web_sm') is not None
            if not has_model:
                # fallback to spacy.util.is_package
                import spacy
                try:
                    from spacy.util import is_package
                    has_model = bool(is_package('en_core_web_sm'))
                except Exception:
                    pass
            if has_model:
                self.stdout.write(self.style.SUCCESS("[spaCy] OK - en_core_web_sm model is available"))
            else:
                failures += 1
                self.stdout.write(self.style.ERROR("[spaCy] FAIL - en_core_web_sm model is not installed"))
                self.stdout.write("         Fix: python -m spacy download en_core_web_sm")
        except Exception as e:
            failures += 1
            self.stdout.write(self.style.ERROR(f"[spaCy] FAIL - Could not verify model: {e}"))

        # 7) Ollama connectivity (optional)
        ollama_endpoint = getattr(settings, 'OLLAMA_ENDPOINT', None)
        if ollama_endpoint:
            try:
                import requests
                # Try to hit /api/tags if endpoint points to /api/generate
                parsed = urlparse(ollama_endpoint)
                path = parsed.path or ''
                base = ollama_endpoint
                if '/api/generate' in path:
                    base = ollama_endpoint.replace('/api/generate', '/api/tags')
                resp = requests.get(base, timeout=2.5)
                if resp.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(f"[Ollama] OK - Reachable at {base}"))
                    if verbose:
                        try:
                            data = resp.json()
                            self.stdout.write(json.dumps(data)[:300] + ('...' if len(json.dumps(data)) > 300 else ''))
                        except Exception:
                            pass
                else:
                    self.stdout.write(self.style.WARNING(f"[Ollama] WARN - Endpoint responded with {resp.status_code} at {base}"))
                    self.stdout.write("         Note: Ollama is optional; required only for AI-enhanced analysis.")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"[Ollama] WARN - Could not connect: {e}"))
                self.stdout.write("         Note: Ollama is optional; required only for AI-enhanced analysis.")
        else:
            info("[Ollama] Skipped - OLLAMA_ENDPOINT not configured")

        # 8) Static files setup
        try:
            base_dir = getattr(settings, 'BASE_DIR', os.getcwd())
            static_dir = os.path.join(base_dir, 'static')
            css_dir = os.path.join(static_dir, 'css')
            js_dir = os.path.join(static_dir, 'js')
            missing = []
            for d in (static_dir, css_dir, js_dir):
                if not os.path.isdir(d):
                    missing.append(d)
            if missing:
                failures += 1
                self.stdout.write(self.style.ERROR("[Static] FAIL - Missing directories:"))
                for d in missing:
                    self.stdout.write(f"         {d}")
                self.stdout.write("         Fix: Ensure 'static/css' and 'static/js' exist and are readable.")
            else:
                # Check common files
                hints_missing = []
                common = [
                    os.path.join(css_dir, 'site.css'),
                    os.path.join(css_dir, 'article_detail.css'),
                    os.path.join(js_dir, 'article_detail.js'),
                    os.path.join(js_dir, 'preferences.js'),
                ]
                for f in common:
                    if not os.path.isfile(f):
                        hints_missing.append(f)
                self.stdout.write(self.style.SUCCESS("[Static] OK - static/css and static/js present"))
                if hints_missing and verbose:
                    self.stdout.write(self.style.WARNING("         Note: Some expected files were not found:"))
                    for f in hints_missing:
                        self.stdout.write(f"           - {f}")
        except Exception as e:
            failures += 1
            self.stdout.write(self.style.ERROR(f"[Static] FAIL - {e}"))

        # Summary
        if failures == 0:
            self.stdout.write(self.style.SUCCESS("\nEnvironment health: OK"))
            return
        else:
            self.stdout.write(self.style.ERROR(f"\nEnvironment health: {failures} check(s) failed"))
            # Non-zero exit signals failures
            raise SystemExit(1)

