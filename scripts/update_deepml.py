import base64
import math
import re
from pathlib import Path

from playwright.sync_api import sync_playwright


# ============================================================
# Configuration
# ============================================================

PROFILE_URL = (
    "https://www.deep-ml.com/profile/"
    "X82iZV216RUSAObiUGdusCXLMR42"
)

OUTPUT_PATH = Path("assets/deepml-stats.svg")
LOGO_PATH = Path("assets/deepml-logo.png")


# ============================================================
# Fetch Deep-ML stats
# ============================================================

def get_deepml_stats():
    """
    Open the Deep-ML profile with Playwright and extract
    Easy / Medium / Hard solved counts.

    Deep-ML currently exposes the difficulty statistics inside
    SVG <title> elements, for example:

        Easy · 4 · 80%
        Medium · 1 · 20%
        Hard · 0 · 0%
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            viewport={
                "width": 1400,
                "height": 1200,
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/127.0.0.0 Safari/537.36"
            ),
        )

        max_attempts = 3

        try:
            for attempt in range(1, max_attempts + 1):
                print(
                    f"Attempt {attempt}/{max_attempts} "
                    "to load Deep-ML stats..."
                )

                try:
                    page.goto(
                        PROFILE_URL,
                        wait_until="domcontentloaded",
                        timeout=60000,
                    )

                    # Wait until Deep-ML has rendered all three
                    # difficulty statistics into SVG <title> tags.
                    #
                    # IMPORTANT:
                    # We do NOT wait for text=Easy to become visible,
                    # because these <title> elements are intentionally
                    # hidden SVG metadata.
                    page.wait_for_function(
                        r"""
                        () => {
                            const titles = Array
                                .from(document.querySelectorAll("title"))
                                .map(el =>
                                    (el.textContent || "").trim()
                                );

                            const hasEasy = titles.some(
                                text =>
                                    /^Easy\s*[·•]\s*\d+/.test(text)
                            );

                            const hasMedium = titles.some(
                                text =>
                                    /^Medium\s*[·•]\s*\d+/.test(text)
                            );

                            const hasHard = titles.some(
                                text =>
                                    /^Hard\s*[·•]\s*\d+/.test(text)
                            );

                            return (
                                hasEasy &&
                                hasMedium &&
                                hasHard
                            );
                        }
                        """,
                        timeout=30000,
                    )

                    titles = page.locator(
                        "title"
                    ).all_text_contents()

                    # Show relevant data in GitHub Actions logs.
                    relevant_titles = [
                        title.strip()
                        for title in titles
                        if title.strip().startswith(
                            (
                                "Easy",
                                "Medium",
                                "Hard",
                            )
                        )
                    ]

                    print("Deep-ML difficulty data found:")

                    for title in relevant_titles:
                        print(f"  {title}")

                    def extract_count(label):
                        """
                        Extract the solved count from strings such as:
                        Easy · 4 · 80%
                        """

                        pattern = re.compile(
                            rf"^{re.escape(label)}"
                            rf"\s*[·•]\s*(\d+)"
                        )

                        for title in titles:
                            cleaned = title.strip()
                            match = pattern.search(cleaned)

                            if match:
                                return int(match.group(1))

                        raise RuntimeError(
                            f"Could not extract {label} count "
                            "from Deep-ML page."
                        )

                    easy = extract_count("Easy")
                    medium = extract_count("Medium")
                    hard = extract_count("Hard")

                    print(
                        "Successfully extracted Deep-ML stats:"
                    )
                    print(f"  Easy   = {easy}")
                    print(f"  Medium = {medium}")
                    print(f"  Hard   = {hard}")
                    print(
                        f"  Total  = "
                        f"{easy + medium + hard}"
                    )

                    return easy, medium, hard

                except Exception as error:
                    print(
                        f"Attempt {attempt} failed:"
                    )
                    print(error)

                    # Print available matching titles to make
                    # future debugging easier.
                    try:
                        titles = page.locator(
                            "title"
                        ).all_text_contents()

                        possible = [
                            title.strip()
                            for title in titles
                            if any(
                                word in title
                                for word in (
                                    "Easy",
                                    "Medium",
                                    "Hard",
                                )
                            )
                        ]

                        if possible:
                            print(
                                "Relevant <title> elements "
                                "currently on page:"
                            )

                            for title in possible:
                                print(f"  {title}")

                    except Exception:
                        pass

                    if attempt < max_attempts:
                        print(
                            "Waiting 5 seconds before retry..."
                        )

                        page.wait_for_timeout(5000)

            raise RuntimeError(
                "Deep-ML stats could not be loaded "
                "after multiple attempts."
            )

        finally:
            browser.close()


# ============================================================
# Logo
# ============================================================

def encode_logo():
    """
    Embed the Deep-ML logo directly into the SVG as base64.

    This is more reliable on GitHub than referencing a relative
    PNG path from inside an SVG.
    """

    if not LOGO_PATH.exists():
        print(
            f"Warning: {LOGO_PATH} not found. "
            "Generating card without logo."
        )
        return ""

    encoded = base64.b64encode(
        LOGO_PATH.read_bytes()
    ).decode("utf-8")

    return (
        "data:image/png;base64,"
        + encoded
    )


# ============================================================
# Circular chart
# ============================================================

def make_ring_segments(
    easy,
    medium,
    hard,
):
    total = (
        easy
        + medium
        + hard
    )

    if total == 0:
        return ""

    radius = 43
    circumference = (
        2
        * math.pi
        * radius
    )

    values = [
        (
            easy,
            "#22c55e",
        ),
        (
            medium,
            "#f4b400",
        ),
        (
            hard,
            "#ef4444",
        ),
    ]

    segments = []
    offset = 0.0

    for value, color in values:
        if value <= 0:
            continue

        length = (
            circumference
            * value
            / total
        )

        remaining = (
            circumference
            - length
        )

        segments.append(
            f"""
    <circle
        cx="100"
        cy="112"
        r="{radius}"
        fill="none"
        stroke="{color}"
        stroke-width="7"
        stroke-linecap="round"
        stroke-dasharray="{length:.2f} {remaining:.2f}"
        stroke-dashoffset="{-offset:.2f}"
        transform="rotate(-90 100 112)"
    />
            """.strip()
        )

        offset += length

    return "\n".join(
        segments
    )


# ============================================================
# SVG generation
# ============================================================

def make_svg(
    easy,
    medium,
    hard,
):
    total = (
        easy
        + medium
        + hard
    )

    # Difficulty percentages among solved problems.
    if total > 0:
        easy_pct = (
            easy
            / total
        )

        medium_pct = (
            medium
            / total
        )

        hard_pct = (
            hard
            / total
        )

    else:
        easy_pct = 0
        medium_pct = 0
        hard_pct = 0

    bar_width = 250

    easy_width = (
        bar_width
        * easy_pct
    )

    medium_width = (
        bar_width
        * medium_pct
    )

    hard_width = (
        bar_width
        * hard_pct
    )

    ring_segments = (
        make_ring_segments(
            easy,
            medium,
            hard,
        )
    )

    logo_data = encode_logo()

    if logo_data:
        logo_svg = f"""
    <image
        href="{logo_data}"
        x="27"
        y="18"
        width="38"
        height="38"
        preserveAspectRatio="xMidYMid meet"
    />
        """
    else:
        logo_svg = ""

    svg = f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="500"
    height="190"
    viewBox="0 0 500 190"
    role="img"
    aria-label="Deep-ML Stats"
>

    <!-- Background -->

    <rect
        x="0.5"
        y="0.5"
        width="499"
        height="189"
        rx="12"
        fill="#ffffff"
        stroke="#d0d7de"
    />

    <!-- Deep-ML Logo -->

    {logo_svg}

    <!-- Title -->

    <text
        x="74"
        y="43"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
        font-size="21"
        font-weight="600"
        fill="#24292f"
    >
        Deep-ML
    </text>

    <!-- Total solved -->

    <text
        x="455"
        y="43"
        text-anchor="end"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
        font-size="18"
        font-weight="600"
        fill="#24292f"
    >
        {total} solved
    </text>

    <!-- Circle background -->

    <circle
        cx="100"
        cy="112"
        r="43"
        fill="none"
        stroke="#eaeef2"
        stroke-width="7"
    />

    <!-- Circle difficulty distribution -->

    {ring_segments}

    <!-- Number inside circle -->

    <text
        x="100"
        y="110"
        text-anchor="middle"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
        font-size="28"
        font-weight="600"
        fill="#24292f"
    >
        {total}
    </text>

    <text
        x="100"
        y="130"
        text-anchor="middle"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
        font-size="12"
        fill="#57606a"
    >
        Solved
    </text>


    <!-- ================================================= -->
    <!-- EASY -->
    <!-- ================================================= -->

    <circle
        cx="185"
        cy="77"
        r="5"
        fill="#22c55e"
    />

    <text
        x="200"
        y="82"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
        font-size="16"
        font-weight="600"
        fill="#24292f"
    >
        Easy
    </text>

    <text
        x="450"
        y="82"
        text-anchor="end"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
        font-size="16"
        font-weight="600"
        fill="#57606a"
    >
        {easy}
    </text>

    <line
        x1="200"
        y1="91"
        x2="450"
        y2="91"
        stroke="#eaeef2"
        stroke-width="5"
        stroke-linecap="round"
    />

    <line
        x1="200"
        y1="91"
        x2="{200 + easy_width:.2f}"
        y2="91"
        stroke="#22c55e"
        stroke-width="5"
        stroke-linecap="round"
    />


    <!-- ================================================= -->
    <!-- MEDIUM -->
    <!-- ================================================= -->

    <circle
        cx="185"
        cy="112"
        r="5"
        fill="#f4b400"
    />

    <text
        x="200"
        y="117"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
        font-size="16"
        font-weight="600"
        fill="#24292f"
    >
        Medium
    </text>

    <text
        x="450"
        y="117"
        text-anchor="end"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
        font-size="16"
        font-weight="600"
        fill="#57606a"
    >
        {medium}
    </text>

    <line
        x1="200"
        y1="126"
        x2="450"
        y2="126"
        stroke="#eaeef2"
        stroke-width="5"
        stroke-linecap="round"
    />

    <line
        x1="200"
        y1="126"
        x2="{200 + medium_width:.2f}"
        y2="126"
        stroke="#f4b400"
        stroke-width="5"
        stroke-linecap="round"
    />


    <!-- ================================================= -->
    <!-- HARD -->
    <!-- ================================================= -->

    <circle
        cx="185"
        cy="147"
        r="5"
        fill="#ef4444"
    />

    <text
        x="200"
        y="152"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
        font-size="16"
        font-weight="600"
        fill="#24292f"
    >
        Hard
    </text>

    <text
        x="450"
        y="152"
        text-anchor="end"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
        font-size="16"
        font-weight="600"
        fill="#57606a"
    >
        {hard}
    </text>

    <line
        x1="200"
        y1="161"
        x2="450"
        y2="161"
        stroke="#eaeef2"
        stroke-width="5"
        stroke-linecap="round"
    />

    <line
        x1="200"
        y1="161"
        x2="{200 + hard_width:.2f}"
        y2="161"
        stroke="#ef4444"
        stroke-width="5"
        stroke-linecap="round"
    />

</svg>
""".strip()

    return svg


# ============================================================
# Main
# ============================================================

def main():
    print(
        "Fetching Deep-ML statistics..."
    )

    easy, medium, hard = (
        get_deepml_stats()
    )

    total = (
        easy
        + medium
        + hard
    )

    print()
    print(
        "Generating SVG card..."
    )

    print(
        f"Easy={easy}, "
        f"Medium={medium}, "
        f"Hard={hard}, "
        f"Total={total}"
    )

    svg = make_svg(
        easy,
        medium,
        hard,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        svg,
        encoding="utf-8",
    )

    print()
    print(
        f"Successfully updated "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
