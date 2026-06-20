"""Generate a sample DPDP PDF so you can test the pipeline before adding the official Act PDF.

Replace data/DPDP_sample.pdf with the real DPDP Act / Rules PDF and re-run `python ingest.py`.
The content here is a plain-language educational summary, current to the DPDP Rules 2025
(notified 13 Nov 2025). It is NOT the official text and NOT legal advice.

Run:  python make_sample_pdf.py
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

SECTIONS = [
    ("Overview, Scope and Applicability",
     ["The Digital Personal Data Protection Act, 2023 (DPDP Act) is India's data-protection law. "
      "It received presidential assent in August 2023. The Digital Personal Data Protection Rules, "
      "2025 (DPDP Rules) were notified on 13 November 2025 and provide the operational detail.",
      "Key roles: the Data Principal is the individual the data is about; the Data Fiduciary decides "
      "the purpose and means of processing; the Data Processor processes data on a Fiduciary's behalf; "
      "a Consent Manager is a platform registered with the Data Protection Board through which an "
      "individual can give, manage and withdraw consent.",
      "The Act applies to digital personal data — including data collected offline and later digitised. "
      "It applies to processing in India, and also outside India where the processing is connected with "
      "offering goods or services to individuals in India. It does not apply to data processed for purely "
      "personal or domestic purposes, or to data the individual has made public themselves.",
      "Implementation is phased. Provisions setting up the Data Protection Board came into force on "
      "notification. Registration of Consent Managers becomes effective about twelve months later. "
      "Substantive obligations — notices, consent, security safeguards, breach reporting, rights, and "
      "Significant Data Fiduciary duties — carry an eighteen-month runway, with full compliance expected "
      "by 13 May 2027."]),

    ("Consent, Notice and Consent Managers",
     ["Personal data may generally be processed only for a lawful purpose for which the Data Principal "
      "has given consent, or for certain legitimate uses. Consent must be free, specific, informed, "
      "unconditional and unambiguous, given through a clear affirmative action, and limited to the data "
      "necessary for the stated purpose.",
      "Every consent request must come with a notice. The notice must state what personal data is "
      "collected and the purpose, how to exercise rights, how to withdraw consent, and how to complain "
      "to the Data Protection Board. It must be in clear plain language, available in English or any "
      "language in the Eighth Schedule to the Constitution.",
      "A Data Principal can withdraw consent at any time, and withdrawal must be as easy as giving "
      "consent. After withdrawal, the Fiduciary must stop processing within a reasonable time unless "
      "another lawful ground applies.",
      "Legitimate uses allow some processing without separate consent, such as data voluntarily provided, "
      "certain State functions and subsidies, medical emergencies, and specified employment purposes. "
      "A Consent Manager, registered with the Board, gives individuals one place to manage consents."]),

    ("Rights of the Data Principal",
     ["Right to access information: an individual can ask for a summary of the personal data being "
      "processed, the processing activities, and the identities of Fiduciaries and Processors the data "
      "was shared with.",
      "Right to correction and erasure: an individual can have inaccurate data corrected, incomplete "
      "data completed, data updated, and data erased when it is no longer needed, unless the law "
      "requires it to be kept.",
      "Right of grievance redressal: the Fiduciary or Consent Manager must offer a readily available "
      "grievance mechanism and respond within the prescribed period; the individual generally uses this "
      "before approaching the Board.",
      "Right to nominate: an individual can nominate another person to exercise their rights if they die "
      "or become incapacitated. Individuals also have duties, such as not impersonating others and not "
      "filing false or frivolous complaints."]),

    ("Obligations of Data Fiduciaries",
     ["A Data Fiduciary is accountable for compliance whether it processes data itself or through a "
      "Processor. It must process data only for the consented purpose, keep it accurate where used for "
      "decisions or sharing, and erase it when consent is withdrawn or the purpose ends.",
      "It must implement reasonable security safeguards to prevent a personal data breach — such as "
      "encryption, access control, logging and monitoring, and measures to detect and respond to "
      "breaches — and ensure its Processors do the same under a valid contract.",
      "On a personal data breach, the Fiduciary must notify the Data Protection Board and each affected "
      "individual in the manner and timelines in the Rules, describing the breach, its consequences, the "
      "remedial steps, and what the individual can do.",
      "The Central Government may designate certain entities as Significant Data Fiduciaries (SDFs) based "
      "on data volume and sensitivity and risk. SDFs must appoint an India-based Data Protection Officer, "
      "appoint an independent data auditor, and carry out periodic Data Protection Impact Assessments."]),

    ("Children and Persons with Disability",
     ["Under the DPDP Act a child is anyone below eighteen years of age. Before processing a child's "
      "personal data, a Data Fiduciary must obtain verifiable consent from a parent or lawful guardian, "
      "verified using reliable identity and age details or a virtual token mapped to them.",
      "A Fiduciary must not process children's data in a way likely to cause harm, must not track or "
      "behaviourally monitor children, and must not direct targeted advertising at them.",
      "Where a person with disability has a lawful guardian, the Fiduciary must obtain the guardian's "
      "consent before processing that person's data.",
      "The Rules exempt some limited, necessary processing from the stricter children's requirements — "
      "for example certain processing by healthcare providers, educational institutions, and entities "
      "providing benefits to children, subject to conditions."]),

    ("Data Protection Board, Penalties and Cross-Border Transfers",
     ["The Data Protection Board of India is the regulator. It investigates breaches and complaints, "
      "directs remedial measures, and imposes financial penalties. Appeals from the Board go to the "
      "Telecom Disputes Settlement and Appellate Tribunal (TDSAT).",
      "Penalties are tiered by the type of violation and can reach up to ₹250 crore per instance. The "
      "highest penalties apply to failures to take reasonable security safeguards that lead to a breach. "
      "There are also penalties for failing to notify breaches and for breaching children's-data duties.",
      "For cross-border transfers the Act takes a permissive negative-list approach: personal data may be "
      "transferred to any country except those the Central Government restricts by notification. For "
      "Significant Data Fiduciaries the Government may additionally require certain data to stay in India.",
      "This document is an educational summary, current to the DPDP Rules 2025, and is not legal advice."]),
]


def main():
    doc = SimpleDocTemplate("data/DPDP_sample.pdf", pagesize=A4,
                            topMargin=2*cm, bottomMargin=2*cm, leftMargin=2.2*cm, rightMargin=2.2*cm)
    styles = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=styles["Heading1"], fontSize=15, spaceAfter=10, textColor="#11243d")
    body = ParagraphStyle("b", parent=styles["BodyText"], fontSize=10.5, leading=15, spaceAfter=8)
    title = ParagraphStyle("t", parent=styles["Title"], fontSize=20, textColor="#11243d")

    flow = [Paragraph("Digital Personal Data Protection (DPDP) — Plain-Language Summary", title),
            Paragraph("Educational sample. Current to the DPDP Rules 2025 (13 Nov 2025). Not legal advice.", body),
            Spacer(1, 0.4*cm)]
    for i, (head, paras) in enumerate(SECTIONS):
        if i:
            flow.append(PageBreak())
        flow.append(Paragraph(head, h))
        for p in paras:
            flow.append(Paragraph(p, body))
    doc.build(flow)
    print("Wrote data/DPDP_sample.pdf")


if __name__ == "__main__":
    main()
