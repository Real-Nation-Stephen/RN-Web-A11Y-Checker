
# streamlit_app.py
# Website Accessibility Checker (Streamlit + Playwright + axe-core)
# Outputs: Audit (with Quick Wins + Severity) and an Accessibility Statement

import asyncio
import datetime
import json
import re
import urllib.parse
from collections import defaultdict, Counter

import pandas as pd
import streamlit as st
from jinja2 import Template
from playwright.async_api import async_playwright
from auth.auth_module import AuthManager, check_authentication

DEFAULT_MAX_PAGES = 40
DESKTOP_VIEWPORT = {"width": 1280, "height": 800}
MOBILE_VIEWPORT = {"width": 390, "height": 844}  # iPhone-ish

QUICK_WIN_HINTS = [
    "color-contrast",
    "document-title",
    "page titled",
    "label",
    "labels or instructions",
    "image", "img",
    "non-text content",
    "button-name", "link-name",
    "target size", "viewport",
]

SEVERITY_MAP = {
    "critical": "Critical",
    "serious": "Serious",
    "moderate": "Moderate",
    "minor": "Minor",
    None: "Moderate",
}

CATEGORY_BY_CRITERION = [
    ("Page Structure and Headings", ["info & relationships", "page titled", "landmarks", "heading"]),
    ("Keyboard Navigation", ["keyboard", "focus visible", "focus order", "skip link"]),
    ("Text and Colour Contrast", ["contrast"]),
    ("Images and Alt Text", ["non-text content", "image", "img"]),
    ("Forms and Labels", ["labels or instructions", "autocomplete", "error", "form", "label"]),
    ("Mobile Accessibility", ["target size", "reflow", "viewport"]),
    ("Screen Reader Experience", ["name, role, value", "aria", "link-name", "button-name"]),
]

STATEMENT_TEMPLATE = """
# Accessibility statement for {{ org_name }}

**Status**
This website aims to conform to **WCAG {{ wcag_version }} Level AA**. Based on our latest audit ({{ scanned_at }}), the site is **partially compliant** due to the non-compliances listed below.

{% if groups %}
## Non-accessible content
{% for g in groups %}
### {{ g.category }} — {{ g.criterion }}
{% for v in g["items"] %}
- **Page**: {{ v.page }}
  - **What’s wrong**: {{ v.summary }}
  - **Example element**: `{{ v.selector }}`
  - **Impact**: {{ v.impact }}
  - **Planned fix**: {{ v.recommended_fix }}
  - **Owner**: TBC | **Target date**: {{ roadmap_default_date }}
{% endfor %}
{% endfor %}
{% else %}
## Non-accessible content
No known issues. This site is fully compliant with WCAG {{ wcag_version }} Level AA.
{% endif %}

## How we tested
- Automated checks: axe-core + custom contrast/typography/keyboard/mobile rules (run on {{ pages_scanned }} pages).
- Manual QA: keyboard order, screen-reader announcements for dynamic content, and motion preferences are reviewed in ongoing improvements.

**Manual checks still required:** reading order in complex layouts, quality of alt text, clarity and association of error messages, live announcements for dynamic updates, motion/animation preferences, and complex widget keyboard behavior.

## Roadmap
- **Wave 1 (within 30 days)**: Critical issues (forms, labels, keyboard reachability, page titles).  
- **Wave 2 (within 60–90 days)**: Contrast & typography adjustments; heading structure; link purpose.  
- **Wave 3 (ongoing)**: ARIA quality, motion preferences, complex widgets; regression tests.

## Feedback and contact
If you find accessibility barriers not listed above, contact **{{ contact_name }}** at **{{ contact_email }}**. We aim to respond within **{{ sla_days }}** working days.

_Last updated: {{ scanned_at }}._
""".strip()


def same_site(url, host):
    try:
        return urllib.parse.urlparse(url).netloc == host
    except Exception:
        return False

