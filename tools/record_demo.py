#!/usr/bin/env python3
"""Record the `telos view` demo GIF for the README.

The pipeline is: ``telos view --export`` into a temp directory, serve that
static site on a loopback port, drive a scripted Chromium visit with
Playwright (a fake DOM cursor is injected so moves and clicks are visible
on the recording), then encode the captured webm with ffmpeg into
``docs/demo.mp4`` and an optimised ``docs/demo.gif``.

Requirements on PATH: ``telos`` (or pass --telos) and ``ffmpeg``. Python
side: ``pip install playwright`` and ``playwright install chromium``.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright

VIEWPORT = {"width": 1280, "height": 800}
GIF_WIDTH = 960
GIF_FPS = 10
GIF_COLORS = 256
MAX_GIF_BYTES = 10_000_000

# Installed on every page: a dot that follows mousemove events (Playwright's
# mouse dispatches real DOM events, the OS cursor is never on the video) and
# a ripple ring on mousedown. Colours match the Telos identity.
CURSOR_JS = """
(() => {
  const install = () => {
    const style = document.createElement('style');
    style.textContent = `
      #demo-cursor{position:fixed;left:0;top:0;width:22px;height:22px;
        margin:-11px 0 0 -11px;border-radius:50%;background:rgba(1,98,251,.88);
        box-shadow:0 0 0 4px rgba(1,98,251,.22),0 2px 8px rgba(0,0,0,.35);
        pointer-events:none;z-index:2147483647;opacity:0;
        transition:opacity .2s,transform .12s;}
      #demo-cursor.down{transform:scale(.65);}
      .demo-ripple{position:fixed;width:80px;height:80px;border-radius:50%;
        border:3px solid rgba(3,225,240,.85);pointer-events:none;
        z-index:2147483646;transform:translate(-50%,-50%);
        animation:demo-ripple .5s ease-out forwards;}
      @keyframes demo-ripple{
        from{transform:translate(-50%,-50%) scale(0);opacity:1;}
        to{transform:translate(-50%,-50%) scale(1);opacity:0;}}
    `;
    document.head.appendChild(style);
    const dot = document.createElement('div');
    dot.id = 'demo-cursor';
    document.body.appendChild(dot);
    document.addEventListener('mousemove', e => {
      dot.style.opacity = '1';
      dot.style.left = e.clientX + 'px';
      dot.style.top = e.clientY + 'px';
    }, true);
    document.addEventListener('mousedown', e => {
      dot.classList.add('down');
      const r = document.createElement('div');
      r.className = 'demo-ripple';
      r.style.left = e.clientX + 'px';
      r.style.top = e.clientY + 'px';
      document.body.appendChild(r);
      setTimeout(() => r.remove(), 600);
    }, true);
    document.addEventListener('mouseup', () => dot.classList.remove('down'), true);
  };
  document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', install)
    : install();
})()
"""


@dataclass(frozen=True)
class TourResult:
    global_search_query: str
    intent_id: str
    scenario_id: str
    graph_query: str
    selected_node: str
    glossary_query: str
    glossary_consumers: int

SMOOTH_SCROLL_JS = """
([target, ms]) => new Promise(resolve => {
  const start = window.scrollY, delta = target - start, t0 = performance.now();
  const ease = t => t < .5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;
  const step = now => {
    const p = Math.min(1, (now - t0) / ms);
    window.scrollTo(0, start + delta * ease(p));
    p < 1 ? requestAnimationFrame(step) : resolve();
  };
  requestAnimationFrame(step);
})
"""


class Cursor:
    """Eased mouse moves so the injected dot glides instead of teleporting."""

    def __init__(self, page: Page, x: float = 640, y: float = 120):
        self.page, self.x, self.y = page, x, y

    def show(self) -> None:
        self.page.mouse.move(self.x, self.y)
        self.page.mouse.move(self.x + 1, self.y)

    def move_to(self, x: float, y: float, duration_ms: int = 500) -> None:
        steps = max(2, duration_ms // 33)
        for i in range(1, steps + 1):
            t = i / steps
            ease = 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2
            self.page.mouse.move(
                self.x + (x - self.x) * ease, self.y + (y - self.y) * ease
            )
            self.page.wait_for_timeout(33)
        self.x, self.y = x, y

    def click(self, target: str | Locator, settle_ms: int = 250) -> None:
        locator = self.page.locator(target) if isinstance(target, str) else target
        box = locator.bounding_box()
        if box is None:
            raise RuntimeError(f"no bounding box for {target!r}")
        self.move_to(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        self.page.wait_for_timeout(settle_ms)
        self.page.mouse.down()
        self.page.wait_for_timeout(280)
        self.page.mouse.up()

    def type(self, target: str | Locator, value: str, delay_ms: int = 70) -> None:
        locator = self.page.locator(target) if isinstance(target, str) else target
        self.click(locator)
        self.page.keyboard.type(value, delay=delay_ms)


def scroll_to(
    page: Page, selector: str, margin: int = 96, duration_ms: int = 600
) -> None:
    top = page.locator(selector).evaluate(
        "el => el.getBoundingClientRect().top + window.scrollY"
    )
    page.evaluate(SMOOTH_SCROLL_JS, [max(0, top - margin), duration_ms])


def enforce_gif_size(gif: Path) -> None:
    size = gif.stat().st_size
    if size >= MAX_GIF_BYTES:
        raise RuntimeError(
            f"{gif} is {size / 1e6:.1f} MB; the demo GIF must stay below 10.0 MB"
        )


def tour(page: Page, base: str) -> TourResult:
    """Walk the exported spec site and return its semantic checkpoints."""
    wait = page.wait_for_timeout
    cursor = Cursor(page)

    # Dashboard: project coherence and the headline coverage metrics.
    page.goto(f"{base}/index.html")
    page.get_by_role("heading", name="Dashboard").wait_for()
    cursor.show()
    wait(1200)

    # Global search: jump from a rule of the game to its owning intent.
    global_search_query = "three in a row"
    search_button = page.get_by_role("button", name="Search all Telos entities")
    cursor.click(search_button)
    dialog = page.get_by_role("dialog", name="Search Telos")
    global_input = dialog.get_by_role(
        "combobox", name="Search all Telos entities"
    )
    cursor.type(global_input, global_search_query)
    global_result = dialog.get_by_role("option").filter(has_text=re.compile(r"INT-\d{4}")).first
    global_result.wait_for()
    wait(700)
    cursor.click(global_result)
    page.wait_for_url(re.compile(r".*#/intent/INT-\d{4}$"))
    intent_id = re.search(r"INT-\d{4}", page.url).group(0)
    page.get_by_role("heading", name=re.compile(rf"^{intent_id} — ")).wait_for()
    statement = page.locator(".statement-card").filter(has_text="event-driven")
    statement.wait_for()
    wait(1100)

    # Intent detail: reveal the canonical statement and its first proved scenario.
    first_scenario = page.locator('[id^="scenario-SCN-"]').first
    first_scenario.wait_for()
    scenario_id = (first_scenario.get_attribute("id") or "").removeprefix("scenario-")
    scroll_to(page, f"#scenario-{scenario_id}", margin=180)
    scenario = page.locator(f"#scenario-{scenario_id}").filter(
        has_text=f"scenario {scenario_id}"
    )
    scenario.wait_for()
    wait(1200)

    # Graph finder: locate the same intent and focus its dependency node.
    cursor.click(page.get_by_role("link", name="Graph", exact=True))
    page.wait_for_url("**/index.html#/graph")
    page.get_by_role("heading", name="Graph", exact=True).wait_for()
    page.locator(".cyto-graph__canvas").wait_for()
    wait(900)
    graph_query = intent_id
    graph_input = page.get_by_label("Find node")
    cursor.type(graph_input, graph_query)
    graph_result = page.get_by_role("option").filter(has_text=intent_id)
    graph_result.wait_for()
    wait(700)
    cursor.click(graph_result)
    selected = page.locator(".selection-panel__id").filter(has_text=intent_id)
    selected.wait_for()
    wait(1300)

    # Glossary: the Board notion and the contexts that consume it.
    cursor.click(page.get_by_role("link", name="Glossary", exact=True))
    page.wait_for_url("**/index.html#/glossary")
    page.get_by_role("heading", name="Glossary", exact=True).wait_for()
    glossary_query = "Board"
    glossary_input = page.get_by_label("Search glossary")
    cursor.type(glossary_input, glossary_query)
    wait(500)
    board_card_selector = '[id="notion-board/Board"]'
    scroll_to(page, board_card_selector, margin=150)
    board_card = page.locator(board_card_selector)
    board_card.get_by_label("Used by entities").wait_for()
    consumer_count = board_card.locator("tbody tr").count()
    wait(1500)

    return TourResult(
        global_search_query=global_search_query,
        intent_id=intent_id,
        scenario_id=scenario_id,
        graph_query=graph_query,
        selected_node=intent_id,
        glossary_query=glossary_query,
        glossary_consumers=consumer_count,
    )


def record(site: Path, workdir: Path) -> Path:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=2,
            record_video_dir=str(workdir),
            record_video_size=VIEWPORT,
        )
        context.add_init_script(CURSOR_JS)
        page = context.new_page()

        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(site))
        )
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            tour(page, f"http://127.0.0.1:{server.server_address[1]}")
        finally:
            server.shutdown()
        video = page.video
        context.close()
        browser.close()
        return Path(video.path())


def encode(webm: Path, out_dir: Path) -> None:
    run = partial(subprocess.run, check=True)
    filters = f"fps={GIF_FPS},scale={GIF_WIDTH}:-1:flags=lanczos"
    palette = webm.with_name("palette.png")
    run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(webm),
            "-vf",
            "fps=30,scale=1280:-2:flags=lanczos",
            "-c:v",
            "libx264",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(out_dir / "demo.mp4"),
        ]
    )
    run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(webm),
            "-vf",
            f"{filters},palettegen=stats_mode=diff:max_colors={GIF_COLORS}",
            str(palette),
        ]
    )
    run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(webm),
            "-i",
            str(palette),
            "-lavfi",
            f"{filters}[x];[x][1:v]paletteuse="
            "dither=bayer:bayer_scale=5:diff_mode=rectangle",
            str(out_dir / "demo.gif"),
        ]
    )
    enforce_gif_size(out_dir / "demo.gif")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--site", type=Path, help="already-exported site (skips telos view --export)"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "docs",
        help="output directory (default: docs/)",
    )
    parser.add_argument("--telos", default="telos", help="telos binary")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="telos-demo-") as tmp:
        workdir = Path(tmp)
        site = args.site
        if site is None:
            site = workdir / "site"
            subprocess.run([args.telos, "view", "--export", str(site)], check=True)
        webm = record(site, workdir)
        encode(webm, args.out)

    for name in ("demo.gif", "demo.mp4"):
        size = (args.out / name).stat().st_size
        print(f"{args.out / name}  {size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
