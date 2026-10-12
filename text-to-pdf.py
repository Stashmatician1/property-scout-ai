from reportlab.platypus import SimpleDocTemplate, Paragraph # type: ignore
from reportlab.lib.styles import getSampleStyleSheet # type: ignore

txt_file = r"PROJECT SKYLINE RESIDENCES.txt"
pdf_file = r"PROJECT SKYLINE RESIDENCES.pdf"

def txt_to_pdf(txt_file, pdf_file):

    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.readlines()

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    story = []

    for line in text:

        if line.strip():
            story.append(
                Paragraph(
                    line.strip(),
                    styles["BodyText"]
                )
            )

    doc.build(story)

    print(f"Saved: {pdf_file}")

txt_to_pdf(txt_file, pdf_file)

