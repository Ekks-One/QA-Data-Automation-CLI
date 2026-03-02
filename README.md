# QA-Data-Automation-CLI
CLI tool for ingesting, validating, deduplicating, and reporting QA datasets using MongoDB.

A Python-based command-line tool for ingesting, validating, deduplicating, and reporting QA datasets using MongoDB.

This tool processes structured QA test reports from multiple releases (Fall/Spring builds), merges them into MongoDB collections, and generates filtered reports without duplicates.

---

## Features

- Excel → CSV ingestion into MongoDB
- Data validation and schema enforcement
- Duplicate detection across multiple datasets
- Automated CSV report generation
- Command-line filtering using `argparse`
- MongoDB querying with regex-based filters

---

## Tech Stack

- Python
- MongoDB
- Pandas
- Argparse
- PyMongo
- CSV

---

## How It Works

1. Load two Excel QA datasets (Fall + Spring builds)
2. Convert to CSV for structured ingestion
3. Insert data into separate MongoDB collections
4. Validate rows:
   - Required fields present
   - Correct date formatting
   - Proper numeric test identifiers
   - Valid boolean flags (Repeatable / Blocker)
5. Perform cross-collection duplicate detection
6. Generate filtered reports programmatically

---

## Usage

### Fill Database

```bash
python script.py --verbose --fill databases Fall2025.xlsx Spring2025.xlsx
```

### Show Repeatable Bugs

```bash
python script.py --verbose --repeat
```

### Show Blocker Bugs

```bash
python script.py --verbose --blocker
```

### Show Repeatable AND Blocker Bugs

```bash
python script.py --verbose --repeat --blocker
```

### Filter by Test Owner

```bash
python script.py --verbose --user "Kevin Chaja"
```

### Filter by Build Date

```bash
python script.py --verbose --date 02/24/2024
```

---

## Duplicate Prevention Strategy

Duplicates are prevented by generating a composite key from:

- Build #
- Category
- Test Case
- Expected Result
- Actual Result

Each field is normalized to ensure:
- Case-insensitive matching
- Whitespace normalization
- Cross-dataset deduplication

---

## Generated Reports

The tool generates structured CSV reports such as:

- `repeatable.csv`
- `blocker.csv`
- `repeatable&blocker.csv`
- `date.csv`
- User-specific exports

All reports are deduplicated across both collections.

---

## Resume Summary

Engineered a CLI-based QA automation tool that ingests multi-release datasets into MongoDB, enforces validation rules, prevents cross-build duplication, and generates structured QA reports programmatically.

---

## 🔮 Future Improvements

- Add aggregation pipelines for advanced analytics
- Add Docker containerization
- Add unit testing suite
- Add structured logging
- Expose as REST API
