# 19 Degrees

**170 bull shark bites in Australia since 1900. Not one in water below 19°C.**

19 Degrees is a free, open-source look at how warming water is changing where and when sharks and people meet in Australia. Every Australian bull, tiger and white shark bite since 1900 is matched to that month's sea surface temperature.

**Live site:** https://i-am-blake.github.io/19-degrees/

## What's here

| Path | What it is |
|---|---|
| `index.html` | The page: story, students and schools, researchers, news and media |
| `classroom*.html` | Printable classroom sheets with teacher notes, by age group |
| `data/` | Every dataset behind the charts (CSV and JSON), a data dictionary and a starter Jupyter notebook |
| `share/` | Share images and a LinkedIn carousel (PDF) |
| `fonts/` | Self-hosted fonts (SIL Open Font License) |
| `src/` | The scripts and template that build everything above |

## Rebuild it yourself

The analysis scripts are in `src/`. See [`src/README.md`](src/README.md) to rebuild every number, chart and download from the raw shark database and sea temperature records.

## Data sources

- Bites: [Australian Shark-Incident Database](https://zenodo.org/records/18752301) (Taronga Conservation Society Australia and Flinders University), CC BY 4.0
- Sea temperature: [HadISST](https://www.metoffice.gov.uk/hadobs/hadisst/) (UK Met Office), Open Government Licence

## Contributing

The most useful thing right now is **data**: tracking, catch, rescue and first-aid records, or evidence of which shark was involved in a past bite. See [CONTRIBUTING.md](CONTRIBUTING.md) for the data we need and how sharing works, or [open a data offer](../../issues/new?template=offer-data.yml).

You can also test one of the fifteen claims on the Researchers tab, or fix an error with an issue or pull request.

## Licence

Code: MIT. Text, charts and the 19 Degrees datasets: CC BY 4.0. Source data stays under its own licence. See `LICENSE`.

## Privacy

The site sets no cookies. Visits are counted with GoatCounter, which stores no personal data. The contact form sends messages through Web3Forms; the access key in the page is public by design and can only deliver messages to the site's owner.
