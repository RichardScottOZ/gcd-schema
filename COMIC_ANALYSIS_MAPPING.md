# GCD Schema to Comic-Analysis Project Mapping

## Overview

This document maps the Grand Comics Database (GCD) schema to the specific needs of the [Comic-Analysis](https://github.com/RichardScottOZ/Comic-Analysis) project, which focuses on multimodal analysis of comic book pages.

## Comic-Analysis Project Context

### Current State
- **Dataset:** ~330K Calibre pages, ~805K Amazon pages
- **Framework:** Closure Lite - multimodal fusion model
- **Processing Pipeline:**
  1. Comic file → Page images
  2. VLM text extraction
  3. Fast-RCNN panel detection
  4. DataSpec integration
  5. Multimodal embedding generation

### Future Work Goals (from documentation/future_work/)

1. **Paratext Classification**
   - Classify pages: cover, credits, ads, previews, back cover
   - Page Stream Segmentation (PSS)

2. **Character Reidentification**
   - Track character appearances across pages/issues
   - Link visual representations to character identities

3. **Creator Attribution**
   - Assign creators (writers, artists, etc.) to comic pages
   - Support ~40K comic collection

4. **Storyline Assignment**
   - Associate pages with storyline metadata
   - Genre classification

5. **Age Rating & Metadata**
   - Age appropriateness
   - Publisher information
   - Publication dates

## GCD Schema Mapping to Project Needs

### 1. Creator Attribution

**Comic-Analysis Need:** For each comic file, extract creator names by role (writer, penciller, inker, colorist, letterer, editor).

**GCD Mapping:**

```
Comic File → Parse filename
           → Match to Issue (gcd_issue)
           → Get Stories (gcd_story where type_id = 'comic story')
           → Get Credits (gcd_storycredit)
           → Get Creator Names (gcd_creatornamedetail)
           → Get Creator Info (gcd_creator)
```

**Key Tables:**
- `gcd_issue` - Issue identification
- `gcd_story` - Story content
- `gcd_storycredit` - Creator-to-story links
- `gcd_creatornamedetail` - Creator name variants
- `gcd_creator` - Creator biographical data
- `gcd_credittype` - Role types

**Data Structure:**
```python
{
    "comic_file": "Amazing Spider-Man 001 (1963).cbz",
    "gcd_issue_id": 12345,
    "creators": {
        "script": ["Stan Lee"],
        "pencils": ["Steve Ditko"],
        "inks": ["Steve Ditko"],
        "colors": ["Stan Goldberg"],
        "letters": ["Artie Simek"],
        "editing": ["Stan Lee"]
    }
}
```

**SQL Query:**
```sql
SELECT 
    ct.name AS role,
    GROUP_CONCAT(c.gcd_official_name ORDER BY c.gcd_official_name) AS creators
FROM gcd_storycredit sc
JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
JOIN gcd_creator c ON cnd.creator_id = c.id
JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
JOIN gcd_story s ON sc.story_id = s.id
JOIN gcd_storytype st ON s.type_id = st.id
WHERE s.issue_id = ?
  AND st.name = 'comic story'
GROUP BY ct.name
ORDER BY ct.sort_code;
```

### 2. Storyline Information

**Comic-Analysis Need:** Synopsis, genre, character list, story title for embedding enrichment.

**GCD Mapping:**

```
Issue → Stories (comic story type)
      → Extract: title, feature, genre, characters, synopsis
```

**Key Tables:**
- `gcd_story` - Story metadata
- `gcd_storytype` - Content type filter
- `gcd_storycharacter` - Character appearances
- `gcd_characternamedetail` - Character names
- `gcd_storyarc` - Multi-issue storylines

**Data Structure:**
```python
{
    "comic_file": "Amazing Spider-Man 001 (1963).cbz",
    "storylines": [
        {
            "title": "Spider-Man",
            "feature": "Spider-Man",
            "genre": "superhero",
            "characters": ["Spider-Man [Peter Parker]", "Uncle Ben", "Aunt May"],
            "synopsis": "High school student Peter Parker is bitten by a radioactive spider...",
            "page_count": 11
        }
    ]
}
```

**SQL Query:**
```sql
SELECT 
    s.title,
    s.feature,
    s.genre,
    s.characters,
    s.synopsis,
    s.page_count,
    s.sequence_number
FROM gcd_story s
JOIN gcd_storytype st ON s.type_id = st.id
WHERE s.issue_id = ?
  AND st.name IN ('comic story', 'text story')
ORDER BY s.sequence_number;
```

### 3. Paratext Classification (Story Type)

**Comic-Analysis Need:** Distinguish narrative content from covers, ads, credits pages, previews, etc.

**GCD Mapping:**

```
Story → StoryType
      → Map to paratext categories
```

**Key Tables:**
- `gcd_storytype` - Content type (critical!)

**GCD Story Types → Comic-Analysis Paratext Classes:**

| GCD StoryType | Comic-Analysis Class | Description |
|---------------|----------------------|-------------|
| cover | cover | Front cover |
| comic story | narrative | Main story content |
| text story | narrative | Text-based story |
| illustration | art | Standalone art |
| advertisement | advertisements | Ads |
| statement of ownership | text | Legal text |
| letters page | letters | Reader letters |
| foreword | text | Introduction |
| activity | text | Puzzles, games |
| biography | text | Biographical text |
| filler | text | Filler content |
| preview | previews | Upcoming content |
| pinup | art | Character pinup |
| insert | other | Insert/supplement |
| photo story | narrative | Photo narrative |
| cover reprint | art | Reprint of previous cover |

**Integration Point:**
When training the PSS (Page Stream Segmentation) model, use GCD story types as ground truth labels for supervised learning.

**Data Structure:**
```python
{
    "comic_file": "Amazing Spider-Man 001 (1963).cbz",
    "pages": [
        {"page": 0, "type": "cover", "gcd_story_id": 1001},
        {"page": 1, "type": "narrative", "gcd_story_id": 1002, "page_range": [1, 11]},
        {"page": 12, "type": "advertisements", "gcd_story_id": 1003},
        {"page": 13, "type": "narrative", "gcd_story_id": 1004, "page_range": [13, 18]},
        # ...
    ]
}
```

**SQL Query:**
```sql
SELECT 
    s.sequence_number,
    st.name AS story_type,
    s.page_count,
    s.title
FROM gcd_story s
JOIN gcd_storytype st ON s.type_id = st.id
WHERE s.issue_id = ?
ORDER BY s.sequence_number;
```

**Use Case:**
1. Parse GCD story sequences for an issue
2. Calculate cumulative page positions
3. Assign GCD story types to page ranges
4. Use as training labels for PSS classifier
5. Validate VLM-extracted page classifications against GCD ground truth

### 4. Character Reidentification

**Comic-Analysis Need:** Link visual character representations across pages to character identities.

**GCD Mapping:**

```
Issue → Stories → StoryCharacter
                → CharacterNameDetail
                → Character (canonical identity)
```

**Key Tables:**
- `gcd_storycharacter` - Character appearances
- `gcd_characternamedetail` - Character name variants
- `gcd_character` - Canonical character info
- `gcd_characterrole` - Role in story
- `gcd_universe` - Fictional universe

**Data Structure:**
```python
{
    "comic_file": "Amazing Spider-Man 001 (1963).cbz",
    "characters": [
        {
            "gcd_character_id": 5001,
            "canonical_name": "Spider-Man",
            "name_in_story": "Spider-Man",
            "alternate_names": ["Peter Parker", "Spidey", "Web-Slinger"],
            "role": "lead",
            "universe": "Marvel Universe",
            "appearance_flags": {
                "is_origin": True,
                "is_flashback": False,
                "is_death": False
            },
            "stories": [1002, 1004]  # Story IDs where character appears
        },
        # ...
    ]
}
```

**SQL Query:**
```sql
SELECT 
    c.id AS character_id,
    c.name AS canonical_name,
    cnd.name AS name_in_story,
    u.name AS universe,
    cr.name AS role,
    sc.is_origin,
    sc.is_flashback,
    sc.is_death,
    s.id AS story_id,
    s.title AS story_title
FROM gcd_storycharacter sc
JOIN gcd_characternamedetail cnd ON sc.character_id = cnd.id
JOIN gcd_character c ON cnd.character_id = c.id
LEFT JOIN gcd_universe u ON sc.universe_id = u.id
LEFT JOIN gcd_characterrole cr ON sc.role_id = cr.id
JOIN gcd_story s ON sc.story_id = s.id
WHERE s.issue_id = ?
ORDER BY s.sequence_number, cr.sort_code;
```

**Integration Strategy:**
1. Extract character list from GCD for each issue
2. Use as ground truth labels for visual character detection
3. Link panel-level character detections to canonical GCD character IDs
4. Build character appearance timeline across issues/series
5. Support visual similarity search: "Find pages with Spider-Man"

**Use Case for Reidentification Project:**
- GCD provides canonical character names
- VLM provides visual descriptions
- Combine: "This panel contains Spider-Man (canonical) wearing his classic costume (visual)"

### 5. Age Rating & Content Metadata

**Comic-Analysis Need:** Filter comics by appropriateness, organize by publisher/era.

**GCD Mapping:**

```
Issue → rating (age rating)
      → Series → publisher, year_began, format
```

**Key Tables:**
- `gcd_issue` - Issue-level rating
- `gcd_series` - Series-level metadata
- `gcd_publisher` - Publisher info

**Data Structure:**
```python
{
    "comic_file": "Amazing Spider-Man 001 (1963).cbz",
    "metadata": {
        "gcd_issue_id": 12345,
        "gcd_series_id": 1001,
        "age_rating": "Approved by the Comics Code Authority",
        "publisher": "Marvel Comics",
        "series": "Amazing Spider-Man",
        "volume": 1,
        "issue_number": "1",
        "publication_date": "March 1963",
        "year": 1963,
        "format": "comic",
        "page_count": 36,
        "color": "color",
        "price": "0.12 USD"
    }
}
```

**SQL Query:**
```sql
SELECT 
    i.id AS issue_id,
    i.rating AS age_rating,
    i.publication_date,
    i.page_count,
    i.price,
    i.barcode,
    i.isbn,
    s.id AS series_id,
    s.name AS series_name,
    s.year_began,
    s.year_ended,
    s.format,
    s.color,
    p.name AS publisher
FROM gcd_issue i
JOIN gcd_series s ON i.series_id = s.id
JOIN gcd_publisher p ON s.publisher_id = p.id
WHERE i.id = ?;
```

**Age Rating Values (examples):**
- "Approved by the Comics Code Authority"
- "Comics Code"
- "Ages 12+"
- "Mature"
- "T+ (Teen Plus)"
- "MAX"
- NULL (no rating)

**Integration Notes:**
- GCD age ratings are inconsistent (historical variation)
- May need normalization/mapping to standard categories
- Can use as feature for content-based filtering

### 6. Genre Classification

**Comic-Analysis Need:** Classify comics by genre for recommendation/organization.

**GCD Mapping:**

```
Story → genre (text field)
Series → format (comic, magazine, etc.)
```

**Key Tables:**
- `gcd_story` - Story-level genre
- `gcd_series` - Series-level format

**Genre Values (examples from GCD):**
- "superhero"
- "science fiction"
- "fantasy"
- "horror"
- "humor"
- "adventure"
- "western"
- "romance"
- "war"
- "crime"
- "biography"
- "non-fiction"

**Data Structure:**
```python
{
    "comic_file": "Amazing Spider-Man 001 (1963).cbz",
    "genres": ["superhero", "science fiction"],
    "series_format": "comic"
}
```

**SQL Query:**
```sql
SELECT DISTINCT
    s.genre
FROM gcd_story s
WHERE s.issue_id = ?
  AND s.genre IS NOT NULL
  AND s.genre != '';
```

**Note:** Genre is a text field, may contain multiple comma-separated genres.

## Hybrid Extraction Strategy

As recommended in Comic-Databases.md, use a hybrid approach:

### Level 1: GCD Database (Fast, Free)
1. Parse filename
2. Query local GCD database
3. Extract all available metadata

### Level 2: VLM Fallback (Slow, Costly)
For comics not found in GCD:
1. Extract first 5 pages
2. Use VLM to extract:
   - Creator information (from credits page)
   - Title and publisher
   - Basic storyline description

### Level 3: Manual Review
For failures from both methods:
1. Log for manual review
2. Prioritize by dataset importance

## Data Export Format

Recommended output format for Comic-Analysis integration:

```json
{
    "comic_file": "/path/to/Amazing_Spider-Man_001.cbz",
    "filename": "Amazing Spider-Man 001 (1963).cbz",
    "source": "gcd",  // "gcd", "vlm", or "manual"
    "gcd_issue_id": 12345,
    "series": {
        "gcd_series_id": 1001,
        "name": "Amazing Spider-Man",
        "publisher": "Marvel Comics",
        "year_began": 1963,
        "volume": 1
    },
    "issue": {
        "number": "1",
        "publication_date": "1963-03-00",
        "page_count": 36,
        "price": "0.12 USD",
        "age_rating": "Approved by the Comics Code Authority"
    },
    "creators": {
        "script": [
            {"gcd_id": 1, "name": "Stan Lee"}
        ],
        "pencils": [
            {"gcd_id": 2, "name": "Steve Ditko"}
        ],
        "inks": [
            {"gcd_id": 2, "name": "Steve Ditko"}
        ],
        "colors": [
            {"gcd_id": 3, "name": "Stan Goldberg"}
        ],
        "letters": [
            {"gcd_id": 4, "name": "Artie Simek"}
        ],
        "editing": [
            {"gcd_id": 1, "name": "Stan Lee"}
        ]
    },
    "stories": [
        {
            "gcd_story_id": 1002,
            "sequence": 1,
            "type": "comic story",
            "title": "Spider-Man",
            "page_count": 11,
            "page_range": [1, 11],
            "genre": ["superhero", "science fiction"],
            "feature": "Spider-Man",
            "characters": [
                {
                    "gcd_character_id": 5001,
                    "name": "Spider-Man",
                    "alternate_names": ["Peter Parker"],
                    "role": "lead",
                    "is_origin": true
                }
            ],
            "synopsis": "High school student Peter Parker is bitten by a radioactive spider and gains superpowers...",
            "creators": {
                "script": ["Stan Lee"],
                "pencils": ["Steve Ditko"],
                "inks": ["Steve Ditko"]
            }
        }
    ],
    "extraction_metadata": {
        "extracted_at": "2024-11-12T22:00:00Z",
        "gcd_version": "2024-10-01",
        "confidence": 1.0  // 1.0 for exact match, lower for fuzzy matches
    }
}
```

## Integration Workflow

### Step 1: Database Setup
```bash
# Download GCD dump
wget https://www.comics.org/download/current_dump.sql.bz2

# Import to MySQL
bunzip2 current_dump.sql.bz2
mysql -u root -p gcd < current_dump.sql

# Or convert to SQLite for portability
mysql2sqlite current_dump.sql | sqlite3 gcd.db
```

### Step 2: Filename Parsing
```python
from gcd_extractor import FilenameParser

parser = FilenameParser()
parsed = parser.parse("Amazing Spider-Man 001 (1963).cbz")
# Returns: {'series_name': 'Amazing Spider-Man', 'issue_number': '001', 'year': '1963'}
```

### Step 3: GCD Query
```python
from gcd_extractor import GCDExtractor

extractor = GCDExtractor(connection_string='sqlite:///gcd.db')
issue = extractor.get_issue_by_series_and_number(
    parsed['series_name'], 
    parsed['issue_number']
)
```

### Step 4: Extract All Data
```python
if issue:
    credits = extractor.get_issue_credits(issue.issue_id)
    stories = extractor.get_issue_stories(issue.issue_id)
    characters = extractor.get_character_appearances(issue.issue_id)
    # ... build output JSON
```

### Step 5: Batch Processing
```python
# Process entire comic collection
comic_files = list(Path("/comics").rglob("*.cb[rz]"))
extractor.batch_extract(comic_files, "gcd_metadata.json")
```

### Step 6: Integration with DataSpec
```python
# Load GCD metadata
with open('gcd_metadata.json') as f:
    gcd_data = json.load(f)

# Load existing DataSpec (from VLM + RCNN pipeline)
dataspec = load_dataspec('comics_dataspec.zarr')

# Merge GCD metadata into DataSpec
for entry in gcd_data:
    comic_id = entry['comic_file']
    if comic_id in dataspec:
        dataspec[comic_id].update({
            'gcd_creators': entry['creators'],
            'gcd_storyline': entry['stories'],
            'gcd_characters': entry.get('characters', []),
            'gcd_metadata': entry['issue']
        })

# Save enhanced DataSpec
dataspec.to_zarr('comics_dataspec_enhanced.zarr')
```

## Use Cases for Enhanced Pipeline

### 1. Creator-Aware Embeddings
Train Closure Lite model with creator information:
- Input: page image + panel text + **creator names**
- Output: embedding that understands artistic style by creator

**Query:** "Find pages drawn by Steve Ditko"

### 2. Storyline-Aware Search
Enhance semantic search with storyline context:
- Input: page image + panel text + **story synopsis + characters**
- Output: embedding enriched with narrative context

**Query:** "Find origin story pages"

### 3. Character-Focused Analysis
Link visual character detection to canonical identities:
- Input: detected character in panel + **GCD character name**
- Output: reidentification across issues/series

**Query:** "Track Spider-Man costume changes across issues"

### 4. Paratext Filtering
Use GCD story types for training/validation:
- Ground truth: GCD story type labels
- Predictions: VLM page classification
- Accuracy: Compare predictions to GCD labels

**Benefit:** Improve paratext classifier with GCD supervision

### 5. Genre-Based Retrieval
Organize embeddings by genre:
- Cluster embeddings by GCD genre labels
- Support genre-specific queries

**Query:** "Find superhero pages with dark/noir atmosphere"

## Performance Considerations

### Database Size
- Full GCD dump: ~10GB MySQL, ~7GB SQLite
- Indexes: Add ~2GB
- Total: ~12GB local storage

### Query Performance
- Series search (indexed): <10ms
- Issue lookup: <5ms
- Full credit extraction: 50-100ms (joins)
- Batch processing: ~100-200 comics/second

### Optimization Strategies
1. **Cache frequent queries** (series lookups)
2. **Batch SQL queries** (use WHERE IN for multiple issues)
3. **Precompute common joins** (materialized views)
4. **Index custom fields** (add indexes for Comic-Analysis-specific queries)

## Missing Data Handling

### GCD Limitations
- Not all comics are in GCD
- Some entries lack detailed credits
- Historical entries may be incomplete

### Fallback Strategy
```python
def extract_metadata(comic_file):
    # Level 1: GCD
    gcd_data = gcd_extractor.extract(comic_file)
    if gcd_data and gcd_data['confidence'] > 0.8:
        return gcd_data
    
    # Level 2: VLM
    vlm_data = vlm_extractor.extract(comic_file, pages=[0, 1, 2, 3, 4])
    if vlm_data:
        return vlm_data
    
    # Level 3: Manual
    log_for_manual_review(comic_file)
    return None
```

## Validation & Quality Assurance

### GCD vs VLM Cross-Validation
For comics in both GCD and VLM extractions:
1. Compare creator names
2. Validate character lists
3. Check storyline descriptions
4. Identify discrepancies

**Benefit:** Improve VLM prompts based on GCD ground truth

### Metrics
- **Match Rate:** % of comics found in GCD
- **Completeness:** % of matched comics with full credits
- **Accuracy:** Agreement between GCD and VLM (for validation subset)

## Future Enhancements

### 1. Cover Image Matching
- Download GCD cover images
- Use perceptual hashing for filename-independent matching
- Fallback when filename parsing fails

### 2. Series Disambiguation
- Use publisher + year to disambiguate series
- Example: "Ghost Rider (Marvel, 1973)" vs "Ghost Rider (Marvel, 1990)"

### 3. Multi-Language Support
- GCD has international comics
- Support non-English series names
- Handle translated titles

### 4. Real-Time API Integration
- Query GCD API for very recent comics
- Supplement local database dump

### 5. Community Contributions
- Allow manual corrections
- Feed back to GCD project
- Build Comic-Analysis-specific metadata layer

## References

- **GCD Schema Documentation:** [GCD_SCHEMA_OVERVIEW.md](GCD_SCHEMA_OVERVIEW.md)
- **Entity Relationships:** [GCD_ENTITY_RELATIONSHIPS.md](GCD_ENTITY_RELATIONSHIPS.md)
- **Extractor Code:** [gcd_extractor.py](gcd_extractor.py)
- **Comic-Analysis Project:** https://github.com/RichardScottOZ/Comic-Analysis
- **GCD Official Site:** https://www.comics.org/
- **GCD Data Downloads:** https://www.comics.org/download/
