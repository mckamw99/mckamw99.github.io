# Site build

The site in `docs/` is generated from the markdown in `case-studies/`, `library/` and `generator/`, so the web pages and PDFs never disagree. Code is AI-assisted (Claude).

```
pip install markdown
python3 site-build/build_site.py .                      # writes docs/
python3 -m http.server 8765 --directory docs &          # serve it locally
python3 site-build/make_pdfs.py . http://localhost:8765 # writes docs/pdf/ with headless Chrome
```

GitHub Pages serves the `docs/` folder of the `main` branch.
