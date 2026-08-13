import os
from fpdf import FPDF
from datetime import date

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_LOGO_PATH = os.path.join(_MODULE_DIR, "..", "..", "..", "images.png")


class AttestationPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)


def pt_to_mm(pt):
    return pt / 2.835


def generer_attestation_pdf(stagiaire, numero_attestation, output_path, current_user=None):
    pdf = AttestationPDF()
    pdf.add_page()

    pdf.add_font("Calibri", "", "C:/Windows/Fonts/calibri.ttf", uni=True)
    pdf.add_font("Calibri", "B", "C:/Windows/Fonts/calibrib.ttf", uni=True)

    page_w = 210
    lm = pt_to_mm(71)

    # Logo
    logo_path = _LOGO_PATH
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.path.dirname(_LOGO_PATH), "frontend", "public", "hutchinson_logo-remove.live.png")
    if os.path.exists(logo_path):
        try:
            pdf.image(logo_path, x=lm, y=12, w=50, h=36)
        except Exception:
            pass

    # Date (original: y=74pt -> 26mm)
    today = date.today()
    date_str = f"Sousse le {today.strftime('%d/%m/%Y')}"
    pdf.set_font("Calibri", "B", 14)
    date_w = pdf.get_string_width(date_str)
    pdf.set_xy(page_w - lm - date_w, 26)
    pdf.cell(date_w, 8, date_str)

    # Titre (original: y=165pt -> 58mm)
    pdf.set_font("Calibri", "B", 16)
    pdf.set_xy(0, 58)
    pdf.cell(page_w, 10, "ATTESTATION DE STAGE", align="C")

    # Corps 1 (original: y=242pt -> 85mm)
    pdf.set_xy(lm, 85)
    pdf.set_font("Calibri", "", 12)
    pdf.write(8, "Nous soussignés, société ")
    pdf.set_font("Calibri", "B", 12)
    pdf.write(8, "HUTCHINSON TUNISIE SARL")
    pdf.set_font("Calibri", "", 12)
    pdf.write(8, ", certifions par la présente que :")

    # Nom du stagiaire (original: y=286pt -> 101mm)
    pdf.set_font("Calibri", "B", 14)
    civilite = "Mme" if stagiaire.civilite == "Mme" else "Mr"
    nom_affiche = stagiaire.nom_complet or ""
    nom_complet = f"{civilite}. {nom_affiche}" if nom_affiche else civilite
    pdf.set_xy(0, 101)
    pdf.cell(page_w, 10, nom_complet, align="C")

    # CIN (original: y=355pt -> 125mm)
    pdf.set_font("Calibri", "", 12)
    pdf.set_xy(lm, 125)
    pdf.cell(page_w - 2 * lm, 8, f"Titulaire de la CIN n° : {stagiaire.cin}")

    # Service (original: y=377pt -> 133mm)
    service = stagiaire.service or "Bureau d'études"
    pdf.set_xy(lm, 133)
    pdf.set_font("Calibri", "", 12)
    pdf.write(8, "A poursuivi un stage au sein de notre société dans le service ")
    pdf.set_font("Calibri", "B", 12)
    pdf.write(8, service)
    pdf.set_font("Calibri", "", 12)
    pdf.write(8, ".")

    # Dates (original: y=399pt -> 141mm)
    debut = stagiaire.date_debut_stage
    fin = stagiaire.date_fin_stage
    if hasattr(debut, "strftime"):
        debut_str = debut.strftime("%d/%m/%Y")
        fin_str = fin.strftime("%d/%m/%Y")
    else:
        debut_str = str(debut)
        fin_str = str(fin)
    pdf.set_xy(lm, 141)
    pdf.cell(page_w - 2 * lm, 8, f"Du {debut_str} Jusqu'au {fin_str}.")

    # Texte legal (original: y=443pt + 465pt -> 156mm + 164mm)
    pdf.set_xy(lm, 156)
    pdf.cell(page_w - 2 * lm, 8, "Cette attestation est délivrée à l'intéressé sur sa demande pour servir et valoir ce que de")
    pdf.set_xy(lm, 164)
    pdf.cell(page_w - 2 * lm, 8, "droit.")

    # Signature RH (original: y=557pt + 581pt -> 197mm + 205mm)
    pdf.set_font("Calibri", "B", 14)
    pdf.set_xy(0, 197)
    pdf.cell(page_w, 10, "Responsable Développement des Ressources Humaines", align="C")

    if current_user and current_user.get("nom"):
        rh_nom = f"{current_user.get('prenom', '')} {current_user.get('nom', '')}".strip()
        pdf.set_xy(0, 205)
        pdf.cell(page_w, 10, rh_nom, align="C")
    else:
        pdf.set_xy(0, 205)
        pdf.cell(page_w, 10, "____________________________", align="C")

    pdf.output(output_path)
