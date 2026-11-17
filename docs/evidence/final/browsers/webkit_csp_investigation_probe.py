import os, sys, tempfile, threading, sqlite3
from werkzeug.serving import make_server
from werkzeug.security import generate_password_hash
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.getcwd())
from app import create_app
d = tempfile.mkdtemp(); db = os.path.join(d, "p.db")
app = create_app({"TESTING": True, "DATABASE": db, "SECRET_KEY": "probe"})
with sqlite3.connect(db) as c:
    for u, r in (("pa","admin"),("pt","teacher"),("ps","student")):
        c.execute("INSERT INTO users (username,password_hash,role,active) VALUES (?,?,?,1)", (u, generate_password_hash("ProbePass1!"), r))
s = make_server("127.0.0.1", 0, app, threaded=True); threading.Thread(target=s.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{s.server_port}"
import logging; logging.getLogger("werkzeug").setLevel(logging.ERROR)
with sync_playwright() as p:
    for engine in ("webkit", "chromium"):
        b = getattr(p, engine).launch(headless=True)
        for user, page_path in (("pa","/admin"),("pt","/teacher"),("ps","/student")):
            ctx = b.new_context(); pg = ctx.new_page(); msgs = []
            pg.on("console", lambda m: msgs.append((m.type, m.text[:100], m.location)))
            pg.goto(base + "/login"); pg.fill("#username", user); pg.fill("#password", "ProbePass1!"); pg.click("#loginButton")
            pg.wait_for_url(base + page_path + "*"); pg.wait_for_timeout(800); nsel = pg.evaluate("document.querySelectorAll('select').length"); pg.screenshot(path=f"docs/evidence/final/browsers/screenshots/{engine}_{page_path.strip('/')}_overview.png", full_page=True)
            errs = [m for m in msgs if m[0] == "error"]
            print(f"{engine:8} {page_path:9} console errors: {len(errs)}  <select> elements: {nsel}")
            ctx.close()
        b.close()
s.shutdown()
