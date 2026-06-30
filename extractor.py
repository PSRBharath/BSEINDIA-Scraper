from bs4 import BeautifulSoup
from pathlib import Path
import json
import re
import sys

BASE_OUTPUT = Path("output")

COMPANY = input("Company Name: ").strip()

company_folder = BASE_OUTPUT / COMPANY

WARNINGS = []

R = {

    "finance": {
        "chapter": 7,
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
        "chapter": 15,
        "raw_file": "governance_detail.html",
        "board_of_directors": []
    },

    "shareholding": {
        "chapter": 17,
        "raw_file": "shareholding_xbrl.html",
        "shareholding_pattern": [],
        "shareholding_pattern_detailed": []
    },

    "brsr": {
        "chapter": 13,
        "raw_file": "brsr_xbrl.html",
        "holding_subsidiary_associate_jv": []
    },

    "credit_information": {
        "chapter": 24,

        "cra": [],

        "erp": [],

        "credit_rating_details": {
            "status": "empty",
            "raw_file": "credit_rating.csv",
            "data": []
        }
    }
}


# =====================================================
# HELPERS
# =====================================================

def read_html(name):

    p = company_folder / name

    if not p.exists():
        warn(f"Missing input file: {p}")
        return None

    return p.read_text(
        encoding="utf-8",
        errors="ignore"
    )


def warn(message):

    WARNINGS.append(message)
    print(f"[WARN] {message}", file=sys.stderr)


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
    except ValueError:
        return x


def norm(x):

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        clean(x).lower()
    ).strip()


def norm_compact(x):

    return re.sub(
        r"[^a-z0-9]+",
        "",
        clean(x).lower()
    )


def looks_numbered(value):

    return bool(
        re.fullmatch(
            r"\s*\(?\d+[.)]?\s*",
            clean(value)
        )
    )


def strip_numbering(row):

    data = row[:]

    if data and looks_numbered(data[0]):
        data = data[1:]

    while data and not clean(data[0]):
        data = data[1:]

    return data


def build_header_map(rows, required_terms, scan_rows=8):

    required = [
        norm_compact(x)
        for x in required_terms
    ]

    for idx, row in enumerate(rows[:scan_rows]):

        header = [
            norm_compact(x)
            for x in row
        ]

        joined = " ".join(header)

        if all(term in joined for term in required):
            return idx, header

    return None, []


def find_col(header, *needles):

    normalized = [
        norm_compact(x)
        for x in needles
    ]

    for i, h in enumerate(header):

        if any(n in h for n in normalized):
            return i

    return None


def value_at(row, idx, default=""):

    if idx is None or idx >= len(row):
        return default

    return clean(row[idx])


def first_item_value(item, include, exclude=()):

    includes = [
        norm_compact(x)
        for x in include
    ]
    excludes = [
        norm_compact(x)
        for x in exclude
    ]

    for key, value in item.items():

        normalized = norm_compact(key)

        if (
            all(x in normalized for x in includes)
            and not any(x in normalized for x in excludes)
        ):
            return value

    return ""


def strip_director_title(name):

    return re.sub(
        r"^(mr|mrs|ms|dr|shri|smt|prof)\.?\s+",
        "",
        clean(name),
        flags=re.IGNORECASE
    ).strip()


def clean_din(value):

    digits = re.sub(
        r"\D",
        "",
        clean(value)
    )

    if 1 <= len(digits) <= 8:
        return digits.zfill(8)

    return ""


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

#     soup = BeautifulSoup(
#         html,
#         "html.parser"
#     )

#     tables = []

#     for table in soup.find_all("table"):

#         rows = []

#         rowspan_map = {}

#         trs = table.find_all("tr")

#         for r, tr in enumerate(trs):

#             row = []

#             col_pos = 0

#             while (
#                 col_pos in rowspan_map
#                 and rowspan_map[col_pos]["rows"] > 0
#             ):
#                 row.append(
#                     rowspan_map[col_pos]["value"]
#                 )

#                 rowspan_map[col_pos]["rows"] -= 1

#                 if (
#                     rowspan_map[col_pos]["rows"]
#                     == 0
#                 ):
#                     del rowspan_map[col_pos]

#                 col_pos += 1

#             cells = tr.find_all(
#                 ["td", "th"]
#             )

#             for cell in cells:

#                 while (
#                     col_pos in rowspan_map
#                     and rowspan_map[col_pos]["rows"] > 0
#                 ):
#                     row.append(
#                         rowspan_map[col_pos]["value"]
#                     )

#                     rowspan_map[col_pos]["rows"] -= 1

