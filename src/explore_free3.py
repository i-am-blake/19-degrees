"""Look only: text of free public reports to strengthen the answers (ISAF yearly reports, NSW shark program reports,
NOAA gray seal assessment). Changes nothing on the site."""
import io, json, time, urllib.request
from pypdf import PdfReader
UA = {"User-Agent": "Mozilla/5.0 (compatible; 19-degrees research; +https://19-degrees.org)"}
DOCS = {
 "isaf2023": "https://www.floridamuseum.ufl.edu/wp-content/uploads/sites/23/2024/02/The-ISAF-2023-shark-attack-report.pdf",
 "isaf2024": "https://floridamuseum.ufl.edu/wp-content/uploads/sites/23/2025/02/Full.pdf",
 "nsw_smp_2324": "https://sharksmart.nsw.gov.au/__data/assets/pdf_file/0010/1570987/Shark-Meshing-Bather-Protection-Program-2023-24-Annual-Performance-Report.pdf",
 "nsw_tssc_2425": "https://www.environment.nsw.gov.au/sites/default/files/2025-11/2024-25-scientific-committtee-advice-shark-meshing-bather-protection-program.pdf",
 "nsw_smart_2223": "https://www.sharksmart.nsw.gov.au/__data/assets/pdf_file/0003/1546302/NSW-SMART-drumline-report-1-July-2022-30-June-2023.pdf",
 "noaa_grayseal_2024": "https://www.fisheries.noaa.gov/s3/2026-04/gray-seal_2024-template_jb-edit-gw508.pdf",
}
out = {}
for k, u in DOCS.items():
    for t in range(3):
        try:
            b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
            r = PdfReader(io.BytesIO(b)); out[k] = {"url": u, "pages": len(r.pages), "text": "\n".join((p.extract_text() or "") for p in r.pages)[:120000]}
            print(k, "pages", len(r.pages), "chars", len(out[k]["text"]), flush=True); break
        except Exception as e:
            out[k] = {"url": u, "error": repr(e)[:200]}; print(k, "failed", repr(e)[:120], flush=True); time.sleep(5)
json.dump(out, open("../free3.json", "w"))
