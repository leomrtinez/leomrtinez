import re
from pathlib import Path

import bibtexparser


README_PATH = Path("README.md")
BIB_PATH = Path("publications.bib")
MAX_PUBLICATIONS = 12

START_MARKER = "<!-- PUBLICATIONS:START -->"
END_MARKER = "<!-- PUBLICATIONS:END -->"


def clean(value):
    """
    Nettoie une chaîne BibTeX pour l'affichage Markdown/HTML.
    """
    if not value:
        return ""

    value = str(value)
    value = value.replace("\n", " ")
    value = value.replace("{", "")
    value = value.replace("}", "")
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def format_author_name(author):
    """
    Convertit 'Nom, Prénom' en 'Prénom Nom'.
    Si le nom est déjà dans le bon ordre, on le garde tel quel.
    """
    author = clean(author)

    if "," in author:
        parts = [part.strip() for part in author.split(",", 1)]
        if len(parts) == 2:
            last, first = parts
            return f"{first} {last}".strip()

    return author


def format_authors(authors_field):
    """
    Formate les auteurs d'une entrée BibTeX.
    BibTeX sépare normalement les auteurs avec 'and'.
    """
    authors_field = clean(authors_field)

    if not authors_field:
        return ""

    authors = [
        format_author_name(author)
        for author in authors_field.split(" and ")
        if author.strip()
    ]

    return ", ".join(authors)


def get_publication_link(entry):
    """
    Priorité des liens :
    1. url
    2. doi
    3. rien
    """
    url = clean(entry.get("url"))
    doi = clean(entry.get("doi"))

    if url:
        return url

    if doi:
        doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        return f"https://doi.org/{doi}"

    return ""


def get_venue(entry):
    """
    Récupère le nom de la revue/conférence/livre selon le type d'entrée BibTeX.
    """
    venue_fields = [
        "journal",
        "journaltitle",
        "booktitle",
        "conference",
        "publisher",
        "school",
        "institution",
    ]

    for field in venue_fields:
        venue = clean(entry.get(field))
        if venue:
            return venue

    return ""


def get_year(entry):
    """
    Récupère l'année de publication.
    """
    year = clean(entry.get("year"))

    if year:
        match = re.search(r"\d{4}", year)
        if match:
            return match.group(0)

    return ""


def get_extra_metadata(entry):
    """
    Génère une petite ligne volume/numéro/pages si disponible.
    """
    volume = clean(entry.get("volume"))
    number = clean(entry.get("number"))
    pages = clean(entry.get("pages"))

    parts = []

    if volume:
        if number:
            parts.append(f"{volume}({number})")
        else:
            parts.append(volume)

    if pages:
        parts.append(f"pp. {pages}")

    return ", ".join(parts)


def render_publication(entry):
    """
    Convertit une entrée BibTeX en bloc HTML compact pour README GitHub.
    Style proche de Google Scholar :
    titre cliquable, auteurs, venue/année, métadonnées.
    """
    title = clean(entry.get("title")) or "Titre indisponible"
    authors = format_authors(entry.get("author"))
    venue = get_venue(entry)
    year = get_year(entry)
    link = get_publication_link(entry)
    extra_metadata = get_extra_metadata(entry)

    venue_parts = [part for part in [venue, year] if part]
    venue_line = " · ".join(venue_parts)

    if link:
        title_line = f'<a href="{link}"><strong>{title}</strong></a>'
    else:
        title_line = f"<strong>{title}</strong>"

    block = "<p>\n"
    block += f"  {title_line}<br>\n"

    if authors:
        block += f"  <em>{authors}</em><br>\n"

    if venue_line:
        block += f"  {venue_line}<br>\n"

    if extra_metadata:
        block += f"  <sub>{extra_metadata}</sub><br>\n"

    doi = clean(entry.get("doi"))
    if doi:
        doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        block += f'  <sub>DOI: <a href="https://doi.org/{doi}">{doi}</a></sub>\n'

    block += "</p>"

    return block


def sort_entries(entries):
    """
    Trie les publications par année décroissante.
    Les entrées sans année vont à la fin.
    """
    def sort_key(entry):
        year = get_year(entry)
        try:
            return int(year)
        except ValueError:
            return -1

    return sorted(entries, key=sort_key, reverse=True)


def load_bib_entries():
    """
    Lit le fichier publications.bib.
    """
    if not BIB_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable : {BIB_PATH}")

    with open(BIB_PATH, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)

    return bib_database.entries


def generate_publications_section():
    """
    Génère la section complète des publications.
    """
    entries = load_bib_entries()
    entries = sort_entries(entries)

    if MAX_PUBLICATIONS:
        entries = entries[:MAX_PUBLICATIONS]

    if not entries:
        return "_Aucune publication trouvée dans `publications.bib`._"

    rendered = [render_publication(entry) for entry in entries]

    footer = (
        '\n<p>'
        '<a href="https://scholar.google.ca/citations?user=g1__itUAAAAJ&hl=fr&oi=sra">'
        "Voir toutes mes publications sur Google Scholar"
        "</a>"
        "</p>"
    )

    return "\n\n".join(rendered) + footer


def update_readme(publications_section):
    """
    Remplace le contenu situé entre les marqueurs dans README.md.
    """
    if not README_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable : {README_PATH}")

    readme = README_PATH.read_text(encoding="utf-8")

    pattern = (
        f"{re.escape(START_MARKER)}"
        r".*?"
        f"{re.escape(END_MARKER)}"
    )

    replacement = (
        f"{START_MARKER}\n"
        f"{publications_section}\n"
        f"{END_MARKER}"
    )

    updated_readme = re.sub(
        pattern,
        replacement,
        readme,
        flags=re.DOTALL,
    )

    if updated_readme == readme:
        raise RuntimeError(
            "Les marqueurs PUBLICATIONS n'ont pas été trouvés dans README.md."
        )

    README_PATH.write_text(updated_readme, encoding="utf-8")


def main():
    publications_section = generate_publications_section()
    update_readme(publications_section)
    print("README.md mis à jour à partir de publications.bib.")


if __name__ == "__main__":
    main()
