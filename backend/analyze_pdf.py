import fitz

doc = fitz.open("C:/Users/moura/OneDrive/Bureau/gestion des stagiaires/Attestation de Stage Haider BOUZAIDA PFE (1).pdf")
page = doc[0]
print(f"Page size: {page.rect.width:.0f} x {page.rect.height:.0f} pts")

blocks = page.get_text("dict")["blocks"]
for b in blocks:
    if "lines" in b:
        for line in b["lines"]:
            text = "".join([s["text"] for s in line["spans"]])
            if not text.strip():
                continue
            font = line["spans"][0]["font"]
            size = line["spans"][0]["size"]
            color = line["spans"][0]["color"]
            bbox = line["bbox"]
            print(f"font={font}, size={size:.1f}, color=#{int(color):06x}, x={bbox[0]:.0f}, y={bbox[1]:.0f}, w={bbox[2]-bbox[0]:.0f}, text={text}")

print("\n--- Images ---")
for b in blocks:
    if "image" in b:
        print(f"Image at x={b['bbox'][0]:.0f}, y={b['bbox'][1]:.0f}, size={b['bbox'][2]-b['bbox'][0]:.0f}x{b['bbox'][3]-b['bbox'][1]:.0f}")
