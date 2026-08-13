import fitz

# Original model
doc = fitz.open("C:/Users/moura/OneDrive/Bureau/gestion des stagiaires/Attestation de Stage Haider BOUZAIDA PFE (1).pdf")
page = doc[0]
print("=== MODELE OFFICIEL ===")
print(f"Page: {page.rect.width:.0f}x{page.rect.height:.0f} pts")
blocks = page.get_text("dict")["blocks"]
for b in blocks:
    if "lines" in b:
        for line in b["lines"]:
            text = "".join([s["text"] for s in line["spans"]])
            if text.strip():
                bb = line["bbox"]
                font = line["spans"][0]["font"]
                size = line["spans"][0]["size"]
                print(f"  y={bb[1]:.0f} x={bb[0]:.0f} font={font} size={size:.0f} texte={text[:80]}")

# Generated PDF - need to find the latest one
import os, glob
pdfs = glob.glob("C:/Users/moura/OneDrive/Bureau/gestion des stagiaires/backend/uploads/attestations/*.pdf")
if pdfs:
    latest = max(pdfs, key=os.path.getctime)
    doc2 = fitz.open(latest)
    page2 = doc2[0]
    print(f"\n=== GENEREE ({os.path.basename(latest)}) ===")
    print(f"Page: {page2.rect.width:.0f}x{page2.rect.height:.0f} pts")
    print(f"Images: {len(page2.get_images())}")
    blocks2 = page2.get_text("dict")["blocks"]
    for b in blocks2:
        if "lines" in b:
            for line in b["lines"]:
                text = "".join([s["text"] for s in line["spans"]])
                if text.strip():
                    bb = line["bbox"]
                    print(f"  y={bb[1]:.0f} x={bb[0]:.0f} texte={text[:80]}")
        else:
            print(f"  [IMAGE] x={b['bbox'][0]:.0f} y={b['bbox'][1]:.0f}")
