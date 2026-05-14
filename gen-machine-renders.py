#!/usr/bin/env python3
"""Generate 5 marketing renders of the REAL Omni Elite, re-wrapped black with
Sm0kBot branding, in different upscale settings. Feeds the real machine photo +
the locked logo as image inputs so the machine form stays faithful."""
import base64, json, subprocess, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
MACHINE = HERE / "images" / "IMG_6888.jpeg"      # real Omni Elite
LOGO = HERE / "images" / "logo-lockup.png"        # locked Sm0kBot lockup
OUT_DIR = HERE / "images" / "machine-renders"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROJECT = "babycakes3126"
MODEL = "gemini-2.5-flash-image"
ENDPOINT = (f"https://aiplatform.googleapis.com/v1/projects/{PROJECT}"
            f"/locations/global/publishers/google/models/{MODEL}:generateContent")

CORE = (
    "You are given two images. IMAGE 1 is a real vending machine — the 'Omni Elite.' "
    "IMAGE 2 is the Sm0kBot brand logo.\n\n"
    "Create a photorealistic commercial marketing photograph of THIS EXACT vending "
    "machine. You MUST preserve its precise structure and proportions from IMAGE 1: "
    "the faceted triangular-panel exterior geometry, the large left-side glass product "
    "display window, the curved header panel across the top, the right-side control "
    "column (vertical screen, payment terminal with keypad, card reader, scanner "
    "device), the product pickup door at the lower left, the boxy upright footprint. "
    "Do NOT change the machine's shape, layout, or proportions.\n\n"
    "THE ONLY CHANGES:\n"
    "1) Re-wrap the entire exterior in a sleek glossy/matte BLACK vinyl wrap instead of "
    "white. Keep the faceted panel geometry, now black with crisp electric-blue edge "
    "lighting accents.\n"
    "2) Apply the Sm0kBot branding from IMAGE 2 onto the machine — the Sm0kBot chip "
    "icon as the primary mark on the header panel, with the wordmark below it. The "
    "brand name is spelled exactly Sm0kBot (capital S, lowercase m, the digit ZERO, "
    "lowercase k, capital B, lowercase o, lowercase t) — do not misspell it. Keep "
    "branding clean and premium.\n"
    "3) Place the machine in {setting}.\n\n"
    "Style: photorealistic professional product photography, the machine is the sharp-"
    "focus hero of the shot, full machine visible head to toe, tall vertical framing. "
    "{lighting}. No people interacting with it. No text watermarks."
)

SETTINGS = [
    ("an-upscale-hotel-lobby",
     "an upscale modern hotel lobby with marble floors, elegant minimalist decor, a reception desk softly blurred in the background",
     "soft warm interior lighting with gentle reflections on the black wrap"),
    ("a-dark-cocktail-bar",
     "a sophisticated dark cocktail bar at night, backlit liquor bottle shelves glowing behind the bar",
     "moody low-key lighting with amber and neon-blue accents, dramatic shadows"),
    ("a-premium-cigar-lounge",
     "a premium cigar lounge with rich leather armchairs, dark wood paneling, and warm low lighting",
     "warm dim intimate lighting, cozy amber glow, the blue machine accents popping against the warm room"),
    ("a-rooftop-lounge-at-dusk",
     "a rooftop lounge at dusk with a city skyline in the background, string lights and modern outdoor seating",
     "blue-hour dusk light with warm string-light accents"),
    ("a-boutique-hotel-corridor",
     "a sleek boutique hotel corridor near the elevators, minimalist modern design with polished concrete and glass",
     "cool clean architectural lighting with electric-blue accent lighting"),
]


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def generate(slug: str, setting: str, lighting: str, machine_b64: str, logo_b64: str) -> bool:
    prompt = CORE.format(setting=setting, lighting=lighting)
    body = json.dumps({
        "contents": [{
            "role": "user",
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": machine_b64}},
                {"inline_data": {"mime_type": "image/png", "data": logo_b64}},
                {"text": prompt},
            ],
        }],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }).encode()
    for attempt in (1, 2):
        try:
            token = subprocess.check_output(
                ["gcloud", "auth", "print-access-token"], text=True, timeout=30).strip()
            req = urllib.request.Request(
                ENDPOINT, data=body,
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "application/json"}, method="POST")
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode())
            for cand in data.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    inline = part.get("inlineData") or part.get("inline_data")
                    if inline and inline.get("data"):
                        out = OUT_DIR / f"omni-elite-black__{slug}.png"
                        out.write_bytes(base64.b64decode(inline["data"]))
                        print(f"  OK  {out.name}  ({out.stat().st_size//1024} KB, "
                              f"{time.time()-t0:.1f}s, attempt {attempt})")
                        return True
            print(f"  WARN {slug}: no image in response (attempt {attempt})")
        except Exception as e:
            print(f"  WARN {slug}: attempt {attempt} failed: {e}")
            if attempt == 1:
                time.sleep(5)
    print(f"  FAIL {slug}")
    return False


def main():
    print(f"machine: {MACHINE.name}  logo: {LOGO.name}  -> {OUT_DIR}")
    machine_b64 = b64(MACHINE)
    logo_b64 = b64(LOGO)
    ok = 0
    for slug, setting, lighting in SETTINGS:
        print(f"[{slug}]")
        if generate(slug, setting, lighting, machine_b64, logo_b64):
            ok += 1
    print(f"\nDONE: {ok}/{len(SETTINGS)} renders generated in {OUT_DIR}")


if __name__ == "__main__":
    main()
