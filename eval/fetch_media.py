"""Re-fetch eval/demo media from the Pexels page URLs in demo/SOURCES.md.

Binaries are NOT stored in git (see .gitignore: demo/footage/, demo/photos/).
Run: cd eval && ../.venv/bin/python fetch_media.py [dest-root]
Defaults to <repo>/demo so footage lands at demo/footage/... and
demo/photos/... exactly as SOURCES.md catalogues them.

Each entry resolves its Pexels page in HTML, picks the direct file whose
URL carries the asset id (largest variant available), and downloads it.
Already-present files with nonzero size are skipped. Prints one line per
asset: OK / SKIP / FAIL. Exit 1 if any asset failed.
"""
from __future__ import annotations

import os
import re
import sys

import httpx

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"}

# (pexels page URL, repo-relative dest path)
ASSETS: list[tuple[str, str]] = [
    # flagship factory
    ("https://www.pexels.com/video/warehouse-operations-with-forklift-and-workers-32243654/",
     "demo/footage/factory/forklift-workers-warehouse_32243654.mp4"),
    ("https://www.pexels.com/video/man-driving-forklift-in-warehouse-13422070/",
     "demo/footage/factory/forklift-driving_13422070.mp4"),
    ("https://www.pexels.com/video/man-at-work-wearing-his-helmet-5100046/",
     "demo/footage/factory/worker-helmet_5100046.mp4"),
    ("https://www.pexels.com/video/man-using-machinery-in-factory-9737949/",
     "demo/footage/factory/worker-machinery_9737949.mp4"),
    ("https://www.pexels.com/video/textile-factory-worker-operating-machine-31007049/",
     "demo/footage/factory/worker-textile-machine_31007049.mp4"),
    # construction
    ("https://www.pexels.com/video/construction-worker-on-scaffolding-building-exterior-32228166/",
     "demo/footage/construction/worker-scaffolding_32228166.mp4"),
    ("https://www.pexels.com/video/construction-workers-on-an-elevated-platform-32244799/",
     "demo/footage/construction/workers-elevated-platform_32244799.mp4"),
    ("https://www.pexels.com/video/a-group-of-men-in-orange-vests-and-hard-hats-working-on-a-construction-site-19832500/",
     "demo/footage/construction/crew-vests-hardhats_19832500.mp4"),
    ("https://www.pexels.com/video/a-construction-worker-putting-on-goggles-8963855/",
     "demo/footage/construction/worker-goggles_8963855.mp4"),
    # farm
    ("https://www.pexels.com/video/irrigating-a-vine-yard-using-water-spray-8467118/",
     "demo/footage/farm/vineyard-irrigation-spray_8467118.mp4"),
    ("https://www.pexels.com/video/modern-tractor-spraying-in-vast-crop-field-36768458/",
     "demo/footage/farm/tractor-spraying_36768458.mp4"),
    ("https://www.pexels.com/video/a-man-choosing-vegetable-plants-inside-a-greenhouse-3191934/",
     "demo/footage/farm/greenhouse-worker_3191934.mp4"),
    ("https://www.pexels.com/video/drone-footage-of-irrigation-on-farmland-8357855/",
     "demo/footage/farm/irrigation-aerial_8357855.mp4"),
    # round-2 violations
    ("https://www.pexels.com/video/man-painting-facade-on-ladder-13372330/",
     "demo/footage/violations/man-ladder-facade_13372330.mp4"),
    ("https://www.pexels.com/video/a-man-using-a-grinder-6046356/",
     "demo/footage/violations/man-using-grinder_6046356.mp4"),
    ("https://www.pexels.com/video/angle-grinder-sparks-6046357/",
     "demo/footage/violations/angle-grinder-sparks_6046357.mp4"),
    ("https://www.pexels.com/video/man-working-at-welding-in-factory-10641848/",
     "demo/footage/violations/man-welding-factory_10641848.mp4"),
    ("https://www.pexels.com/video/a-man-welding-a-metal-sheet-at-a-workshop-14314931/",
     "demo/footage/violations/man-welding-workshop_14314931.mp4"),
    ("https://www.pexels.com/video/industrial-worker-descends-for-maintenance-40195931/",
     "demo/footage/violations/worker-descends-maintenance_40195931.mp4"),
    # round-2 photos
    ("https://www.pexels.com/photo/industrial-worker-grinding-metal-with-sparks-36003964/",
     "demo/photos/worker-grinding-sparks_36003964.jpg"),
    ("https://www.pexels.com/photo/construction-workers-on-a-building-site-12314551/",
     "demo/photos/construction-workers-site_12314551.jpg"),
    ("https://www.pexels.com/photo/a-person-using-a-grinder-12303734/",
     "demo/photos/person-grinder_12303734.jpg"),
    ("https://www.pexels.com/photo/cut-off-saw-cutting-metal-with-sparks-1145434/",
     "demo/photos/cutoff-saw-sparks_1145434.jpg"),
    ("https://www.pexels.com/photo/construction-workers-installing-reinforcement-bars-at-site-32141074/",
     "demo/photos/workers-rebar_32141074.jpg"),
    ("https://www.pexels.com/photo/a-welder-in-blue-welding-in-a-dark-room-27630177/",
     "demo/photos/welder-dark-room_27630177.jpg"),
    ("https://www.pexels.com/photo/welder-at-work-in-industrial-setting-outdoors-36227261/",
     "demo/photos/welder-outdoors_36227261.jpg"),
    ("https://www.pexels.com/photo/man-wearing-brown-glove-and-a-mask-3678228/",
     "demo/photos/worker-glove-mask_3678228.jpg"),
    ("https://www.pexels.com/photo/construction-worker-climbing-ladder-outdoors-38510725/",
     "demo/photos/worker-climbing-ladder_38510725.jpg"),
    ("https://www.pexels.com/photo/man-standing-on-the-ladder-in-a-yard-fixing-a-roof-on-a-house-19769643/",
     "demo/photos/man-ladder-roof_19769643.jpg"),
]


