import json
import re
import requests
from typing import Dict, Any, List

try:
    from playwright.sync_api import sync_playwright  # type: ignore
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False


class WebResearchTool:
    DUCKDUCKGO_SEARCH = "https://api.duckduckgo.com/"

    def fetch_url(self, url: str, timeout: int = 15, use_playwright: bool = False) -> Dict[str, Any]:
        if not url.startswith("http"):
            url = f"https://{url}"

        if use_playwright and PLAYWRIGHT_AVAILABLE:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, timeout=timeout * 1000)
                    content = page.content()
                    browser.close()
                    return {"url": url, "status_code": 200, "summary": self._summarize_html(content)}
            except Exception as exc:
                # Fall back to requests on any Playwright error
                return {"url": url, "error": f"playwright_error: {exc}", "summary": "Unable to fetch URL via Playwright."}

        try:
            response = requests.get(url, timeout=timeout, headers={"User-Agent": "Orix-Agent/1.0"})
            response.raise_for_status()
            return {"url": url, "status_code": response.status_code, "summary": self._summarize_html(response.text)}
        except Exception as exc:
            return {"url": url, "error": str(exc), "summary": "Unable to fetch URL."}

    def search_query(self, query: str, timeout: int = 15) -> Dict[str, Any]:
        try:
            response = requests.get(
                self.DUCKDUCKGO_SEARCH,
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
                timeout=timeout,
                headers={"User-Agent": "Orix-Agent/1.0"},
            )
            response.raise_for_status()
            data = response.json()
            return {
                "query": query,
                "abstract": data.get("AbstractText", ""),
                "related": [item.get("Text") for item in data.get("RelatedTopics", []) if isinstance(item, dict) and item.get("Text")],
            }
        except Exception as exc:
            return {"query": query, "error": str(exc), "abstract": ""}

    def _summarize_html(self, html: str) -> str:
        title = self._extract_tag(html, "title")
        paragraphs = self._extract_paragraphs(html, max_paragraphs=3)
        summary = title + "\n" + "\n".join(paragraphs)
        return summary.strip()

    def _extract_tag(self, html: str, tag: str) -> str:
        pattern = fr"<\s*{tag}[^>]*>(.*?)<\s*/\s*{tag}>"
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_paragraphs(self, html: str, max_paragraphs: int = 3) -> List[str]:
        paragraphs = re.findall(r"<p[^>]*>(.*?)<\s*/\s*p>", html, flags=re.IGNORECASE | re.DOTALL)
        cleaned = [re.sub(r"<[^>]+>", "", p).strip() for p in paragraphs]
        return [p for p in cleaned if p][:max_paragraphs]
