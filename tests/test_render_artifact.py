import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "scholar-megasearch" / "scripts" / "render_artifact.py"


def load_render_artifact_module():
    spec = importlib.util.spec_from_file_location("render_artifact", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RenderArtifactTests(unittest.TestCase):
    def make_run_dir(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        run_dir = Path(tmp.name) / "literature_search" / "unsafe-topic_2026-06-22"
        (run_dir / "pdfs").mkdir(parents=True)
        pdf_path = run_dir / "pdfs" / "01_attention-test.pdf"
        pdf_path.write_bytes(b"%PDF- test")

        corpus = [
            {
                "rank": 1,
                "title": "Attention <script>alert(1)</script>",
                "authors": ["Alice <A>", "Bob"],
                "year": 2025,
                "venue": "arXiv",
                "citations": 42,
                "score": 0.912345,
                "sources": ["arxiv", "semanticscholar"],
                "sources_count": 2,
                "queries": ["attention survey", "attention pdf"],
                "doi": "10.1000/test",
                "arxiv_id": "2401.00001",
                "pdf_url": "https://example.com/paper.pdf",
                "url": "https://example.com/paper",
                "abstract": "Uses <b>unsafe</b> HTML in fields.",
                "rank_layers": {
                    "provenance": 1,
                    "impact": 0.8,
                    "recency": 0.7,
                    "access": 1,
                    "relevance": 0.9,
                },
            },
            {
                "rank": 2,
                "title": "Closed Paper",
                "authors": ["Carol"],
                "year": 2021,
                "citations": 3,
                "sources": ["openalex"],
                "sources_count": 1,
                "queries": ["closed paper"],
                "abstract": "No open PDF found.",
                "url": "javascript:alert(2)",
            },
        ]
        (run_dir / "corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
        (run_dir / "summary.md").write_text("# Summary\n\nThis <should> be displayed safely.", encoding="utf-8")
        manifest = [
            {"rank": 1, "status": "ok", "route": "arxiv", "file": str(pdf_path), "bytes": 9},
            {"rank": 2, "status": "needs_mcp", "title": "Closed Paper"},
        ]
        (run_dir / "pdfs" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return run_dir

    def test_render_artifact_creates_safe_interactive_html(self):
        self.assertTrue(SCRIPT.exists(), "render_artifact.py should exist")
        module = load_render_artifact_module()
        run_dir = self.make_run_dir()

        output = module.render_artifact(run_dir)

        self.assertEqual(output, run_dir / "artifact" / "index.html")
        html = output.read_text(encoding="utf-8")
        self.assertIn("scholar-megasearch artifact", html)
        self.assertIn("Search papers", html)
        self.assertIn("sourceFilter", html)
        self.assertIn("pdfFilter", html)
        self.assertIn("sortSelect", html)
        self.assertIn("Attention &lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("Uses &lt;b&gt;unsafe&lt;/b&gt; HTML", html)
        self.assertIn("This &lt;should&gt; be displayed safely.", html)
        self.assertIn("PDF downloaded", html)
        self.assertIn("needs_mcp", html)
        self.assertIn("../pdfs/01_attention-test.pdf", html)
        self.assertNotIn("javascript:alert(2)", html)
        self.assertIn('data-sources="arxiv semanticscholar"', html)
        self.assertIn('data-pdf-status="ok"', html)

    def test_cli_exposes_localhost_preview_flags(self):
        self.assertTrue(SCRIPT.exists(), "render_artifact.py should exist")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--serve", result.stdout)
        self.assertIn("--bind", result.stdout)
        self.assertIn("127.0.0.1", result.stdout)
        self.assertIn("--port", result.stdout)
        self.assertIn("--open", result.stdout)


if __name__ == "__main__":
    unittest.main()