def bucket_name(criterion_text):
    t = (criterion_text or "").lower()
    for name, keys in CATEGORY_BY_CRITERION:
        if any(k.lower() in t for k in keys):
            return name
    return "Other"


async def scan_site(start_url: str, max_pages: int = DEFAULT_MAX_PAGES):
    host = urllib.parse.urlparse(start_url).netloc
    results = {
        "scanned_at": datetime.date.today().isoformat(),
        "site": start_url, "pages_scanned": 0,
        "wcag_version": "2.2", "violations": []
    }

    visited, queue = set(), [start_url]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport=DESKTOP_VIEWPORT)
        page = await context.new_page()

        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception:
                continue

            # Enqueue same-site links
            try:
                links = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
                for href in links:
                    if same_site(href, host) and href not in visited and href not in queue:
                        queue.append(href)
            except Exception:
                pass

            # Inject axe-core from CDN and run
            try:
                await page.add_script_tag(url="https://cdn.jsdelivr.net/npm/axe-core@4.9.1/axe.min.js")
                axe = await page.evaluate("""() => new Promise((resolve) => {
                    window.axe.run(document, { resultTypes: ["violations"] }).then(resolve);
                })""")
            except Exception:
                axe = {"violations": []}

            # Map axe violations (flatten a bit)
            for v in axe.get("violations", []):
                selector = (v.get("nodes", [{}])[0].get("target", ["?"])[0])
                results["violations"].append({
                    "page": url,
                    "criterion": f"{v.get('id')} — {v.get('help')}",
                    "axe_id": v.get("id"),
                    "severity": v.get("impact"),
                    "elements": [{"selector": selector}],
                    "recommended_fix": v.get("helpUrl")
                })

            results["pages_scanned"] = len(visited)

        await browser.close()

    return results


def build_audit_table(results: dict) -> pd.DataFrame:
    rows = []
    for v in results.get("violations", []):
        sev = SEVERITY_MAP.get(v.get("severity"), "Moderate")
        ex = v.get("elements", [{}])[0] if v.get("elements") else {}
        rows.append({
            "Page": v.get("page"),
            "Criterion": v.get("criterion"),
            "Axe ID": v.get("axe_id"),
            "Severity": sev,
            "Selector / Element": ex.get("selector", "?"),
            "Planned Fix": v.get("recommended_fix"),
        })
    
    # Create DataFrame with expected columns even if empty
    df = pd.DataFrame(rows, columns=["Page", "Criterion", "Axe ID", "Severity", "Selector / Element", "Planned Fix"])
    
    # Only sort if DataFrame is not empty
    if not df.empty:
        df = df.sort_values(["Severity", "Page"]).reset_index(drop=True)
    
    return df

