from bs4 import BeautifulSoup
from pathlib import Path
import json
import re

O = Path("output")

R = {
    "finance": {
        "raw_file": "finance_xbrl.html",
        "segment_reporting": {
            "metadata": {},
            "segment_revenue": [],
            "segment_result": [],
            "segment_assets": [],
            "segment_liabilities": []
        }
    },
    "governance": {
        "raw_file": "governance_detail.html",
        "board_of_directors": []
    },
    "shareholding": {
        "raw_file": "shareholding_xbrl.html",
        "shareholding_pattern": []
    },
    "brsr": {
        "raw_file": "brsr_xbrl.html",
        "holding_subsidiary_associate_jv": []
    },
    "cra": [],
    "erp": []
}


# =====================================================
# HELPERS
# =====================================================

def read_html(name):

    p = O / name

    if not p.exists():
        return None

    return p.read_text(
        encoding="utf-8",
        errors="ignore"
    )


def clean(x):

    return re.sub(
        r"\s+",
        " ",
        str(x)
    ).strip()


def to_num(x):

    x = clean(x)

    x = x.replace(",", "")

    if x.startswith("(") and x.endswith(")"):
        x = "-" + x[1:-1]

    try:
        return float(x)
    except:
        return x


def get_tables(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    tables = []

    for table in soup.find_all("table"):

        rows = []

        for tr in table.find_all("tr"):

            cols = [
                clean(
                    td.get_text(
                        " ",
                        strip=True
                    )
                )
                for td in tr.find_all(
                    ["td", "th"]
                )
            ]

            if cols:
                rows.append(cols)

        if rows:
            tables.append(rows)

    return tables


def table_text(table, n=20):

    return " ".join(
        [
            " ".join(r)
            for r in table[:n]
        ]
    ).lower()


def find_table(tables, keywords):

    for table in tables:

        txt = table_text(table)

        ok = True

        for k in keywords:

            if k.lower() not in txt:
                ok = False
                break

        if ok:
            return table

    return None


# =====================================================
# FINANCE
# =====================================================

html = read_html(
    "finance_xbrl.html"
)

if html:

    tables = get_tables(html)

    finance_table = None

    for t in tables:

        txt = table_text(t)

        if (
            "particulars" in txt
            and
            "year to date figures" in txt
            and
            (
                "segment revenue" in txt
                or
                "segment result" in txt
                or
                "segment asset" in txt
                or
                "segment liabilities" in txt
            )
        ):
            finance_table = t
            break

    if finance_table:

        section = None

        for row in finance_table:

            row_text = clean(
                " ".join(row)
            )

            low = row_text.lower()

            if (
                "date of start of reporting period"
                in low
                and len(row) >= 2
            ):
                R["finance"][
                    "segment_reporting"
                ]["metadata"][
                    "period_start"
                ] = row[1]

            elif (
                "date of end of reporting period"
                in low
                and len(row) >= 2
            ):
                R["finance"][
                    "segment_reporting"
                ]["metadata"][
                    "period_end"
                ] = row[1]

            elif (
                "whether results are audited or unaudited"
                in low
                and len(row) >= 2
            ):
                R["finance"][
                    "segment_reporting"
                ]["metadata"][
                    "audit_status"
                ] = row[1]

            elif (
                "nature of report standalone or consolidated"
                in low
                and len(row) >= 2
            ):
                R["finance"][
                    "segment_reporting"
                ]["metadata"][
                    "report_type"
                ] = row[1]

            elif (
                "segment revenue"
                in low
            ):
                section = "segment_revenue"

            elif (
                "segment result"
                in low
            ):
                section = "segment_result"

            elif (
                "segment asset"
                in low
            ):
                section = "segment_assets"

            elif (
                "segment liabilities"
                in low
            ):
                section = "segment_liabilities"

            elif (
                section
                and len(row) >= 4
                and row[0].strip().isdigit()
            ):

                R["finance"][
                    "segment_reporting"
                ][section].append(
                    {
                        "segment":
                            row[1],
                        "current":
                            to_num(
                                row[2]
                            ),
                        "ytd":
                            to_num(
                                row[3]
                            )
                    }
                )
   


# =====================================================
# GOVERNANCE
# =====================================================

html = read_html(
    "governance_detail.html"
)

if html:

    tables = get_tables(html)

    gov_table = None

    for table in tables:

        txt = table_text(
            table,
            50
        )

        if (
            "name of the director" in txt
            and
            "din" in txt
            and
            "category" in txt
        ):
            gov_table = table
            break

    if gov_table:

        header = [
            clean(x).lower()
            for x in gov_table[0]
        ]

        name_idx = None
        din_idx = None
        cat_idx = None

        for i, h in enumerate(header):

            if (
                "name of the director"
                in h
            ):
                name_idx = i

            if (
                h == "din"
                or "din" in h
            ):
                din_idx = i

            if (
                "category"
                in h
            ):
                cat_idx = i

        if (
            name_idx is not None
            and
            din_idx is not None
            and
            cat_idx is not None
        ):

            seen = set()

            for row in gov_table[1:]:

                if len(row) <= max(
                    name_idx,
                    din_idx,
                    cat_idx
                ):
                    continue

                din = clean(
                    row[din_idx]
                )

                if not re.fullmatch(
                    r"\d{8}",
                    din
                ):
                    continue

                name = clean(
                    row[name_idx]
                )

                name = (
                    name
                    .replace("Mr ", "")
                    .replace("Ms ", "")
                    .replace("Mrs ", "")
                    .replace("Dr ", "")
                    .strip()
                )

                key = (
                    name,
                    din
                )

                if key in seen:
                    continue

                seen.add(key)

                R["governance"][
                    "board_of_directors"
                ].append(
                    {
                        "name": name,
                        "din": din,
                        "category": clean(
                            row[cat_idx]
                        )
                    }
                )


# =====================================================
# SHAREHOLDING
# =====================================================

html = read_html(
    "shareholding_xbrl.html"
)

if html:

    tables = get_tables(html)

    share_table = find_table(
        tables,
        [
            "category of shareholder",
            "fully paid up equity shares"
        ]
    )

    if share_table:

        for row in share_table[1:]:

            if len(row) < 4:
                continue

            category = row[1].strip()

            low = category.lower()

            if (
                "category of shareholder"
                in low
                or
                low.startswith(
                    "class eg"
                )
                or
                category == ""
            ):
                continue

            R["shareholding"][
                "shareholding_pattern"
            ].append(
                {
                    "category":
                        category,
                    "shareholders":
                        row[2],
                    "shares":
                        row[3]
                }
            )


# =====================================================
# BRSR
# =====================================================

html = read_html(
    "brsr_xbrl.html"
)

if html:

    tables = get_tables(html)

    brsr_table = find_table(
        tables,
        [
            "holding",
            "subsidiary",
            "associate"
        ]
    )

    if brsr_table:

        seen = set()

        for row in brsr_table[1:]:

            if len(row) < 5:
                continue

            try:

                name = clean(
                    row[1]
                )

                if (
                    name.lower().startswith(
                        "name of"
                    )
                ):
                    continue

                key = (
                    name,
                    row[2]
                )

                if key in seen:
                    continue

                seen.add(key)

                R["brsr"][
                    "holding_subsidiary_associate_jv"
                ].append(
                    {
                        "name":
                            name,
                        "relationship":
                            row[2],
                        "shareholding_percent":
                            to_num(
                                row[3]
                            ),
                        "participates_in_br":
                            row[4]
                    }
                )

            except:
                pass

# =====================================================
# CRA
# =====================================================

html = read_html(
    "cra_table.html"
)

if html:

    tables = get_tables(html)

    cra_table = find_table(
        tables,
        [
            "credit rating agency"
        ]
    )

    if cra_table:

        header = cra_table[0]

        seen = set()

        for row in cra_table[1:]:

            if len(row) != len(header):
                continue

            item = dict(
                zip(
                    header,
                    row
                )
            )

            key = (
                item.get(
                    "Credit Rating Agency Name",
                    ""
                ),
                item.get(
                    "Credit Rating (actual rating provided)",
                    ""
                ),
                item.get(
                    "Outlook (actual outlook to be provided)",
                    ""
                ),
                item.get(
                    "Date of Current Credit Rating / Outlook",
                    ""
                ),
                item.get(
                    "Rating Assigned on (details of instrument)",
                    ""
                )
            )

            if key in seen:
                continue

            seen.add(key)

            R["cra"].append(
                item
            )


# =====================================================
# ERP
# =====================================================

html = read_html(
    "erp_table.html"
)

if html:

    tables = get_tables(html)

    for table in tables:

        txt = table_text(table)

        if (
            "erp" in txt
            or
            "intermediary" in txt
        ):

            header = table[0]

            for row in table[1:]:

                if len(row) != len(header):
                    continue

                R["erp"].append(
                    dict(
                        zip(
                            header,
                            row
                        )
                    )
                )

            break


# =====================================================
# SAVE
# =====================================================

out = O / "company_data.json"

with open(
    out,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        R,
        f,
        indent=4,
        ensure_ascii=False
    )

print(
    json.dumps(
        R,
        indent=4,
        ensure_ascii=False
    )
)

print(
    "\nSaved:",
    out
)