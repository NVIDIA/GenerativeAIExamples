"""Run against the local app: python tests/browser_workflow.py (requires Playwright + Edge)."""

import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "test-results"


def run():
    ARTIFACTS.mkdir(exist_ok=True)
    checks = []
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:5000", wait_until="networkidle")
        expect(page.locator("#mode")).to_have_text("Local analysis")
        expect(page).to_have_title("Overview · Pears Analyzer")
        expect(page.locator(".brand")).to_have_accessible_name("Pears Analyzer overview")
        assert page.locator(".logo").evaluate("img => img.complete && img.naturalWidth > 0")
        page.screenshot(path=str(ARTIFACTS / "pears-desktop-empty.png"), full_page=True)
        checks.append("Brand, title, logo, initial state")

        page.get_by_role("button", name="Try demo", exact=True).click()
        expect(page.locator("#analysis-dashboard")).to_be_visible(timeout=30000)
        expect(page.locator("#dataset-name")).to_have_text("demo.csv")
        expect(page.locator("#metrics .metric")).not_to_have_count(0)
        expect(page.locator("#summary")).not_to_have_text("Run an analysis to generate a summary.")
        expect(page.locator("#chart")).to_be_visible()
        page.locator("#chart-metric").select_option("usage")
        expect(page.locator("#chart-title")).to_contain_text("Usage")
        page.locator("#chart-metric").select_option("cost")
        page.locator("#account-search").fill("Northstar")
        expect(page.locator("#account-usage-table tbody tr")).to_have_count(1)
        page.locator("#account-search").fill("no-matching-account")
        expect(page.locator("#account-usage-table")).to_contain_text("No accounts")
        page.locator("#account-search").fill("")
        page.screenshot(path=str(ARTIFACTS / "pears-desktop-analysis.png"), full_page=True)
        checks.append("Demo, automatic analysis, metrics, chart, summary")

        for view in ["quality", "mapping", "calculations", "chat", "overview"]:
            page.locator(f'nav [data-view="{view}"]').click()
            expect(page.locator(f'[data-page="{view}"]')).to_be_visible()
            expect(page.locator(f'nav [data-view="{view}"]')).to_have_attribute("aria-current", "page")
        checks.append("All five navigation views")

        page.locator('nav [data-view="chat"]').click()
        page.locator("#question").fill("Which region spent the most in October?")
        page.locator("#send").click()
        expect(page.locator("#conversation .message")).to_have_count(2, timeout=30000)
        expect(page.locator("#conversation .message").last).not_to_be_empty()
        checks.append("Local chat question and computed answer")

        page.locator("#model-settings").click()
        expect(page.locator("#settings-dialog")).to_be_visible()
        expect(page.locator("#saved-model")).to_be_enabled()
        page.locator("#provider").select_option("compatible")
        expect(page.locator("#endpoint")).to_be_visible()
        page.locator("#provider").select_option("openai")
        expect(page.locator("#endpoint")).to_be_hidden()
        page.get_by_role("button", name="Close model settings").click()
        expect(page.locator("#settings-dialog")).to_be_hidden()
        checks.append("Settings dialog and provider-specific controls")

        page.locator("#file").set_input_files({"name": "invalid.txt", "mimeType": "text/plain", "buffer": b"invalid"})
        expect(page.locator("#notice.error")).to_contain_text("CSV")
        expect(page.locator("#dataset-name")).to_have_text("demo.csv")
        expect(page.locator("#run")).to_be_enabled()
        checks.append("Rejected upload preserves dataset and restores controls")

        page.locator("#file").set_input_files(str(ROOT / "demo.csv"))
        expect(page.locator("#run")).to_be_enabled()
        expect(page.locator("#analysis-dashboard")).to_be_hidden()
        page.locator("#run").click()
        expect(page.locator("#analysis-dashboard")).to_be_visible(timeout=30000)
        expect(page.locator("#notice.error")).to_have_count(0)
        checks.append("CSV upload, report reset, explicit analysis, error recovery")

        for width in [375, 620, 768, 1150, 1440]:
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Overflow at {width}px"
            assert page.locator(".brand").bounding_box()["width"] > 0
            if width == 375:
                page.screenshot(path=str(ARTIFACTS / "pears-mobile-analysis.png"), full_page=True)
        checks.append("No page overflow at five mobile, tablet, and desktop widths")

        page.goto("http://127.0.0.1:5000/#mapping", wait_until="networkidle")
        expect(page.locator('[data-page="mapping"]')).to_be_visible()
        page.get_by_role("button", name="Model settings", exact=True).click()
        expect(page.locator("#saved-model")).to_be_enabled()
        page.keyboard.press("Escape")
        expect(page.locator("#settings-dialog")).to_be_hidden()
        checks.append("Direct navigation and keyboard dialog dismissal")
        page.locator("#file").set_input_files({
            "name": "no-usable-rows.csv", "mimeType": "text/csv",
            "buffer": b"Date,GPU_Hours\n2026-01-01,\n,10\n",
        })
        expect(page.locator("#run")).to_be_enabled()
        page.locator("#run").click()
        expect(page.locator("#summary")).to_contain_text("No usable rows", timeout=30000)
        expect(page.locator("#chart")).to_be_hidden()
        expect(page.locator("#notice.error")).to_have_count(0)
        checks.append("All rows excluded: clear explanation and no misleading chart")
        page.route("**/api/upload", lambda route: route.abort("failed"))
        page.locator("#file").set_input_files(str(ROOT / "demo.csv"))
        expect(page.locator("#notice.error")).to_be_visible()
        expect(page.locator("#run")).to_be_enabled()
        page.unroute("**/api/upload")
        page.locator("#file").set_input_files(str(ROOT / "demo.csv"))
        expect(page.locator("#dataset-name")).to_have_text("demo.csv")
        expect(page.locator("#run")).to_be_enabled()
        page.locator("#run").click()
        expect(page.locator("#analysis-dashboard")).to_be_visible(timeout=30000)
        checks.append("Network failure restores controls and subsequent upload succeeds")
        assert not errors, errors
        checks.append("No uncaught browser JavaScript errors")
        browser.close()
    report = {"passed": len(checks), "checks": checks, "browser_errors": errors}
    (ARTIFACTS / "browser-review.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