def asset_id(dest: str) -> str:
    return re.search(r"_(\d+)\.(mp4|jpg)$", dest).group(1)


def pick_file_url(page_html: str, aid: str, want_video: bool) -> str | None:
    if want_video:
        cands = re.findall(r"https://videos\.pexels\.com/video-files/[^\s\"']+\.mp4", page_html)
    else:
        cands = re.findall(r"https://images\.pexels\.com/photos/\d+/[^\s\"']+\.(?:jpe?g)", page_html)
    mine = [u.replace("\\u0026", "&") for u in cands if aid in u]
    if not mine:
        return None

    def pixels(u: str) -> int:
        m = re.search(r"(\d+)_(\d+)_\d+fps", u)
        if m:
            return int(m.group(1)) * int(m.group(2))
        m = re.search(r"[?&]w=(\d+)", u)
        return int(m.group(1)) if m else 0

    return sorted(set(mine), key=pixels)[-1]


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..")
    failures: list[str] = []
    with httpx.Client(timeout=60, follow_redirects=True, headers=UA) as client:
        for page_url, dest in ASSETS:
            local = os.path.join(root, dest)
            if os.path.exists(local) and os.path.getsize(local) > 0:
                print(f"SKIP {dest}")
                continue
            try:
                page = client.get(page_url)
                page.raise_for_status()
                want_video = dest.endswith(".mp4")
                file_url = pick_file_url(page.text, asset_id(dest), want_video)
                if not file_url:
                    print(f"FAIL {dest} (no direct file link on page)")
                    failures.append(dest)
                    continue
                os.makedirs(os.path.dirname(local), exist_ok=True)
                with client.stream("GET", file_url) as dl:
                    dl.raise_for_status()
                    with open(local, "wb") as f:
                        for chunk in dl.iter_bytes(1 << 20):
                            f.write(chunk)
                print(f"OK {dest} ({os.path.getsize(local)//1024} KB)")
            except Exception as exc:
                print(f"FAIL {dest} ({exc})")
                failures.append(dest)
    if failures:
        print(f"{len(failures)} asset(s) failed:")
        for d in failures:
            print("  " + d)
        return 1
    print(f"all {len(ASSETS)} assets present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
