import csv
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from journey.models import Phase, JourneyPhase
from kpi.models import KPI


class Command(BaseCommand):
    help = "Restructure phases to match CSV structure, then import KPI data from kpis_shv_new.csv"

    def handle(self, **options):
        with transaction.atomic():
            self._restructure_phases()
            self._restructure_journey_phases()
            self._import_kpis()

    def _restructure_phases(self):
        self.stdout.write("=== Restructuring Phases ===\n")

        renames = {
            "Orientation": "1. Orientation",
            "Onboarding": "2. Onboarding",
            "Invoicing and Payment": "4. Invoicing and payment",
            "Support": "5. Support & Service",
            "After care": "6. After care",
        }
        for old, new in renames.items():
            try:
                p = Phase.objects.get(name=old)
                p.name = new
                p.save()
                self.stdout.write(f"  Renamed: '{old}' -> '{new}'")
            except Phase.DoesNotExist:
                self.stdout.write(f"  [skip] Phase '{old}' not found")

        # Merge Usage (id=3) + Order and Delivery (id=4) into "3. Usage, Order & Delivery"
        try:
            usage = Phase.objects.get(name="Usage")
        except Phase.DoesNotExist:
            self.stdout.write("  [skip] Phase 'Usage' not found")
            usage = None

        try:
            order_del = Phase.objects.get(name="Order and Delivery")
        except Phase.DoesNotExist:
            self.stdout.write("  [skip] Phase 'Order and Delivery' not found")
            order_del = None

        if usage and order_del:
            merged_name = "3. Usage, Order & Delivery"
            self.stdout.write(f"\n  Merging 'Usage' + 'Order and Delivery' -> '{merged_name}'")

            # Move KPIs from order_del to usage
            kpi_count = KPI.objects.filter(lifecycle_phase=order_del).update(lifecycle_phase=usage)
            self.stdout.write(f"  Moved {kpi_count} KPIs from 'Order and Delivery' -> 'Usage'")

            # Move JourneyPhases from order_del to usage
            jp_count = JourneyPhase.objects.filter(phase=order_del).update(phase=usage)
            self.stdout.write(f"  Moved {jp_count} JourneyPhases from 'Order and Delivery' -> 'Usage'")

            # Rename usage to merged name
            usage.name = merged_name
            usage.save()

            # Delete the old Order and Delivery phase (also cascade deletes its Steps, Actions, Touchpoints)
            order_del.delete()
            self.stdout.write(f"  Deleted Phase 'Order and Delivery'")

        # Reassign order values to be consecutive
        for i, phase in enumerate(Phase.objects.all().order_by('id')):
            phase.order = i
            phase.save()
        self.stdout.write("\n  Reordered all phases consecutively\n")

    def _restructure_journey_phases(self):
        self.stdout.write("=== Restructuring JourneyPhases ===\n")

        try:
            onboarding = Phase.objects.get(name="2. Onboarding")
        except Phase.DoesNotExist:
            self.stdout.write("  [skip] Phase '2. Onboarding' not found")
            return

        moves = ["Preparing for Installation", "Installation"]
        for jp_name in moves:
            try:
                jp = JourneyPhase.objects.get(name=jp_name)
                old_parent = jp.phase.name
                jp.phase = onboarding
                jp.save()
                self.stdout.write(f"  Moved '{jp_name}' from '{old_parent}' -> '2. Onboarding'")
            except JourneyPhase.DoesNotExist:
                self.stdout.write(f"  [skip] JourneyPhase '{jp_name}' not found")
        self.stdout.write("")

    def _import_kpis(self):
        self.stdout.write("=== Importing KPIs from CSV ===\n")

        csv_path = "kpis_shv_new.csv"
        phase_cache = {p.name: p for p in Phase.objects.all()}
        all_journey_phases = list(JourneyPhase.objects.select_related("phase"))

        def _find_journey_phase(sub_name, parent_name):
            """Case-insensitive match for JourneyPhase by name and parent phase name."""
            if not sub_name:
                return None
            sub_lower = sub_name.lower()
            parent_lower = parent_name.lower()
            for jp in all_journey_phases:
                if jp.name.lower() == sub_lower and jp.phase.name.lower() == parent_lower:
                    return jp
            # Fallback: match just by name
            for jp in all_journey_phases:
                if jp.name.lower() == sub_lower:
                    return jp
            return None

        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        updated = 0
        not_found = 0
        for row in rows:
            kpi_name = row["KPI"].strip()
            try:
                kpi = KPI.objects.get(name=kpi_name)
            except KPI.DoesNotExist:
                self.stdout.write(f"  [NOT FOUND] '{kpi_name}' — skipping")
                not_found += 1
                continue

            # Map Level to model choices
            level_map = {
                "Biz Goal KPI": "business_kpi",
                "KPIs": "kpi",
                "Metrics": "metric",
            }
            level = level_map.get(row.get("Level", "").strip(), "")

            # Map Type to model choices
            type_map = {
                "n.a.": "n_a",
                "Behavioral": "behavioral",
                "Experience": "experience",
                "Operational": "operational",
            }
            kpi_type = type_map.get(row.get("Type", "").strip(), "")

            # Map Do we measure it?
            measure_map = {
                "Yes": "yes",
                "No": "no",
                "Partially": "partially",
            }
            do_measure = measure_map.get(row.get("Do we measure it?", "").strip(), "no")

            # Map Review cadence to choices
            cadence_raw = row.get("Review cadence", "").strip().lower()
            cadence_map = {
                "daily": "daily",
                "weekly": "weekly",
                "weekly / monthly": "weekly",
                "monthly": "monthly",
                "bi-monthly": "monthly",
                "quarterly": "quarterly",
                "annually": "annually",
                "yearly": "annually",
                "post training session": "",
                "twice a year": "quarterly",
                "regular / monthy": "monthly",
            }
            review_cadence = ""
            for key, val in cadence_map.items():
                if key in cadence_raw:
                    review_cadence = val
                    break

            # Map lifecycle phase
            phase_name = row.get("Lifecycle phase (primary)", "").strip()
            lifecycle_phase = phase_cache.get(phase_name)

            # Map journey phase
            sub_phase = row.get("Cust Journey Phase", "").strip()
            journey_phase = _find_journey_phase(sub_phase, phase_name) if sub_phase else None

            # Update fields
            kpi.level = level or kpi.level
            kpi.kpi_type = kpi_type or kpi.kpi_type
            kpi.description = row.get("Description", "").strip() or kpi.description
            kpi.owner = row.get("Owner", "").strip() or kpi.owner
            kpi.why_important = row.get("Why important?", "").strip() or kpi.why_important
            kpi.do_we_measure_it = do_measure
            raw_measurement = row.get("How do/should we measure it?", "").strip()
            current, target = self._split_measurement(raw_measurement, do_measure in ('yes', 'partially'))
            kpi.measurement_current = current
            kpi.measurement_target = target
            raw_store = row.get("Where store?", "").strip()
            store_current, store_target = self._split_store(raw_store)
            kpi.store_current = store_current
            kpi.store_target = store_target
            kpi.review_cadence = review_cadence
            kpi.initiatives = row.get("Initiatives", "").strip()
            kpi.notes = row.get("Notes", "").strip()
            kpi.lifecycle_phase = lifecycle_phase
            kpi.journey_phase = journey_phase
            kpi.save()
            updated += 1

        self.stdout.write(f"\n  Updated: {updated} KPIs")
        if not_found:
            self.stdout.write(f"  Not found: {not_found} KPIs")

        # Summary of empty fields
        self.stdout.write("\n=== Post-import field coverage ===\n")
        total = KPI.objects.count()
        for field in [
            "do_we_measure_it", "measurement_current", "measurement_target",
            "measurement_trigger", "store_current", "store_target",
            "review_cadence",
            "initiatives", "notes", "impact", "effort",
            "implementation_phase", "target_quarter", "journey_phase",
        ]:
            if field in ("impact", "effort", "implementation_phase"):
                empty = KPI.objects.filter(**{field: ""}).count()
            elif field == "target_quarter":
                empty = KPI.objects.filter(**{field: ""}).count()
            elif field == "journey_phase":
                empty = KPI.objects.filter(**{field: None}).count()
            else:
                empty = KPI.objects.filter(**{field: ""}).count()
            pct = round(empty / total * 100)
            self.stdout.write(f"  {field}: {empty}/{total} empty ({pct}%)")

    @staticmethod
    def _split_measurement(text, is_measured):
        text = (text or '').strip()
        if not is_measured:
            return 'Not measured', text if text else ''
        if not text:
            return '', ''

        # Pattern 1: AS-IS / To Be
        m = re.match(r'(?i)as[- ]is:?\s*(.+?)\s*to[- ]?be:?\s*(.+)', text)
        if m:
            return m.group(1).strip().rstrip(';., '), m.group(2).strip().rstrip(';., ')

        # Pattern 2: Currently/Now/Presently X, Y in CRM / Y going forward
        m = re.match(
            r'(?i)(currently|now|presently)\s+(.+?)[,;]\s*(.+?(?:in\s+)?(?:crm|automate|going\s+forward|to\s+be))',
            text,
        )
        if m:
            current = f'{m.group(1).capitalize()} {m.group(2).strip()}'.strip().rstrip(';., ')
            target = m.group(3).strip().rstrip(';., ')
            return current, target

        # Pattern 3: X, Automation from Y / will be automated in Y
        m = re.match(
            r'(?i)(.+?)[,;]\s*(?:automation|will\s+be|going\s+forward|needs?\s+to\s+(?:be\s+)?(?:automate|track|add|upload|develop|capture|monitor))(.+)',
            text,
        )
        if m:
            current = m.group(1).strip().rstrip(';., ')
            target = text[m.start(2):].strip().rstrip(';., ')
            return current, target

        # Pattern 4: X. Need to / should / will be
        m = re.match(
            r'(?i)(.+?[.])?\s*(need(?:s)?\s+to|should|will\s+be|to\s+be)\s+(.+)',
            text,
        )
        if m:
            prefix = (m.group(1) or '').strip().rstrip('. ')
            current = prefix if prefix else 'Not measured'
            target = f'{m.group(2).strip()} {m.group(3).strip()}'.strip().rstrip(';., ')
            return current, target

        # Pattern 5: X, Y via CRM/automation
        m = re.match(r'(?i)(.+?)[.,;]\s*(.+?(?:crm|automate).+)', text)
        if m and not re.search(r'(?i)(?:track|done|available|through)\s', text):
            return m.group(1).strip().rstrip(';., '), m.group(2).strip().rstrip(';., ')

        # Fallback: all current
        return text, ''

    @staticmethod
    def _split_store(text):
        text = (text or '').strip()
        if not text:
            return '', ''
        m = re.split(r'\s*-->\s*|\s*→\s*', text)
        if len(m) == 2:
            return m[0].strip(), m[1].strip()
        return text, ''
