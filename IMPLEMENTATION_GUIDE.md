# Implementation Guide: GCD Integration with Comic-Analysis

## Overview

This guide provides step-by-step instructions for implementing GCD database integration with the Comic-Analysis project.

## Prerequisites

- Python 3.8+
- MySQL/MariaDB or SQLite
- ~12GB disk space for GCD database
- Comic-Analysis repository cloned
- Access to your comic collection

## Phase 1: Database Setup

### Option A: MySQL/MariaDB (Recommended for Production)

```bash
# 1. Download GCD dump
cd ~/data
wget https://www.comics.org/download/current_dump.sql.bz2

# 2. Extract
bunzip2 current_dump.sql.bz2

# 3. Create database
mysql -u root -p -e "CREATE DATABASE gcd CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"

# 4. Import (takes 10-20 minutes)
mysql -u root -p gcd < current_dump.sql

# 5. Verify
mysql -u root -p gcd -e "SELECT COUNT(*) FROM gcd_issue"
```

### Option B: SQLite (Recommended for Development)

```bash
# 1. Download GCD dump
cd ~/data
wget https://www.comics.org/download/current_dump.sql.bz2
bunzip2 current_dump.sql.bz2

# 2. Convert to SQLite (requires mysql2sqlite tool)
# Install: https://github.com/dumblob/mysql2sqlite
mysql2sqlite current_dump.sql | sqlite3 gcd.db

# 3. Verify
sqlite3 gcd.db "SELECT COUNT(*) FROM gcd_issue"
```

### Create Indexes for Performance

```sql
-- Run these in MySQL or SQLite
CREATE INDEX idx_series_name ON gcd_series(name);
CREATE INDEX idx_series_year ON gcd_series(year_began);
CREATE INDEX idx_issue_series ON gcd_issue(series_id);
CREATE INDEX idx_issue_number ON gcd_issue(number);
CREATE INDEX idx_story_issue ON gcd_story(issue_id);
CREATE INDEX idx_storycredit_story ON gcd_storycredit(story_id);
CREATE INDEX idx_storycredit_creator ON gcd_storycredit(creator_id);
CREATE INDEX idx_character_story ON gcd_storycharacter(story_id);
```

## Phase 2: Python Environment Setup

```bash
# 1. Create virtual environment
cd ~/projects/Comic-Analysis
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install sqlalchemy pymysql  # For MySQL
# OR
pip install sqlalchemy          # For SQLite only

# 3. Copy gcd_extractor.py to your project
cp ~/gcd-schema/gcd_extractor.py src/utils/

# 4. Test connection
python -c "from sqlalchemy import create_engine; engine = create_engine('sqlite:///~/data/gcd.db'); print('Connected!')"
```

## Phase 3: Filename Parsing

### Test Filename Parser

```python
from src.utils.gcd_extractor import FilenameParser

parser = FilenameParser()

# Test various filename formats
test_files = [
    "Amazing Spider-Man 001 (1963).cbz",
    "Batman #400.cbr",
    "X-Men v1 001.cbz",
    "2000 AD Prog 2000.pdf",
]

for filename in test_files:
    parsed = parser.parse(filename)
    print(f"{filename} →")
    print(f"  Series: {parsed['series_name']}")
    print(f"  Issue: {parsed['issue_number']}")
    print(f"  Year: {parsed['year']}")
    print()
```

### Enhance Parser for Your Collection

If your filenames have a different format, modify the patterns in `FilenameParser.PATTERNS`:

```python
class FilenameParser:
    PATTERNS = [
        # Add your custom pattern here
        r'^(.+?)\s+(\d{4})\s+(\d+)',  # Example: "Series Name 2023 001.cbz"
        # ... existing patterns
    ]
```

## Phase 4: Database Querying

### Create Database Connection Module

