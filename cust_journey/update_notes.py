import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cust_journey.settings")
import django
django.setup()

from kpi.models import KPI

CSV_PATH = os.path.expanduser("~/Downloads/shv-kpi-framework-current-notes-workshop.csv")

# -----------------------------------------------------------
# Typo / acronym normalization — applied to every note
# -----------------------------------------------------------
FIXES = [
    # Typos
    (r'\binsltalation\b', 'installation'),
    (r'\bthiy\b', 'they'),
    (r'\bregualr\b', 'regular'),
    (r'\bfeeback\b', 'feedback'),
    (r'\bcomplie\b', 'compile'),
    (r'\bmotnly\b', 'monthly'),
    (r'\bcontroling\b', 'controlling'),
    (r'\bsystme\b', 'system'),
    (r'\bmechanisim\b', 'mechanism'),
    (r'\bened\b(?=\s+to)', 'need'),
    (r'\beffor\b', 'effort'),
    (r'\bprioritised\b', 'prioritized'),
    (r'\bdeprioritise\b', 'deprioritize'),
    (r'\bdevations\b', 'deviations'),
    (r'\banlyse\b', 'analyse'),
    (r'\bfilling\b(?=\s|$)', 'filling'),
    # Acronyms (word boundaries)
    (r'\bcsat\b', 'CSAT'),
    (r'\bCsat\b', 'CSAT'),
    (r'\bcrm\b', 'CRM'),
    (r'\bnps\b', 'NPS'),
    (r'\bsla\b', 'SLA'),
    (r'\bSla\b', 'SLA'),
    (r'\bsop\b', 'SOP'),
    (r'\bSop\b', 'SOP'),
    (r'\bces\b', 'CES'),
    (r'\bCes\b', 'CES'),
    (r'\bcx\b', 'CX'),
    (r'\bCx\b', 'CX'),
    (r'\bcs\b', 'CS'),
    (r'\bCs\b', 'CS'),
    (r'\bftr\b', 'FTR'),
    (r'\bFtr\b', 'FTR'),
    (r'\brft\b', 'RFT'),
    (r'\bRft\b', 'RFT'),
    (r'\bftp\b', 'FTR'),
    (r'\bkpi\b', 'KPI'),
    (r'\bKpi\b', 'KPI'),
    (r'\bftfr\b', 'FTFR'),
    (r'\bFtfr\b', 'FTFR'),
    (r'\brft\b', 'RFT'),
    (r'\bpbi\b', 'PBI'),
    (r'\bPbi\b', 'PBI'),
    (r'\bsap\b', 'SAP'),
    (r'\bSap\b', 'SAP'),
    (r'\bmis\b', 'MIS'),
    (r'\bMis\b', 'MIS'),
    # Cleanup
    (r'\s+', ' '),
    (r'\s*-\s*', ' - '),
    (r'\s*\.\s*\.\s*\.\s*', '... '),
    (r'\s*,\s*,', ','),
    (r'\s([.,;:!?])', r'\1'),
    (r'\(\s+', '('),
    (r'\s+\)', ')'),
]

def apply_fixes(text):
    """Apply typo & acronym fixes."""
    for pattern, replacement in FIXES:
        text = re.sub(pattern, replacement, text)
    return text.strip()


