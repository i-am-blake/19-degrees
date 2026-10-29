# Contributing to 19 Degrees

19 Degrees is meant to grow into a shared evidence base on sharks and a warming ocean. There are three ways to help.

## 1. Share data

The site already uses every public source we could find. The data that would settle the open claims sits with agencies, researchers, surf clubs, councils and health services. If you hold any of the following, or know who does, please get in touch.

| Data | Claims it tests | Likely holders |
|---|---|---|
| Acoustic detections of tagged bull, tiger and white sharks, especially south of Sydney | C2, C5, C8 | IMOS Animal Tracking, NSW SharkSmart, university tagging programs |
| Shark-control catch by species, beach and year (NSW, WA) | C1 | NSW DPIRD, WA DPIRD |
| Drone and detection trials in murky water | C10 | NSW DPIRD, universities |
| Baitfish (e.g. mullet) catch by month and region over decades | C4 | NSW DPIRD fisheries |
| Downscaled sea temperature projections to 2050 | C3 | CSIRO, Bureau of Meteorology |
| Turtle tracks and nesting dates; humpback counts | C5, C8 | Turtle tracking programs, whale survey groups |
| De-identified incident timelines: time to first aid, kit or patrol nearby, outcome | C9, C12 | Surf Life Saving, ambulance services, National Coronial Information System |
| Bleeding kit locations, patrolled beaches and seasons, ambulance response times | C13 | Community Shark Bite Kits, councils, Surf Life Saving, ambulance services |
| Tourniquet and leash trials | C11 | Emergency medicine researchers |
| Evidence confirming the species in past bites (bite analysis, tooth fragments, DNA, video of the shark) | All charts | Shark researchers, Taronga Conservation Society |
| Exact dates and places of bites | C6 | Taronga Conservation Society |
| Bite trials of wetsuit fabrics and lights with bull and tiger sharks | C14, C15 | University labs, product makers |

**How sharing works**

1. **Tell us what you have.** [Open a data offer](../../issues/new?template=offer-data.yml) or use the [contact form](https://19-degrees.org/#contact). A description is enough; don't post the data itself in an issue.
2. **Agree how it's used:** openly under CC BY, summarised only (results published, raw data stays private), or under your organisation's data agreement.
3. **Keep people private.** Only de-identified data: no names, contact details, photos of people or medical records that identify anyone. Only share data you have the right to share. Never contact people who were bitten, or their families, for this project.
4. **Get credit.** Your name or organisation on the claim card and in the site's changelog, using the [CRediT contributor roles](https://credit.niso.org/). The data stays yours.

## 2. Test a claim

The Researchers tab lists fifteen testable claims (C1–C15), each with what would support it and what would rule it out.

- Write down your hypothesis, data, method and what would prove it wrong **before** you look at the result. Public pre-registration (e.g. on OSF) is ideal.
- Get any approvals your work needs (human research ethics for records about people; animal ethics and permits for fieldwork).
- Report effect sizes with 95% confidence intervals, say how many tests you ran, and label exploratory findings.
- Share code and data, or exactly how to get them, so others can reproduce the result. Negative results are welcome.
- Disclose funding and any conflict of interest, including links to deterrent makers or advocacy groups.

The scripts in [`src/`](src/README.md) rebuild every number on the site; the starter notebook in `data/` reproduces the headline results in a few minutes.

## 3. Fix something

Spotted an error in the text, a number or the code? Open an issue or a pull request. For changes to the site, edit `src/page19.html` (the template) and the scripts in `src/`, not the built `index.html`, which is regenerated weekly.

## Licences

By contributing code you agree to license it under MIT; text and data you contribute to the site are published under CC BY 4.0 unless agreed otherwise. Source data keeps its own licence.