Create `src/utils/gcd_database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class GCDDatabase:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def find_series(self, series_name):
        """Find series by name with fuzzy matching."""
        query = """
        SELECT id, name, year_began, publisher_id
        FROM gcd_series
        WHERE name LIKE :pattern
        ORDER BY year_began DESC
        LIMIT 10
        """
        pattern = f"%{series_name}%"
        return self.session.execute(query, {'pattern': pattern}).fetchall()
    
    def find_issue(self, series_id, issue_number):
        """Find specific issue."""
        query = """
        SELECT id, number, publication_date, page_count, rating
        FROM gcd_issue
        WHERE series_id = :series_id AND number = :number
        LIMIT 1
        """
        return self.session.execute(
            query, 
            {'series_id': series_id, 'number': issue_number}
        ).fetchone()
    
    def get_issue_credits(self, issue_id):
        """Get all creator credits for an issue."""
        query = """
        SELECT 
            c.gcd_official_name AS creator_name,
            ct.name AS role,
            ct.sort_code
        FROM gcd_storycredit sc
        JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
        JOIN gcd_creator c ON cnd.creator_id = c.id
        JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
        JOIN gcd_story s ON sc.story_id = s.id
        JOIN gcd_storytype st ON s.type_id = st.id
        WHERE s.issue_id = :issue_id
          AND st.name = 'comic story'
        ORDER BY ct.sort_code, c.gcd_official_name
        """
        return self.session.execute(query, {'issue_id': issue_id}).fetchall()
    
    def get_issue_storyline(self, issue_id):
        """Get storyline information."""
        query = """
        SELECT 
            s.title,
            s.feature,
            s.genre,
            s.characters,
            s.synopsis,
            s.page_count
        FROM gcd_story s
        JOIN gcd_storytype st ON s.type_id = st.id
        WHERE s.issue_id = :issue_id
          AND st.name = 'comic story'
        ORDER BY s.sequence_number
        """
        return self.session.execute(query, {'issue_id': issue_id}).fetchall()
    
    def close(self):
        self.session.close()

# Usage
db = GCDDatabase('sqlite:///~/data/gcd.db')
series = db.find_series('Spider-Man')
print(f"Found {len(series)} series")
db.close()
```

## Phase 5: Batch Processing Script

Create `scripts/extract_gcd_metadata.py`:

```python
#!/usr/bin/env python
"""
Extract GCD metadata for all comics in a directory.
"""

import json
from pathlib import Path
from tqdm import tqdm
from src.utils.gcd_extractor import FilenameParser
from src.utils.gcd_database import GCDDatabase

def process_comic_collection(comic_dir, output_file, db_connection):
    """Process all comics in a directory."""
    parser = FilenameParser()
    db = GCDDatabase(db_connection)
    
    # Find all comic files
    comic_files = []
    for ext in ['*.cbz', '*.cbr', '*.pdf']:
        comic_files.extend(Path(comic_dir).rglob(ext))
    
    print(f"Found {len(comic_files)} comic files")
    
    results = []
    matched = 0
    
    for comic_path in tqdm(comic_files):
        filename = comic_path.name
        parsed = parser.parse(filename)
        
        result = {
            'file': str(comic_path),
            'filename': filename,
            'parsed': parsed,
            'matched': False
        }
        
        if parsed['series_name'] and parsed['issue_number']:
            # Search for series
            series_list = db.find_series(parsed['series_name'])
            
            if series_list:
                # Try to find the specific issue
                for series in series_list:
                    issue = db.find_issue(series.id, parsed['issue_number'])
                    
                    if issue:
                        # Found a match!
                        result['matched'] = True
                        result['gcd_issue_id'] = issue.id
                        result['gcd_series_id'] = series.id
                        
                        # Get credits
                        credits_raw = db.get_issue_credits(issue.id)
                        credits = {}
                        for credit in credits_raw:
                            role = credit.role
                            if role not in credits:
                                credits[role] = []
                            credits[role].append(credit.creator_name)
                        result['creators'] = credits
                        
                        # Get storyline
                        storylines = db.get_issue_storyline(issue.id)
                        result['storylines'] = [
                            {
                                'title': s.title,
                                'feature': s.feature,
                                'genre': s.genre,
                                'characters': s.characters,
                                'synopsis': s.synopsis,
                                'page_count': s.page_count
                            }
                            for s in storylines
                        ]
                        
                        matched += 1
                        break
        
        results.append(result)
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults:")
    print(f"  Total: {len(results)}")
    print(f"  Matched: {matched} ({matched/len(results)*100:.1f}%)")
    print(f"  Saved to: {output_file}")
    
    db.close()
    return results

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_gcd_metadata.py /path/to/comics [output.json]")
        sys.exit(1)
    
    comic_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'gcd_metadata.json'
    db_connection = 'sqlite:///~/data/gcd.db'
    
    process_comic_collection(comic_dir, output_file, db_connection)
```

### Run Batch Processing

```bash
python scripts/extract_gcd_metadata.py /path/to/comics gcd_metadata.json
```

## Phase 6: Integration with DataSpec

### Merge GCD Data into Existing DataSpec

Create `scripts/merge_gcd_to_dataspec.py`:

```python
#!/usr/bin/env python
"""
Merge GCD metadata into existing Comic-Analysis DataSpec.
"""

import json
import xarray as xr

def merge_gcd_metadata(dataspec_path, gcd_metadata_path, output_path):
    """Merge GCD metadata into DataSpec."""
    
    # Load GCD metadata
    with open(gcd_metadata_path) as f:
        gcd_data = json.load(f)
    
    # Create lookup by filename
    gcd_lookup = {}
    for entry in gcd_data:
        if entry['matched']:
            gcd_lookup[entry['filename']] = entry
    
    print(f"Loaded {len(gcd_lookup)} matched comics from GCD")
    
    # Load DataSpec
    ds = xr.open_zarr(dataspec_path)
    
    # Add GCD metadata as new variables
    # (Implementation depends on your DataSpec structure)
    
    # Example: Add creator information
    creator_data = []
    for comic_file in ds.coords['comic_id']:
        filename = comic_file.item()
        if filename in gcd_lookup:
            creator_data.append(json.dumps(gcd_lookup[filename]['creators']))
        else:
            creator_data.append(None)
    
    ds['gcd_creators'] = ('comic_id', creator_data)
    
    # Add storyline information
    storyline_data = []
    for comic_file in ds.coords['comic_id']:
        filename = comic_file.item()
        if filename in gcd_lookup:
            storyline_data.append(json.dumps(gcd_lookup[filename]['storylines']))
        else:
            storyline_data.append(None)
    
    ds['gcd_storylines'] = ('comic_id', storyline_data)
    
    # Save enhanced DataSpec
    ds.to_zarr(output_path, mode='w')
    
    print(f"Enhanced DataSpec saved to: {output_path}")
    print(f"Added GCD data for {len(gcd_lookup)} comics")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python merge_gcd_to_dataspec.py dataspec.zarr gcd_metadata.json [output.zarr]")
        sys.exit(1)
    
    dataspec_path = sys.argv[1]
    gcd_metadata_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else 'dataspec_enhanced.zarr'
    
    merge_gcd_metadata(dataspec_path, gcd_metadata_path, output_path)
```

## Phase 7: VLM Fallback Integration

For comics not found in GCD, implement VLM fallback:

```python
def extract_with_fallback(comic_file):
    """Extract metadata with GCD + VLM fallback."""
    
    # Level 1: Try GCD
    gcd_data = extract_from_gcd(comic_file)
    if gcd_data and gcd_data['confidence'] > 0.8:
        return gcd_data
    
    # Level 2: Try VLM
    print(f"GCD match failed, trying VLM for {comic_file}")
    vlm_data = extract_with_vlm(comic_file, pages=[0, 1, 2, 3, 4])
    if vlm_data:
        return vlm_data
    
    # Level 3: Log for manual review
    with open('manual_review.txt', 'a') as f:
        f.write(f"{comic_file}\n")
    
    return None

def extract_with_vlm(comic_file, pages):
    """Extract creator info using VLM from credits pages."""
    from your_vlm_module import VLM
    
    vlm = VLM()
    
    # Extract specified pages from comic
    images = extract_pages_from_comic(comic_file, pages)
    
    # Query VLM
    prompt = """
    Analyze this comic book page and extract:
    1. Creator credits (writer, artist, inker, colorist, letterer, editor)
    2. Publisher name
    3. Series name and issue number
    4. Publication date
    
    Return as JSON.
    """
    
    for image in images:
        result = vlm.query(image, prompt)
        if result:
            return {
                'source': 'vlm',
                'confidence': 0.7,
                'creators': result.get('creators'),
                'metadata': result.get('metadata')
            }
    
    return None
```

## Phase 8: Testing and Validation

### Test on Sample Comics

```python
# Test extraction on a few known comics
test_comics = [
    "/comics/Amazing Spider-Man 001 (1963).cbz",
    "/comics/Batman 400.cbr",
    "/comics/X-Men 001.cbz",
]

for comic in test_comics:
    print(f"\nTesting: {comic}")
    data = extract_with_fallback(comic)
    
    if data:
        print(f"  Source: {data['source']}")
        print(f"  Creators: {data.get('creators', {})}")
        print(f"  Confidence: {data.get('confidence', 'N/A')}")
    else:
        print("  No data extracted")
```

### Validation Against VLM

For comics matched in both GCD and VLM:

