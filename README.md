# GCD Schema Analysis for Comic-Analysis Integration

This repository contains a comprehensive analysis of the Grand Comics Database (GCD) schema to support integration with the [Comic-Analysis](https://github.com/RichardScottOZ/Comic-Analysis) project.

## Purpose

Analyze and document the GCD database structure to enable extraction of:
- **Creator attribution** (writers, artists, inkers, colorists, letterers, editors)
- **Storyline information** (titles, synopses, character appearances)
- **Comic metadata** (publishers, series, publication dates, age ratings)
- **Genre and type classification** (superhero, horror, sci-fi, etc.)
- **Paratext identification** (covers, ads, credits pages, etc.)

## Documentation

### Core Schema Documentation

1. **[GCD_SCHEMA_OVERVIEW.md](GCD_SCHEMA_OVERVIEW.md)**
   - Complete overview of GCD database structure
   - Data access methods (database dumps vs. API)
   - Detailed table descriptions
   - Query patterns for common operations

2. **[GCD_ENTITY_RELATIONSHIPS.md](GCD_ENTITY_RELATIONSHIPS.md)**
   - Entity-relationship diagrams
   - Table relationships and foreign keys
   - Many-to-many junction tables
   - Data integrity constraints

3. **[COMIC_ANALYSIS_MAPPING.md](COMIC_ANALYSIS_MAPPING.md)**
   - Maps GCD schema to Comic-Analysis project needs
   - Integration strategies
   - Data export formats
   - Use cases for enhanced analysis

4. **[SQL_EXAMPLES.md](SQL_EXAMPLES.md)**
   - Practical SQL queries for data extraction
   - Creator attribution queries
   - Storyline and character tracking
   - Performance optimization tips

### Code

5. **[gcd_extractor.py](gcd_extractor.py)**
   - Python utility for GCD data extraction
   - Filename parsing for comic files
   - Batch processing support
   - Hybrid GCD/VLM extraction strategy

## Quick Start

### 1. Get the GCD Database

Download the latest database dump:
```bash
# Download (bi-monthly updates)
wget https://www.comics.org/download/current_dump.sql.bz2

# Extract
bunzip2 current_dump.sql.bz2

# Import to MySQL/MariaDB
mysql -u root -p -e "CREATE DATABASE gcd CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
mysql -u root -p gcd < current_dump.sql

# OR convert to SQLite (more portable)
mysql2sqlite current_dump.sql | sqlite3 gcd.db
```

### 2. Install Dependencies

```bash
pip install sqlalchemy pymysql  # For MySQL
# OR
pip install sqlalchemy            # For SQLite
```

### 3. Extract Data

```python
from gcd_extractor import GCDExtractor, FilenameParser

# Initialize extractor
extractor = GCDExtractor(connection_string='sqlite:///gcd.db')

# Parse a comic filename
parser = FilenameParser()
parsed = parser.parse('Amazing Spider-Man 001 (1963).cbz')

# Find the issue
issue = extractor.get_issue_by_series_and_number(
    parsed['series_name'], 
    parsed['issue_number']
)

# Get creator credits
if issue:
    credits = extractor.get_issue_credits(issue.issue_id)
    for credit in credits:
        print(f"{credit.creator_name} - {credit.role}")
```

### 4. Batch Process Collection

```python
# Process entire comic collection
from pathlib import Path

comic_files = list(Path("/comics").rglob("*.cb[rz]"))
results = extractor.batch_extract(comic_files, 'gcd_metadata.json')

print(f"Matched: {sum(1 for r in results if r['matched'])}/{len(results)}")
```

## Key GCD Tables

### Publisher Hierarchy
```
Publisher → Series → Issue → Story
```

### Creator Attribution
```
Creator → CreatorNameDetail → StoryCredit → Story
                              ↓
                         CreditType (script, pencils, inks, etc.)
```

### Character Tracking
```
Character → CharacterNameDetail → StoryCharacter → Story
```

## Integration with Comic-Analysis

### Current Comic-Analysis Pipeline
1. Comic file → Page images
2. VLM text extraction
3. Fast-RCNN panel detection
4. DataSpec integration
5. Multimodal embedding generation

### Enhanced Pipeline with GCD
1. Comic file → **GCD metadata lookup** (new)
2. Page images + **creator/storyline info** (enhanced)
3. VLM text extraction + **GCD character list** (validation)
4. Fast-RCNN panel detection
5. DataSpec + **GCD metadata** (enriched)
6. Multimodal embedding generation + **creator/genre features** (enhanced)

### Future Work Support

This GCD analysis directly supports Comic-Analysis future work:

1. **Paratext Classification**
   - Use GCD `story_type` as ground truth labels
   - Train Page Stream Segmentation (PSS) with GCD supervision

2. **Character Reidentification**
   - Link visual detections to GCD canonical character IDs
   - Track characters across issues using GCD appearance data

3. **Creator Attribution**
   - Assign creators to extracted pages/panels
   - Support ~40K comic collection with GCD database

4. **Storyline Assignment**
   - Enrich embeddings with GCD synopses and character lists
   - Enable storyline-aware search

5. **Age Rating & Filtering**
   - Use GCD age ratings for content filtering
   - Organize by publisher/era using GCD metadata

## Hybrid Extraction Strategy

Following recommendations from Comic-Analysis documentation:

### Level 1: GCD Database (Fast, Free)
- Query local GCD database
- Extract all available metadata
- ~100-200 comics/second

### Level 2: VLM Fallback (Slow, Costly)
- For comics not in GCD
- Extract first 5 pages
- Use VLM to get creator info from credits page

### Level 3: Manual Review
- Log failures for manual processing
- Prioritize by importance

## Example Queries

### Get Creator Credits
```sql
SELECT 
    c.gcd_official_name AS creator_name,
    ct.name AS role
FROM gcd_storycredit sc
JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
JOIN gcd_creator c ON cnd.creator_id = c.id
JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
JOIN gcd_story s ON sc.story_id = s.id
WHERE s.issue_id = ?
  AND s.type_id = (SELECT id FROM gcd_storytype WHERE name = 'comic story')
ORDER BY ct.sort_code;
```

### Get Storyline Info
```sql
SELECT 
    s.title,
    s.feature,
    s.genre,
    s.characters,
    s.synopsis
FROM gcd_story s
WHERE s.issue_id = ?
  AND s.type_id = (SELECT id FROM gcd_storytype WHERE name = 'comic story')
ORDER BY s.sequence_number;
```

## Data Export Format

Recommended JSON structure for Comic-Analysis integration:

```json
{
  "comic_file": "Amazing_Spider-Man_001.cbz",
  "gcd_issue_id": 12345,
  "creators": {
    "script": ["Stan Lee"],
    "pencils": ["Steve Ditko"],
    "inks": ["Steve Ditko"]
  },
  "storylines": [{
    "title": "Spider-Man",
    "feature": "Spider-Man",
    "genre": ["superhero", "science fiction"],
    "characters": ["Spider-Man", "Uncle Ben", "Aunt May"],
    "synopsis": "Origin story of Spider-Man..."
  }],
  "metadata": {
    "publisher": "Marvel Comics",
    "series": "Amazing Spider-Man",
    "issue_number": "1",
    "publication_date": "1963-03",
    "age_rating": "Comics Code Authority"
  }
}
```

## Project Context

### From Comic-Analysis README
- **Dataset:** ~330K Calibre pages, ~805K Amazon pages
- **Model:** Closure Lite multimodal fusion framework
- **Embeddings:** 384-dimensional, Zarr format
- **Goal:** Queryable embeddings for visual + text + reading order

### From Comic-Databases.md Research
- Hybrid approach recommended: GCD database + VLM fallback
- GCD provides comprehensive, free, community-vetted data
- Full database dumps eliminate API rate limits
- Ideal for large-scale batch processing

## References

- **GCD Official Site:** https://www.comics.org/
- **GCD Database Downloads:** https://www.comics.org/download/
- **GCD Django Repository:** https://github.com/RichardScottOZ/gcd-django
- **GCD API Documentation:** https://github.com/GrandComicsDatabase/gcd-django/wiki/API
- **Comic-Analysis Project:** https://github.com/RichardScottOZ/Comic-Analysis
- **Comic-Analysis Future Work:** https://github.com/RichardScottOZ/Comic-Analysis/tree/main/documentation/future_work

## Contributing

This is an analysis repository. For:
- **GCD data issues:** Report to https://www.comics.org/
- **GCD Django code:** Contribute to https://github.com/GrandComicsDatabase/gcd-django
- **Comic-Analysis project:** See https://github.com/RichardScottOZ/Comic-Analysis

## License

GCD database is available under Creative Commons Attribution license.
See https://www.comics.org/privacy/ for details.

This analysis and extraction code is provided for research and personal use.