def capitalize_sentences(text):
    """Ensure each sentence starts with a capital letter."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return ' '.join(s.capitalize() if s else s for s in sentences).strip()


def sanitize(text):
    """Full sanitization pipeline."""
    if not text or not text.strip():
        return ''
    result = text.strip()
    result = apply_fixes(result)
    result = re.sub(r'\s{2,}', ' ', result)
    result = re.sub(r'\s-\s', ' - ', result)
    result = capitalize_sentences(result)
    # Ensure first letter is capitalised
    if result and result[0].islower():
        result = result[0].upper() + result[1:]
    # Remove trailing dashes / fragments
    result = result.rstrip(' \t-;,').strip()
    return result


# -----------------------------------------------------------
# Manual override map — hand-crafted polished versions
# -----------------------------------------------------------
MANUAL = {
    # These get full rewrite for readability
    "Cold-to-qualified conversion rate": (
        "Clean AS-IS / To Be split. Currently manual Excel/Marketing tracking; "
        "target is CRM-automated pipeline tracking."
    ),
    "Qualified-to-client conversion rate": (
        "Manthan tracking is in process. Once the CRM goes live, this will be "
        "fully automated."
    ),
    "Lead-to-active conversion": (
        "Low effort. Once the CRM goes live, this will be very easy to track."
    ),
    "Progress communication CSAT": (
        "The process is happening but needs to be tracked. We already know when "
        "it can be measured — the system and the survey just need to be set up."
    ),
    "Handover Customer Effort Score": (
        "Feedback is already collected for this. The scoring is not in place "
        "right now, but the process exists."
    ),
    "Customer-Induced Delay Incidents": (
        "Impact is not high. Even if customers are delaying, that is fine because "
        "it might be better for the customer experience if they can delay. However, "
        "the operational side needs to be flexible."
    ),
    "Installation lead time": (
        "Low effort. Once the CRM goes live, this will be very easy to track."
    ),
    "Right-First-Time (RFT) Installation Rate": (
        "Should be renamed to FTR — that is the preferred naming. Reports are "
        "already being handed in and data is already collected during the "
        "installation phase, so it is being measured. It can be difficult to "
        "assess, but it is currently already being measured. Also measure it from "
        "the first complaint that is filed. The measurement still needs to be "
        "set up."
    ),
    "Training quality CSAT": (
        "This still needs to be implemented. It is important. Set the process "
        "to track it and make it more regular."
    ),
    "First delivery on-time %": (
        "This still needs to be tracked. The system to measure it is in place."
    ),
    "Relationship NPS": (
        "This is already being measured and the post-survey result is already "
        "being tracked."
    ),
    "Proactive communication CSAT": (
        "This falls on the impact side."
    ),
    "Safety perception score": (
        "Regular audits. Feedback is already collected during audits. Many things "
        "are still gut feel. High effort to implement."
    ),
    "Dry out rate": (
        "Totally monitored. CS is reporting in the system. This is being tracked "
        "and reported on."
    ),
    "Audit Hazard Rectification Rate": (
        "The process exists. The review and follow-up approach needs to be improved."
    ),
    "Order frequency": (
        "Already captured and already reviewed."
    ),
    "Order volume": (
        "Already captured and already reviewed."
    ),
    "Order channel mix": (
        "Already captured and already reviewed."
    ),
    "Order drop off": (
        "Not important because it almost never happens."
    ),
    "Customers gas levels": (
        "No structured way to compile the offline process yet."
    ),
    "Urgent orders": (
        "Already captured and already reviewed."
    ),
    "Order placement CSAT": (
        "CSAT is available. Review needs to be improved."
    ),
    "Order Cancellation & Reschedule Rate": (
        "Already being tracked, but not actively measured. The data source "
        "exists — it just needs to be reviewed."
    ),
    "On-time delivery %": (
        "Process is already established and already reviewed."
    ),
    "Per-delivery feedback rate": (
        "This can be captured in the CSAT. Additional fields with topics "
        "related to this metric can be added."
    ),
    "Complaint volume by type": (
        "This metric is duplicated across systems, which is why it got prioritized."
    ),
    "Credit note  turn around time": (
        "Not really measured or recorded anywhere. The SOP captures it."
    ),
    "Billing CSAT": (
        "Not currently being done. Process-wise, this needs to be implemented."
    ),
    "Billing Customer Effort Score (CES)": (
        "Not currently being done. Process-wise, this needs to be implemented."
    ),
    "Dispute satisfaction": (
        "Not currently tracked. This is very important — keep it in quick wins."
    ),
    "Revenue leakage": (
        "Various KPIs already used to measure this. Monthly meetings review "
        "what is happening with customers. Robust controlling system in place."
    ),
    "Dispute resolution time": (
        "This is not really tracked. The tracking process needs to be "
        "implemented. It is logged, but not instrumented."
    ),
    "Invoice accuracy rate": (
        "Not currently measured. Deprioritized because it is a lot of effort "
        "to implement, and it is normally accurate."
    ),
    "Portal adoption rate": (
        "No portal exists yet. Currently invoices are uploaded as physical "
        "copies to the customer portal. The portal is not done yet, which is "
        "why it is deprioritized for invoicing. Move this to the usage phase."
    ),
    "Payment delinquency rate": (
        "A threshold of days is set — everything exceeding it is already "
        "flagged as overdue. Actively tracked."
    ),
    "Maintenance & Support CSAT": (
        "A plan is being created for implementing this. It is reviewed "
        "quarterly. Feedback is collected from maintenance. A score needs to "
        "be added and analysed more thoroughly."
    ),
    "Resolution rate": (
        "Tracked by CS and also by operations. Monthly report with a standard "
        "format of 4 days. Any deviations require action. Monthly/quarterly "
        "meetings are already in place for follow-up. Currently tracked "
        "extensively for filling, but other topics are not tracked the same "
        "way. Make the data source available — this can be added into a dashboard."
    ),
    "Complaint resolution CSAT": (
        "CSAT is in place but the process for NPS post complaint resolution "
        "does not exist yet. Change this to CSAT. It is not tracked 100% — a "
        "mechanism to analyse and track it is still needed."
    ),
    "Repeat complaint rate": (
        "This is already tracked and is discussed with the goal of reducing "
        "repeat complaints."
    ),
    "Support ticket volume by type": (
        "Complaint topics by type are visible. Tracking per customer is also "
        "desired."
    ),
    "First response time": (
        "Already being captured. An SLA of 2-3 days is in place. If this is "
        "not met, action is taken. We know where the data is, but it is not "
        "instrumented yet."
    ),
    "First contact resolution rate": (
        "Not currently tracked in a structured way. Statuses exist and are "
        "being tracked — the customer can also view them. Data is available "
        "but needs to be made analysable. Tracking is already in place."
    ),
    "First-Time Fix Rate (FTFR) for Technical Faults": (
        "This is also recorded, but needs to be analysed to get the number "
        "properly. Data is available — the analysis approach still needs to "
        "be determined."
    ),
}

# -----------------------------------------------------------
# Main
# -----------------------------------------------------------
def main():
    # Parse CSV
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [(row[0].strip(), row[1].strip() if len(row) > 1 else '') for row in reader]

    print(f"Read {len(rows)} rows from CSV.\n")

    # Build lookup by name
    kpi_by_name = {kpi.name: kpi for kpi in KPI.objects.all()}

    # CSV→DB name mappings for mismatches
    NAME_MAP = {
        "Order placement CES": "Order placement CSAT",
        "Complaint resolution NPS": "Complaint resolution CSAT",
    }

    # Also add manual entries under the CSV names
    MANUAL["Order placement CES"] = (
        "CSAT is available. Review needs to be improved."
    )
    MANUAL["Complaint resolution NPS"] = (
        "CSAT is in place but the process for NPS post complaint resolution "
        "does not exist yet. Change this to CSAT. It is not tracked 100% — a "
        "mechanism to analyse and track it is still needed."
    )

    to_update = []   # (kpi, old_notes, new_notes)
    skipped_empty = 0
    not_found = 0

    for name, raw in rows:
        if not raw:
            skipped_empty += 1
            continue

        db_name = NAME_MAP.get(name, name)
        if db_name not in kpi_by_name:
            print(f"[NOT FOUND] {name}")
            not_found += 1
            continue

        kpi = kpi_by_name[db_name]

        if name in MANUAL:
            sanitized = MANUAL[name]
        else:
            sanitized = sanitize(raw)

        if sanitized == kpi.notes:
            continue  # no change

        to_update.append((kpi, kpi.notes, sanitized))

    # --- Decide mode ---
    dry_run = "--write" not in sys.argv

    if dry_run:
        print(f"DRY RUN — {len(to_update)} KPIs would be updated. Run with --write to apply.\n")
    else:
        print(f"Writing {len(to_update)} updates to database...\n")

    for kpi, old, new in to_update:
        kpi_name = kpi.name[:60]
        old_preview = old[:80].replace('\n', ' ') if old else '(empty)'
        new_preview = new[:80].replace('\n', ' ')

        if dry_run:
            print(f"--- {kpi_name}")
            print(f"    OLD: {old_preview}")
            print(f"    NEW: {new_preview}")
        else:
            kpi.notes = new
            kpi.save(update_fields=['notes'])
            print(f"[UPDATED] {kpi_name}")

    if not dry_run:
        print(f"\nDone. {len(to_update)} notes updated.")

    print(f"\nSkipped (empty notes in CSV): {skipped_empty}")
    if not_found:
        print(f"Not found in DB: {not_found}")


if __name__ == "__main__":
    main()