```python
def validate_gcd_vs_vlm(sample_size=100):
    """Compare GCD and VLM results for validation."""
    
    # Sample matched comics
    with open('gcd_metadata.json') as f:
        gcd_data = json.load(f)
    
    matched = [d for d in gcd_data if d['matched']][:sample_size]
    
    agreement = 0
    discrepancies = []
    
    for entry in matched:
        # Get VLM extraction
        vlm_result = extract_with_vlm(entry['file'], pages=[0, 1, 2])
        
        if vlm_result:
            # Compare creators
            gcd_creators = set(
                creator 
                for creators in entry['creators'].values() 
                for creator in creators
            )
            vlm_creators = set(
                creator
                for creators in vlm_result.get('creators', {}).values()
                for creator in creators
            )
            
            if gcd_creators & vlm_creators:  # Any overlap
                agreement += 1
            else:
                discrepancies.append({
                    'file': entry['file'],
                    'gcd': list(gcd_creators),
                    'vlm': list(vlm_creators)
                })
    
    print(f"Agreement: {agreement}/{sample_size} ({agreement/sample_size*100:.1f}%)")
    
    # Review discrepancies
    with open('discrepancies.json', 'w') as f:
        json.dump(discrepancies, f, indent=2)
```

## Monitoring and Maintenance

### Track Match Rate

```python
def generate_match_report(gcd_metadata_file):
    """Generate report on GCD match success."""
    
    with open(gcd_metadata_file) as f:
        data = json.load(f)
    
    total = len(data)
    matched = sum(1 for d in data if d['matched'])
    
    print(f"GCD Match Report")
    print(f"================")
    print(f"Total comics: {total}")
    print(f"GCD matches: {matched} ({matched/total*100:.1f}%)")
    print(f"VLM fallback needed: {total - matched}")
    
    # Breakdown by parsing success
    parsed = sum(1 for d in data if d['parsed']['series_name'])
    print(f"\nFilename parsing:")
    print(f"  Success: {parsed} ({parsed/total*100:.1f}%)")
    print(f"  Failed: {total - parsed}")
```

### Update Database Periodically

```bash
# Set up cron job to update GCD database bi-monthly
# crontab -e
# Add: 0 2 1,15 * * /path/to/update_gcd_db.sh

# update_gcd_db.sh:
#!/bin/bash
cd ~/data
wget https://www.comics.org/download/current_dump.sql.bz2
bunzip2 -f current_dump.sql.bz2
mysql -u root -p gcd < current_dump.sql
echo "GCD database updated: $(date)" >> gcd_update.log
```

## Troubleshooting

### Issue: Low Match Rate

**Symptoms:** Less than 50% of comics matched

**Solutions:**
1. Improve filename parsing patterns
2. Add fuzzy matching with Levenshtein distance
3. Implement cover image matching (perceptual hashing)
4. Review common filename formats in your collection

### Issue: Slow Queries

**Symptoms:** Batch processing takes hours

**Solutions:**
1. Verify indexes are created (see Phase 1)
2. Use batch queries with `WHERE IN` clause
3. Cache frequent series lookups
4. Consider connection pooling for MySQL

### Issue: Missing Credits

**Symptoms:** GCD returns empty credits

**Solutions:**
1. Check if using legacy credit fields (Story.script, etc.)
2. Implement fallback to legacy fields
3. Report missing data to GCD community

## Next Steps

After successful implementation:

1. **Enhance Closure Lite Model**
   - Add creator features to embedding generation
   - Train model with creator-aware objectives

2. **Build Creator Search**
   - Index embeddings by creator
   - Enable queries like "Find pages by Steve Ditko"

3. **Improve Paratext Classification**
   - Use GCD story types for PSS training
   - Validate VLM classifications against GCD

4. **Character Reidentification**
   - Link visual detections to GCD character IDs
   - Build character appearance timeline

5. **Contribute Back**
   - Report improvements to GCD community
   - Share insights with Comic-Analysis project

## Support

- **GCD Issues:** https://www.comics.org/
- **Comic-Analysis Issues:** https://github.com/RichardScottOZ/Comic-Analysis/issues
- **This Repository:** https://github.com/RichardScottOZ/gcd-schema

## References

- [GCD_SCHEMA_OVERVIEW.md](GCD_SCHEMA_OVERVIEW.md)
- [COMIC_ANALYSIS_MAPPING.md](COMIC_ANALYSIS_MAPPING.md)
- [SQL_EXAMPLES.md](SQL_EXAMPLES.md)
- [gcd_extractor.py](gcd_extractor.py)
