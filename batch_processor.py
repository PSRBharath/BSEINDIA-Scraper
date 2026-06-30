from concurrent.futures import ProcessPoolExecutor, as_completed
import subprocess
import os
import time
import sys

with open("companies.txt", "r") as f:
    companies = [
        line.strip()
        for line in f
        if line.strip()
    ]

# Number of parallel workers
# Adjust depending on your machine.
# For your current laptop (8 GB RAM), start with 3.
MAX_WORKERS = min(3, len(companies))


def process_company(company):
    start = time.time()

    try:
        print(f"\n[{company}] Harvester Started")

        subprocess.run(
            [
                sys.executable,
                "bse_harvester.py",
                company
            ],
            check=True
        )

        print(f"[{company}] Harvester Finished")

        print(f"[{company}] Extractor Started")

        subprocess.run(
            [
                sys.executable,
                "extractor.py",
                company
            ],
            check=True
        )

        print(f"[{company}] Extractor Finished")

        elapsed = round(time.time() - start, 2)

        return (
            company,
            "SUCCESS",
            elapsed,
            None
        )

    except Exception as e:

        elapsed = round(time.time() - start, 2)

        return (
            company,
            "FAILED",
            elapsed,
            str(e)
        )


if __name__ == "__main__":

    overall_start = time.time()

    results = []

    print("=" * 70)
    print("Starting Batch Processing")
    print(f"Companies : {len(companies)}")
    print(f"Workers   : {MAX_WORKERS}")
    print("=" * 70)

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = {
            executor.submit(process_company, company): company
            for company in companies
        }

        for future in as_completed(futures):

            company, status, elapsed, error = future.result()

            results.append(
                (
                    company,
                    status,
                    elapsed,
                    error
                )
            )

            if status == "SUCCESS":

                print(f"✓ {company} completed in {elapsed}s")

            else:

                print(f"✗ {company} failed")
                print(error)

    total_time = round(time.time() - overall_start, 2)

    success = sum(1 for r in results if r[1] == "SUCCESS")
    failed = len(results) - success

    print("\n")
    print("=" * 70)
    print("Batch Summary")
    print("=" * 70)

    for company, status, elapsed, _ in sorted(results):

        print(
            f"{company:<20} {status:<10} {elapsed:>8}s"
        )

    print("=" * 70)
    print(f"Total Companies : {len(companies)}")
    print(f"Successful      : {success}")
    print(f"Failed          : {failed}")
    print(f"Total Time      : {total_time}s")
    print("=" * 70)