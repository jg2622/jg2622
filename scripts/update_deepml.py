import base64
import math
import re
from pathlib import Path

from playwright.sync_api import sync_playwright


PROFILE_URL = "https://www.deep-ml.com/profile/X82iZV216RUSAObiUGdusCXLMR42"

OUTPUT_PATH = Path("assets/deepml-stats.svg")
LOGO_PATH = Path("assets/deepml-logo.png")


def get_deepml_stats():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            viewport={"width": 1400, "height": 1200}
        )

        page.goto(
            PROFILE_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        # 给 Deep-ML 的 JavaScript 一点时间加载统计数据
        page.wait_for_timeout(7000)

        body_text = page.locator("body").inner_text()

        browser.close()

    lines = [
        line.strip()
        for line in body_text.splitlines()
        if line.strip()
    ]

    # 找到 "BY DIFFICULTY" / "By difficulty" 区域
    difficulty_start = 0

    for i, line in enumerate(lines):
        if "difficulty" in line.lower():
            difficulty_start = i
            break

    def find_count(label):
        label_index = None

        for i in range(difficulty_start, len(lines)):
            if lines[i].lower() == label.lower():
                label_index = i
                break

        if label_index is None:
            raise RuntimeError(
                f"Could not find {label} in Deep-ML page."
            )

        # label 后面第一个纯数字就是做题数
        for line in lines[label_index + 1 : label_index + 8]:
            cleaned = line.replace(",", "")

            if re.fullmatch(r"\d+", cleaned):
                return int(cleaned)

        raise RuntimeError(
            f"Could not find count for {label}."
        )

    easy = find_count("Easy")
    medium = find_count("Medium")
    hard = find_count("Hard")

    return easy, medium, hard


def encode_logo():
    if not LOGO_PATH.exists():
        return ""

    encoded = base64.b64encode(
        LOGO_PATH.read_bytes()
    ).decode("utf-8")

    return f"data:image/png;base64,{encoded}"


def make_ring_segments(easy, medium, hard):
    total = easy + medium + hard

    if total == 0:
        return ""

    radius = 43
    circumference = 2 * math.pi * radius

    values = [
        (easy, "#22c55e"),
        (medium, "#f4b400"),
        (hard, "#ef4444"),
    ]

    svg = []
    offset = 0

    for value, color in values:
        if value == 0:
            continue

        length = circumference * value / total

        svg.append(
            f"""
            <circle
                cx="100"
                cy="112"
                r="{radius}"
                fill="none"
                stroke="{color}"
                stroke-width="7"
                stroke-linecap="round"
                stroke-dasharray="{length:.2f} {circumference - length:.2f}"
                stroke-dashoffset="{-offset:.2f}"
                transform="rotate(-90 100 112)"
            />
            """
        )

        offset += length

    return "\n".join(svg)


def make_svg(easy, medium, hard):
    total = easy + medium + hard

    logo = encode_logo()

    if total > 0:
        easy_pct = easy / total
        medium_pct = medium / total
        hard_pct = hard / total
    else:
        easy_pct = medium_pct = hard_pct = 0

    bar_width = 250

    easy_width = bar_width * easy_pct
    medium_width = bar_width * medium_pct
    hard_width = bar_width * hard_pct

    ring_segments = make_ring_segments(
        easy,
        medium,
        hard,
    )

    logo_svg = ""

    if logo:
        logo_svg = f"""
        <image
            href="{logo}"
            x="27"
            y="20"
            width="36"
            height="36"
            preserveAspectRatio="xMidYMid meet"
        />
        """

    return f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="500"
    height="190"
    viewBox="0 0 500 190"
    role="img"
    aria-label="Deep-ML Stats"
>

    <rect
        x="0.5"
        y="0.5"
        width="499"
        height="189"
        rx="12"
        fill="#ffffff"
        stroke="#d0d7de"
    />

    {logo_svg}

    <text
        x="74"
        y="44"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
        font-size="21"
        font-weight="600"
        fill="#24292f"
    >
        Deep-ML
    </text>

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

    <circle
        cx="100"
        cy="112"
        r="43"
        fill="none"
        stroke="#eaeef2"
        stroke-width="7"
    />

    {ring_segments}

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

    <!-- EASY -->

    <circle cx="185" cy="77" r="5" fill="#22c55e"/>

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
        x2="{200 + easy_width}"
        y2="91"
        stroke="#22c55e"
        stroke-width="5"
        stroke-linecap="round"
    />

    <!-- MEDIUM -->

    <circle cx="185" cy="112" r="5" fill="#f4b400"/>

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
        x2="{200 + medium_width}"
        y2="126"
        stroke="#f4b400"
        stroke-width="5"
        stroke-linecap="round"
    />

    <!-- HARD -->

    <circle cx="185" cy="147" r="5" fill="#ef4444"/>

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
        x2="{200 + hard_width}"
        y2="161"
        stroke="#ef4444"
        stroke-width="5"
        stroke-linecap="round"
    />

</svg>
""".strip()


def main():
    easy, medium, hard = get_deepml_stats()

    print(
        f"Deep-ML stats: "
        f"Easy={easy}, "
        f"Medium={medium}, "
        f"Hard={hard}"
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

    print(
        f"Updated {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
