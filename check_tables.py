from bs4 import BeautifulSoup

for f in [
    "finance_xbrl.html",
    "shareholding_xbrl.html",
    "brsr_xbrl.html"
]:

    html = open(
        "output/" + f,
        encoding="utf-8",
        errors="ignore"
    ).read()

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    print("\n" + "=" * 50)
    print(f)
    print("=" * 50)

    tables = soup.find_all("table")

    print("TABLE COUNT =", len(tables))

    for i, t in enumerate(tables[:10]):

        txt = t.get_text(
            " ",
            strip=True
        )

        print(
            f"\nTABLE {i}"
        )

        print(
            txt[:300]
        )
        