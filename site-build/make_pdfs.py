"""Print every content page to PDF with headless Chrome, from the built HTML. AI-assisted (Claude).
Usage: python3 make_pdfs.py <repo_root> <base_url_of_served_docs>"""
import os, subprocess, sys
sys.argv += [] ; ROOT, BASE = os.path.abspath(sys.argv[1]), sys.argv[2].rstrip("/")
sys.path.insert(0, os.path.dirname(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("b", os.path.join(os.path.dirname(__file__), "build_site.py"))
out_dir = os.path.join(ROOT, "docs", "pdf"); os.makedirs(out_dir, exist_ok=True)
sys_argv = sys.argv; sys.argv = ["x", ROOT]; b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b); sys.argv = sys_argv
for src, out in b.PAGES.items():
    pdf = os.path.join(out_dir, b.pdf_name(out))
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", f"{BASE}/{out}"], check=True, capture_output=True, timeout=120)
    print(os.path.getsize(pdf), os.path.basename(pdf))
