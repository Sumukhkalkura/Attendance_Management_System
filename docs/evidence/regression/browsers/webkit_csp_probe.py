import os, sys, tempfile, threading, sqlite3, json, logging
from werkzeug.serving import make_server
from werkzeug.security import generate_password_hash
from playwright.sync_api import sync_playwright
ROOT = sys.argv[1]; sys.path.insert(0, ROOT); os.chdir(ROOT)
from app import create_app
d = tempfile.mkdtemp(); db = os.path.join(d, "p.db")
app = create_app({"TESTING": True, "DATABASE": db, "SECRET_KEY": "probe"})
with sqlite3.connect(db) as c:
    for u, r in (("pa","admin"),("pt","teacher"),("ps","student")):
        c.execute("INSERT INTO users (username,password_hash,role,active) VALUES (?,?,?,1)", (u, generate_password_hash("ProbePass1!"), r))
logging.getLogger("werkzeug").setLevel(logging.ERROR)
s = make_server("127.0.0.1", 0, app, threaded=True); threading.Thread(target=s.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{s.server_port}"
INIT = """window.__v=[];document.addEventListener('securitypolicyviolation',e=>window.__v.push({blocked:e.blockedURI,directive:e.violatedDirective,effective:e.effectiveDirective,source:e.sourceFile,line:e.lineNumber,col:e.columnNumber,sample:e.sample,target:(e.target&&e.target.nodeName)||''}),true);"""
engines = sys.argv[2].split(",") if len(sys.argv) > 2 else ["webkit", "chromium"]
with sync_playwright() as p:
    for engine in engines:
        b = getattr(p, engine).launch(headless=True)
        for user, page_path in (("pa","/admin"),("pt","/teacher"),("ps","/student")):
            ctx = b.new_context(); pg = ctx.new_page(); msgs = []
            pg.add_init_script(INIT)
            pg.on("console", lambda m: msgs.append((m.type, m.text)))
            pg.goto(base + "/login"); pg.fill("#username", user); pg.fill("#password", "ProbePass1!"); pg.click("#loginButton")
            pg.wait_for_url(base + page_path + "*"); pg.wait_for_timeout(800)
            v = pg.evaluate("window.__v"); nsel = pg.evaluate("document.querySelectorAll('select').length")
            errs = [m for m in msgs if m[0] == "error"]
            print(f"{engine:8} {page_path:9} selects={nsel} console_errors={len(errs)} violations={len(v)}")
            for e in errs[:2]: print("   console:", e[1][:230])
            for x in {json.dumps(i, sort_keys=True) for i in v}: print("   violation:", x)
            ctx.close()
        b.close()
s.shutdown()
