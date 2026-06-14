import re
from urllib.parse import quote

from scholarly import scholarly


SCHOLAR_ID = "g1__itUAAAAJ"
PROFILE_URL = "https://scholar.google.ca/citations?user=g1__itUAAAAJ&hl=fr&oi=sra"
README_PATH = "README.md"
MAX_PUBLICATIONS = 10


def clean(value):
    """
    Nettoie les valeurs récupérées depuis Google Scholar.
    """
    if not value:
        return ""
    return str(value).replace("\n", " ").strip()


def publication_link(pub):
    """
    Retourne le meilleur lien disponible pour une publication.
    Si Google Scholar fournit un lien direct, on l'utilise.
    Sinon, on construit un lien vers la page de citation Scholar.
    """
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


def render_publication(pub):
    """
    Convertit une publication Scholar en bloc HTML/Markdown
    pour un rendu proche de Google Scholar dans le README.
    """
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

    venue_parts = [part for part in [venue, year] if part]
    venue_line = " · ".join(venue_parts)

    block = f"""<p><a href="{link}"><strong>{title}</strong></a><br>"""

    if authors:
        block += f"  <em>{authors}</em><br>\n"

    if venue_line:
        block += f"  {venue_line}<br>\n"

    block += f"  <sub>Cité par : {citations}</sub>\n"
    block += "</p>"

    return block

  



def generate_publications_section():
    """
    Récupère les publications Google Scholar et génère le contenu Markdown.
    """
    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author)

    publications = author.get("publications", [])

    publications = sorted(
        publications,
        key=lambda pub: pub.get("num_citations", 0),
        reverse=True,
    )

    selected_publications = publications[:MAX_PUBLICATIONS]

    if not selected_publications:
        return "_Aucune publication trouvée automatiquement._"

    rendered_publications = [
        render_publication(pub)
        for pub in selected_publications
    ]

    footer = (
        f'\n<p><a href="{PROFILE_URL}">'
        "Voir toutes mes publications sur Google Scholar"
        "</a></p>"
    )

    return "\n\n".join(rendered_publications) + footer


def update_readme(publications_section):
    """
    Remplace le contenu situé entre les marqueurs du README.
    """
    with open(README_PATH, "r", encoding="utf-8") as file:
        readme = file.read()

    start_marker = "<!-- GOOGLE-SCHOLAR:START -->"
    end_marker = "<!-- GOOGLE-SCHOLAR:END -->"

    pattern = (
        f"{re.escape(start_marker)}"
        r".*?"
        f"{re.escape(end_marker)}"
    )

    replacement = (
        f"{start_marker}\n"
        f"{publications_section}\n"
        f"{end_marker}"
    )

    updated_readme = re.sub(
        pattern,
        replacement,
        readme,
        flags=re.DOTALL,
    )

    if updated_readme == readme:
        raise RuntimeError(
            "Les marqueurs GOOGLE-SCHOLAR n'ont pas été trouvés dans README.md."
        )

    with open(README_PATH, "w", encoding="utf-8") as file:
        file.write(updated_readme)


def main():
    publications_section = generate_publications_section()
    update_readme(publications_section)
    print("README.md mis à jour avec les publications Google Scholar.")


if __name__ == "__main__":
    main()