#                     if (
#                         rowspan_map[col_pos]["rows"]
#                         == 0
#                     ):
#                         del rowspan_map[col_pos]

#                     col_pos += 1

#                 text = clean(
#                     cell.get_text(
#                         " ",
#                         strip=True
#                     )
#                 )

#                 colspan = int(
#                     cell.get(
#                         "colspan",
#                         1
#                     )
#                 )

#                 rowspan = int(
#                     cell.get(
#                         "rowspan",
#                         1
#                     )
#                 )

#                 for offset in range(
#                     colspan
#                 ):

#                     row.append(text)

#                     if rowspan > 1:

#                         rowspan_map[
#                             col_pos + offset
#                         ] = {
#                             "value": text,
#                             "rows": rowspan - 1
#                         }

#                 col_pos += colspan

#             while True:

#                 if (
#                     col_pos not in rowspan_map
#                 ):
#                     break

#                 if (
#                     rowspan_map[col_pos]["rows"]
#                     <= 0
#                 ):
#                     del rowspan_map[col_pos]
#                     continue

#                 row.append(
#                     rowspan_map[col_pos]["value"]
#                 )

#                 rowspan_map[col_pos]["rows"] -= 1

#                 if (
#                     rowspan_map[col_pos]["rows"]
#                     == 0
#                 ):
#                     del rowspan_map[col_pos]

#                 col_pos += 1

#             if row:
#                 rows.append(row)

#         if rows:
#             tables.append(rows)

