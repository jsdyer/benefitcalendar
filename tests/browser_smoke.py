"""Exercise the built application at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_EXECUTABLE") or None)
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.locator("#region").select_option("ON")
                page.locator("#period").select_option("all")
                assert page.locator('tr[data-region="AB"]:visible').count() == 0
                page.locator("#program").select_option("otb")
                assert page.locator('tr[data-program="otb"]:visible').count() >= 12
                assert page.locator("#download").get_attribute("href").endswith("/calendars/otb.ics")
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/cpp-payment-dates/")
                assert page.locator("#program").input_value() == "cpp"
                page.locator("#period").select_option("all")
                assert page.locator('tr[data-program="cpp"]:visible').count() >= 12
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                assert not errors, errors
                browser.close()
            print("Browser checks passed for routes, controls and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