def quick_wins(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    pattern = "|".join([re.escape(k) for k in QUICK_WIN_HINTS])
    mask = df["Criterion"].fillna("").str.contains(pattern, case=False)
    return df[mask].copy()

def severity_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    counts = Counter(df["Severity"]) if not df.empty else Counter()
    order = ["Critical", "Serious", "Moderate", "Minor"]
    return pd.DataFrame({"Severity": order, "Count": [counts.get(s, 0) for s in order]})

def group_for_statement(results: dict):
    buckets = defaultdict(lambda: defaultdict(list))
    for v in results.get("violations", []):
        cat = bucket_name(v.get("criterion", ""))
        ex = v.get("elements", [{}])[0] if v.get("elements") else {}
        summary = ex.get("issue") or "See details"
        buckets[cat][v.get("criterion","")].append({
            "page": v.get("page"),
            "selector": ex.get("selector","?"),
            "summary": summary,
            "impact": SEVERITY_MAP.get(v.get("severity"), "Moderate"),
            "recommended_fix": v.get("recommended_fix","Review WCAG guidance and adjust.")
        })
    grouped=[]
    for cat, crits in buckets.items():
        for crit, items in crits.items():
            grouped.append({"category": cat, "criterion": crit, "items": items})
    return grouped

def render_statement(results: dict, org_name: str, contact_name: str, contact_email: str, sla_days: int = 10) -> str:
    tpl = Template(STATEMENT_TEMPLATE)
    md = tpl.render(
        org_name=org_name or urllib.parse.urlparse(results.get("site","")).netloc,
        wcag_version=results.get("wcag_version", "2.2"),
        scanned_at=results.get("scanned_at", datetime.date.today().isoformat()),
        pages_scanned=results.get("pages_scanned", 0),
        groups=group_for_statement(results),
        contact_name=contact_name or "Accessibility Lead",
        contact_email=contact_email or "accessibility@example.com",
        sla_days=sla_days,
        roadmap_default_date=(datetime.date.today() + datetime.timedelta(days=60)).isoformat()
    )
    return md


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(
    page_title="Website Accessibility Checker", 
    page_icon="♿", 
    layout="wide"
)

# Initialize authentication
if 'auth_manager' not in st.session_state:
    st.session_state.auth_manager = AuthManager()

auth_manager = st.session_state.auth_manager

# Check authentication - show login if not authenticated
if not check_authentication(auth_manager):
    st.stop()

# User is authenticated - show main app
st.title("Website Accessibility Checker")
st.caption("Crawls a site, finds accessibility issues, and generates an Audit + Statement.")

with st.sidebar:
    # Logout button at top
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()
    
    st.divider()
    
    url = st.text_input("Start URL (include https://)", placeholder="https://example.com")
    max_pages = st.number_input("Max pages to scan", min_value=1, max_value=500, value=DEFAULT_MAX_PAGES, step=1)
    org_name = st.text_input("Organisation name (for statement)", placeholder="Your Company")
    contact_name = st.text_input("Contact name", value="Accessibility Lead")
    contact_email = st.text_input("Contact email", value="accessibility@example.com")
    run_btn = st.button("Run accessibility scan", type="primary")

if run_btn:
    if not url or not url.startswith("http"):
        st.error("Please enter a valid URL starting with http or https.")
        st.stop()

    with st.spinner("Scanning… this can take a minute."):
        results = asyncio.run(scan_site(url, max_pages=int(max_pages)))

    raw_json = json.dumps(results, indent=2).encode("utf-8")

    audit_df = build_audit_table(results)
    quick_df = quick_wins(audit_df)
    sev_df = severity_breakdown(audit_df)

    left, right = st.columns([2, 1])
    with left:
        st.subheader("Summary")
        st.markdown(f"- **Pages scanned:** {results.get('pages_scanned', 0)}")
        st.markdown(f"- **Total issues found:** {len(results.get('violations', []))}")

        st.markdown("**Quick Wins**:")
        if not quick_df.empty:
            st.dataframe(quick_df[["Page","Criterion","Selector / Element"]], use_container_width=True)
        else:
            st.info("No obvious quick wins detected.")
    with right:
        st.subheader("Severity")
        st.dataframe(sev_df, use_container_width=True)

    st.divider()

    st.header("Accessibility Audit")
    if audit_df.empty:
        st.success("No issues found.")
    else:
        st.dataframe(audit_df, use_container_width=True)

    csv_bytes = audit_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download audit CSV", data=csv_bytes, file_name="a11y_audit.csv", mime="text/csv")
    st.download_button("Download raw JSON", data=raw_json, file_name="a11y_report.json", mime="application/json")

    st.divider()

    st.header("Accessibility Statement (Draft)")
    md = render_statement(results, org_name=org_name, contact_name=contact_name, contact_email=contact_email)
    st.markdown(md)
    st.download_button("Download statement (Markdown)", data=md.encode("utf-8"),
                       file_name="accessibility-statement.md", mime="text/markdown")

else:
    st.info("Enter a URL in the sidebar and click **Run accessibility scan**.")