#     return tables

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
                and len(row) >= 3
            ):

                data = strip_numbering(row)

                if len(data) < 3:
                    continue

                first = norm(data[0])

                if (
                    "particular" in first
                    or "year to date" in first
                    or "quarter" in first
                    or first == "total"
                ):
                    continue

                R["finance"][
                    "segment_reporting"
                ][section].append(
                    {
                        "segment":
                            data[0],
                        "current":
                            to_num(
                                data[1]
                            ),
                        "ytd":
                            to_num(
                                data[2]
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

        header_idx, header = build_header_map(
            gov_table,
            [
                "director",
                "din",
                "category"
            ],
            scan_rows=10
        )

        if (
            header_idx is not None
            and
            header_idx + 1 < len(gov_table)
        ):

            row1 = [
                norm_compact(x)
                for x in gov_table[header_idx]
            ]

            row2 = [
                norm_compact(x)
                for x in gov_table[header_idx + 1]
            ]

            header = []

            i2 = 0

            for i, h in enumerate(row1):

                if i == 5:
                    parent = h

                    while i2 < len(row2):

                        child = row2[i2]

                        header.append(
                            f"{parent}_{child}"
                        )

                        i2 += 1

                    continue

                header.append(h)

        def value_at(row, idx):

            if idx is None:
                return None

            if idx >= len(row):
                return None

            return clean(row[idx])

        name_idx = find_col(
            header,
            "nameofthedirector",
            "directorname"
        )

        din_idx = find_col(
            header,
            "din"
        )

        cat_idx = find_col(
            header,
            "category"
        )

        disqualified_idx = find_col(
            header,
            "whetherthedirectorisdisqualified"
        )

        disq_start_idx = find_col(
            header,
            "startdateofdisqualification"
        )

        disq_end_idx = find_col(
            header,
            "enddateofdisqualification"
        )

        disq_details_idx = find_col(
            header,
            "detailsofdisqualification"
        )

        status_idx = find_col(
            header,
            "currentstatus"
        )

        special_resolution_idx = find_col(
            header,
            "whetherspecialresolutionpassed"
        )

        special_resolution_date_idx = find_col(
            header,
            "dateofpassingspecialresolution"
        )

        initial_appointment_idx = find_col(
            header,
            "initialdateofappointment"
        )

        reappointment_idx = find_col(
            header,
            "dateofreappointment"
        )

        cessation_date_idx = find_col(
            header,
            "dateofcessation"
        )

        tenure_idx = find_col(
            header,
            "tenureofdirector"
        )

        directorships_idx = find_col(
            header,
            "noofdirectorship"
        )

        independent_directorships_idx = find_col(
            header,
            "noofindependentdirectorship"
        )

        audit_membership_idx = find_col(
            header,
            "numberofmembershipsinaudit"
        )

        audit_chair_idx = find_col(
            header,
            "noofpostofchairperson"
        )

        reason_idx = find_col(
            header,
            "reasonforcessation"
        )

        pan_note_idx = find_col(
            header,
            "notesfornotprovidingpan"
        )

        din_note_idx = find_col(
            header,
            "notesfornotprovidingdin"
        )

        if (
            name_idx is not None
            and
            din_idx is not None
            and
            cat_idx is not None
        ):

            seen = set()

            for row in gov_table[header_idx + 2:]:

                if len(row) <= max(
                    name_idx,
                    din_idx,
                    cat_idx
                ):
                    continue

                din = clean_din(
                    row[din_idx]
                )

                if not din:
                    continue

                name = strip_director_title(
                    row[name_idx]
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
                        "category": value_at(
                            row,
                            cat_idx
                        ),

                        "disqualified": value_at(
                            row,
                            disqualified_idx
                        ),

                        "disqualification_start": value_at(
                            row,
                            disq_start_idx
                        ),

                        "disqualification_end": value_at(
                            row,
                            disq_end_idx
                        ),

                        "disqualification_details": value_at(
                            row,
                            disq_details_idx
                        ),

                        "current_status": value_at(
                            row,
                            status_idx
                        ),

                        "special_resolution_passed": value_at(
                            row,
                            special_resolution_idx
                        ),

                        "special_resolution_date": value_at(
                            row,
                            special_resolution_date_idx
                        ),

                        "initial_appointment_date": value_at(
                            row,
                            initial_appointment_idx
                        ),

                        "reappointment_date": value_at(
                            row,
                            reappointment_idx
                        ),

                        "cessation_date": value_at(
                            row,
                            cessation_date_idx
                        ),

                        "tenure_months": value_at(
                            row,
                            tenure_idx
                        ),

                        "listed_directorships": value_at(
                            row,
                            directorships_idx
                        ),

                        "independent_directorships": value_at(
                            row,
                            independent_directorships_idx
                        ),

                        "audit_committee_memberships": value_at(
                            row,
                            audit_membership_idx
                        ),

                        "audit_committee_chairmanships": value_at(
                            row,
                            audit_chair_idx
                        ),

                        "reason_for_cessation": value_at(
                            row,
                            reason_idx
                        ),

                        "pan_notes": value_at(
                            row,
                            pan_note_idx
                        ),

                        "din_notes": value_at(
                            row,
                            din_note_idx
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
    print("\n" + "=" * 60)
    print("SHAREHOLDING SECTION")
    print("=" * 60)

    print("\nHTML PREVIEW:")
    print(html[:500])

    tables = get_tables(html)
    print("\n\nSEARCHING FOR DETAILED SHAREHOLDING TABLE")

    detail_table = None

    for idx, table in enumerate(tables):

        txt = table_text(
            table,
            50
        ).lower()

        if "category & name of the shareholders" in txt:

            print("\nFOUND DETAILED TABLE:", idx)

            detail_table = table

            break

    print(
        "DETAIL TABLE FOUND =",
        detail_table is not None
    )

    if detail_table:

        print("\nFIRST 20 ROWS OF DETAILED TABLE")

        for i, row in enumerate(detail_table[:20]):

            print("\nROW", i)
            print("LEN =", len(row))
            print(row)
        print("\nTOTAL TABLES:", len(tables))

    for i, table in enumerate(tables[:10]):
        print(f"\nTABLE {i}")

        try:
            print(
                table_text(
                    table,
                    20
                )[:500]
            )
        except Exception as e:
            print(
                "TABLE PREVIEW ERROR:",
                e
            )

    share_table = find_table(
        tables,
        [
            "category of shareholder",
            "fully paid up equity shares"
        ]
    )

    print(
        "\nSHARE TABLE FOUND:",
        share_table is not None
    )

    if share_table:
        print("\nSELECTED TABLE PREVIEW:")

        try:
            print(
                table_text(
                    share_table,
                    40
                )
            )
        except Exception as e:
            print(
                "PREVIEW ERROR:",
                e
            )

        header_idx, header = build_header_map(
            share_table,
            [
                "category"
            ],
            scan_rows=10
        )

        print("\n=== SHARE HEADER ===")
        print(
            "HEADER IDX:",
            header_idx
        )

        for i, h in enumerate(header):
            print(
                i,
                repr(h)
            )

        print("\nFIRST 5 SHARE ROWS")

        for i, row in enumerate(share_table[:5]):
            print(
                "\nROW",
                i
            )
            print(row)

        category_idx = find_col(
            header,
            "categoryofshareholder",
            "categoryshareholder"
        )

        shareholders_idx = find_col(
            header,
            "nosofshareholders",
            "noofshareholders",
            "numberofshareholders"
        )

        shares_idx = find_col(
            header,
            "fullypaidupequityshares",
            "noofsharesheld",
            "numberofsharesheld"
        )

        depository_idx = find_col(
            header,
            "depositoryreceipts"
        )

        total_shares_idx = find_col(
            header,
            "totalnossharesheld"
        )

        shareholding_pct_idx = find_col(
            header,
            "shareholdingasaoftotalnoofshares"
        )

        voting_rights_idx = find_col(
            header,
            "numberofvotingrightsheld"
        )

        diluted_total_idx = find_col(
            header,
            "totalnoofsharesonfullydilutedbasis"
        )

        diluted_pct_idx = find_col(
            header,
            "assumingfullconversion"
        )

        demat_idx = find_col(
            header,
            "equitysharesheldindematerializedform"
        )

        subcat_idx = find_col(
            header,
            "subcategorizationofshares"
        )

        print("\nCOLUMN INDEXES")
        print(
            "category_idx =",
            category_idx
        )
        print(
            "shareholders_idx =",
            shareholders_idx
        )
        print(
            "shares_idx =",
            shares_idx
        )

        print("\nSHARE TABLE ROW COUNT =", len(share_table))

        for i, row in enumerate(share_table):
            print(
                "ROW",
                i,
                "LEN=",
                len(row)
            )

        start = header_idx + 3

        for row in share_table[start:]:
            print("\nRAW ROW:", row[:5])

            if len(row) < 3:
                print("SKIP: len < 3")
                continue

            category = value_at(
                row,
                category_idx
            )

            shareholders = value_at(
                row,
                shareholders_idx
            )

            print(
                "CATEGORY=",
                repr(category),
                "SHAREHOLDERS=",
                repr(shareholders)
            )

            if not category:
                print("SKIP: no category")
                continue

            low = category.lower()

            if (
                "category of shareholder" in low
                or low.startswith("class eg")
            ):
                print("SKIP: header row")
                continue

            print("ADDING:", category)

            R["shareholding"][
                "shareholding_pattern"
            ].append(
                {
                    "category": category,
                    "shareholders": shareholders,
                    "fully_paid_equity_shares": value_at(row, 3),
                    "shares_underlying_depository_receipts": value_at(row, 5),
                    "total_shares_held": value_at(row, 6),
                    "shareholding_percent": value_at(row, 7),
                    "voting_rights": value_at(row, 8),
                    "total_voting_rights": value_at(row, 10),
                    "voting_rights_percent": value_at(row, 11),
                    "dematerialized_shares": value_at(row, 16),
                    "subcategory_i": value_at(row, 29),
                    "subcategory_ii": value_at(row, 30),
                    "subcategory_iii": value_at(row, 31)
                }
            )
        
# =====================================================
# SHAREHOLDING - DETAILED
# =====================================================

detail_table = None

for table in tables:

    txt = table_text(
        table,
        50
    ).lower()

    if (
        "category & name of the shareholders" in txt
        and
        "shareholder type" in txt
    ):
        detail_table = table
        break

if detail_table:

    print("\nDETAILED SHAREHOLDING TABLE FOUND")

    for row in detail_table[3:]:

        if len(row) < 2:
            continue

        shareholder_name = clean(
            value_at(row, 1)
        )

        if not shareholder_name:
            continue

        low = shareholder_name.lower()

        # Skip section/category rows
        if (
            low.startswith("table ")
            or low.startswith("sub-total")
            or low.startswith("total shareholding")
            or low == "indian"
            or low == "foreign"
        ):
            continue

        # Keep only rows with actual holdings
        # if (
        #     not value_at(row, 6)
        #     and not value_at(row, 9)
        # ):
        #     continue

        R["shareholding"][
            "shareholding_pattern_detailed"
        ].append(
            {
                "serial_no": value_at(row, 0),

                "shareholder_name": shareholder_name,

                "category": value_at(row, 2),

                "category_more_than_1_percent": value_at(row, 3),

                "bank_name": value_at(row, 4),

                "shareholders": value_at(row, 5),

                "fully_paid_equity_shares": value_at(row, 6),

                "partly_paid_equity_shares": value_at(row, 7),

                "depository_receipts": value_at(row, 8),

                "total_shares_held": value_at(row, 9),

                "shareholding_percent": value_at(row, 10),

                "voting_rights_class_x": value_at(row, 11),

                "voting_rights_class_y": value_at(row, 12),

                "total_voting_rights": value_at(row, 13),

                "voting_rights_percent": value_at(row, 14),

                "outstanding_convertible_securities": value_at(row, 15),

                "outstanding_warrants": value_at(row, 16),

                "outstanding_esop": value_at(row, 17),

                "total_underlying_convertible_warrants_esop": value_at(row, 18),

                "fully_diluted_total_shares": value_at(row, 19),

                "fully_diluted_shareholding_percent": value_at(row, 20),

                "locked_in_shares": value_at(row, 21),

                "locked_in_shares_percent": value_at(row, 22),

                "pledged_shares": value_at(row, 23),

                "pledged_shares_percent": value_at(row, 24),

                "non_disposal_undertaking_shares": value_at(row, 25),

                "non_disposal_undertaking_percent": value_at(row, 26),

                "other_encumbrances_shares": value_at(row, 27),

                "other_encumbrances_percent": value_at(row, 28),

                "total_encumbered_shares": value_at(row, 29),

                "total_encumbered_shares_percent": value_at(row, 30),

                "dematerialized_shares": value_at(row, 31),

                "subcategory_i": value_at(row, 32),

                "subcategory_ii": value_at(row, 33),

                "subcategory_iii": value_at(row, 34),

                "shareholder_type": value_at(row, 35)
            }
        )

    print(
        "DETAILED SHAREHOLDERS:",
        len(
            R["shareholding"][
                "shareholding_pattern_detailed"
            ]
        )
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

        header_idx, header = build_header_map(
            brsr_table,
            [
                "name",
                "subsidiary",
                "associate"
            ],
            scan_rows=10
        )

        name_idx = find_col(
            header,
            "nameoftheholding",
            "nameofholding",
            "nameofentity",
            "name"
        )
        relationship_idx = find_col(
            header,
            "holdingsubsidiaryassociatejointventure",
            "holdingsubsidiaryassociate",
            "relationship"
        )
        share_idx = find_col(
            header,
            "percentageofsharesheld",
            "shareholding"
        )
        participates_idx = find_col(
            header,
            "participatesinbusinessresponsibility",
            "participatesinbr"
        )

        seen = set()

        start = header_idx + 1 if header_idx is not None else 1

        for row in brsr_table[start:]:

            if len(row) < 4:
                continue

            try:

                if name_idx is None:
                    data = strip_numbering(row)
                    name = value_at(data, 0)
                    relationship = value_at(data, 1)
                    shareholding_percent = value_at(data, 2)
                    participates_in_br = value_at(data, 3)
                else:
                    name = value_at(row, name_idx)
                    relationship = value_at(row, relationship_idx)
                    shareholding_percent = value_at(row, share_idx)
                    participates_in_br = value_at(row, participates_idx)

                if (
                    name.lower().startswith(
                        "name of"
                    )
                ):
                    continue

                key = (
                    name,
                    relationship
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
                            relationship,
                        "shareholding_percent":
                            to_num(
                                shareholding_percent
                            ),
                        "participates_in_br":
                            participates_in_br
                    }
                )

            except (IndexError, TypeError, ValueError) as e:
                warn(f"BRSR row skipped: {e}; row={row}")

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

        header_idx, header = build_header_map(
            cra_table,
            [
                "credit rating agency"
            ],
            scan_rows=10
        )

        if header_idx is None:
            header_idx = 0
            header = cra_table[0]

        seen = set()

        for row in cra_table[header_idx + 1:]:

            if len(row) < len(header):
                continue

            row = row[:len(header)]

            item = dict(
                zip(
                    header,
                    row
                )
            )

            key = (
                first_item_value(item, ["agency"]),
                first_item_value(item, ["rating"], ["agency", "outlook"]),
                first_item_value(item, ["outlook"], ["rating"]),
                first_item_value(item, ["date"]),
                first_item_value(item, ["instrument"])
            )

            if key in seen:
                continue

            seen.add(key)

            R["credit_information"]["cra"].append(item)


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

            header_idx, header = build_header_map(
                table,
                [
                    "erp"
                ],
                scan_rows=10
            )

            if header_idx is None:
                header_idx = 0
                header = table[0]

            for row in table[header_idx + 1:]:

                if len(row) < len(header):
                    continue

                row = row[:len(header)]

                R["credit_information"]["erp"].append(
    dict(
        zip(
            header,
            row
        )
    )
)

            break


credit_file = company_folder / "credit_rating.json"

if credit_file.exists():

    with open(credit_file, "r", encoding="utf-8") as f:

        R["credit_information"]["credit_rating_details"] = json.load(f)

# =====================================================
# SAVE
# =====================================================

company_folder.mkdir(
    parents=True,
    exist_ok=True
)

out = company_folder / "company_data.json"

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

# print(
#     json.dumps(
#         R,
#         indent=4,
#         ensure_ascii=False
#     )
# )

print(
    "\nSaved:",
    out
)
