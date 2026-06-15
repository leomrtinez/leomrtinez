import os
import re
from urllib.parse import quote

from scholarly import scholarly


SCHOLAR_ID = "g1__itUAAAAJ"
PROFILE_URL = "https://scholar.google.ca/citations?user=g1__itUAAAAJ&hl=fr&oi=sra"
README_PATH = "README.md"
MAX_PUBLICATIONS = 10


def publication_link(pub):
    if pub.get("pub_url"):
        return pub["pub_url"]

    author_pub_id = pub.get("author_pub_id")
    if author_pub_id:
        citation_id = (
            author_pub_id
            if author_pub_id.startswith(f"{SCHOLAR_ID}:")
            else f"{SCHOLAR_ID}:{author_pub_id}"
        )
        return (
            "https://scholar.google.ca/citations?"
            f"view_op=view_citation&hl=fr&user={SCHOLAR_ID}"
            f"&citation_for_view={quote(citation_id)}"
        )

    return PROFILE_URL


def clean(value):
    if not value:
        return ""
    return str(value).replace("\n", " ").strip()


def render_publication(pub):
    bib = pub.get("bib", {})

    title = clean(bib.get("title")) or "Titre indisponible"
    authors = clean(
        bib.get("author")
        or bib.get("authors")
        or bib.get("author_name")
    )

    venue = clean(
        bib.get("venue")
        or bib.get("journal")
        or bib.get("conference")
        or bib.get("publisher")
    )

    year = clean(
        bib.get("pub_year")
        or bib.get("year")
    )

    citations = pub.get("num_citations", 0)
    link = publication_link(pub)

    venue_line = " · ".join(part for part in [venue, year] if part)

    lines = [
        f"### {link}",
    ]

    if authors:
        lines.append(f"{authors}")

    if venue_line:
        lines.append(f"*{venue_line}*")

    lines.append(f"**Cité par : {citations}**")
    lines.append("")

    return "\n".join(lines)


def main():
    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author)

    publications = author.get("publications", [])

    # Google Scholar retourne souvent les publications déjà triées par citations.
    # On force ici un tri décroissant par citations pour un rendu “Scholar-like”.
    publications = sorted(
        publications,
        key=lambda p: p.get("num_citations", 0),
        reverse=True,
    )

    rendered = "\n".join(
        render_publication(pub)
        for pub in publications[:MAX_PUBLICATIONS]
    )

    if not rendered.strip():
        rendered = "_Aucune publication trouvée automatiquement._"

    with open(README_PATH, "r", encoding="utf-8") as file:
        readme = file.read()

    pattern = (
        r"<!-- GOOGLE-SCHOLAR:START -->"
        r".*?"
        r"<!-- GOOGLE-SCHOLAR:END -->"
    )

    replacement = (
        "<!-- GOOGLE-SCHOLAR:START -->\n"
        f"{rendered}\n"
        "<!-- GOOGLE-SCHOLAR:END -->"
    )

    updated = re.sub(pattern, replacement, readme, flags=re.DOTALL)

    with open(README_PATH, "w", encoding="utf-8") as file:
        file.write(updated)


if __name__ == "__main__":
    main()
