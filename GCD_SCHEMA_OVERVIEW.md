# Grand Comics Database (GCD) Schema Overview

## Introduction

This document provides an analysis of the Grand Comics Database (GCD) schema from [gcd-django](https://github.com/RichardScottOZ/gcd-django) to support integration with the [Comic-Analysis](https://github.com/RichardScottOZ/Comic-Analysis) project.

The GCD is a comprehensive, volunteer-driven database documenting printed comics worldwide, with detailed creator credits, storyline information, and metadata.

## Data Access Methods

### 1. Database Dumps (Recommended for Large-Scale Analysis)
- **Source:** https://www.comics.org/download/
- **Format:** MySQL/MariaDB database dumps
- **Frequency:** Bi-monthly updates
- **License:** Creative Commons
- **Advantages:**
  - No API rate limits
  - Fast local queries
  - Complete dataset access
  - Zero cost after initial setup

### 2. REST API
- **Documentation:** https://github.com/GrandComicsDatabase/gcd-django/wiki/API
- **Advantages:**
  - Real-time data
  - No local setup required
- **Limitations:**
  - Rate limits apply
  - Slower for large-scale batch processing

## Core Database Models

### Publisher Hierarchy

```
Publisher
├── IndPublisher (imprint relationships)
├── Brand (brand groups)
└── Series
    └── Issue
        └── Story
```

### Creator Information

```
Creator (main creator entity)
├── CreatorNameDetail (aliases, pen names, legal names)
├── CreatorSignature (signature information)
├── CreatorRelation (relationships between creators)
└── CreatorSchool (educational background)
```

### Story and Credits

```
Story (individual content piece)
├── StoryCredit (creator credits with roles)
│   ├── creator (FK to CreatorNameDetail)
│   ├── credit_type (script, pencils, inks, colors, letters, editing)
│   ├── is_credited (explicitly credited in comic)
│   ├── is_signed (signature present)
│   └── uncertain (attribution uncertain)
├── StoryCharacter (character appearances)
├── StoryGroup (group appearances)
├── StoryFeature (feature associations)
└── StoryType (cover, comic story, text story, etc.)
```

## Key Tables for Comic-Analysis Integration

### 1. Creator Table
**Purpose:** Core creator information

**Key Fields:**
- `id` - Unique creator identifier
- `gcd_official_name` - Official name used by GCD
- `sort_name` - Name for sorting
- `disambiguation` - Disambiguating text for similar names
- `birth_date`, `death_date` - Biographical dates
- `birth_country`, `birth_city` - Geographic information
- `bio` - Biography text
- `notes` - Additional notes
- `whos_who` - External reference URL

**Usage:** Primary source for creator biographical information.

### 2. CreatorNameDetail Table
**Purpose:** Multiple names/aliases for each creator

**Key Fields:**
- `id` - Unique name detail identifier
- `creator` - Foreign key to Creator
- `name` - The name/alias
- `sort_name` - Sortable version
- `is_official_name` - Whether this is the official name
- `given_name` - First/given name
- `family_name` - Last/family name
- `type` - Name type (FK to NameType)

**Usage:** Handle pen names, aliases, and legal name changes. Essential for matching creator credits.

### 3. StoryCredit Table
**Purpose:** Links creators to specific stories with role information

**Key Fields:**
- `id` - Unique credit identifier
- `creator` - Foreign key to CreatorNameDetail
- `story` - Foreign key to Story
- `credit_type` - Foreign key to CreditType (role)
- `is_credited` - Boolean, explicitly credited
- `is_signed` - Boolean, signature present
- `uncertain` - Boolean, attribution uncertain
- `signature` - Foreign key to CreatorSignature (if signed)
- `signed_as` - Text of signature
- `credited_as` - Text of credit
- `credit_name` - Display name for credit

**Usage:** Primary table for extracting "who did what" on each story.

### 4. CreditType Table
**Purpose:** Types of creative roles

**Standard Credit Types:**
| Sort Code | Name |
|-----------|------|
| 1 | script |
| 2 | pencils |
| 3 | inks |
| 4 | colors |
| 5 | letters |
| 6 | editing |
| 7 | genre |
| 8 | characters |
| 9 | synopsis |
| 10 | reprint notes |
| 11 | cover reproduction |
| 12 | letters page |

**Usage:** Classify creator contributions by role.

### 5. Story Table
**Purpose:** Individual story/content within an issue

**Key Fields:**
- `id` - Unique story identifier
- `issue` - Foreign key to Issue
- `title` - Story title
- `feature` - Associated feature/character
- `type` - Foreign key to StoryType
- `sequence_number` - Order within issue
- `page_count` - Number of pages
- `script` - Script credits (deprecated, use StoryCredit)
- `pencils` - Pencil credits (deprecated, use StoryCredit)
- `inks` - Ink credits (deprecated, use StoryCredit)
- `colors` - Color credits (deprecated, use StoryCredit)
- `letters` - Lettering credits (deprecated, use StoryCredit)
- `editing` - Editor credits (deprecated, use StoryCredit)
- `genre` - Genre information
- `characters` - Character appearances
- `synopsis` - Story synopsis
- `reprint_notes` - Reprint information
- `notes` - Additional notes

**Note:** The individual credit fields (script, pencils, etc.) are legacy fields. Modern GCD data uses the StoryCredit table with CreatorNameDetail relationships.

**Usage:** Access storyline information, synopses, and character appearances.

### 6. Issue Table
**Purpose:** Individual comic book issues

**Key Fields:**
- `id` - Unique issue identifier
- `series` - Foreign key to Series
- `number` - Issue number
- `volume` - Volume number
- `publication_date` - Publication date
- `key_date` - Sortable date string (YYYY-MM-DD)
- `price` - Cover price
- `page_count` - Total pages
- `indicia_publisher` - Publisher name from indicia
- `indicia_frequency` - Publication frequency
- `isbn` - ISBN if applicable
- `barcode` - Barcode/UPC
- `rating` - Age rating
- `notes` - Additional notes
- `editing` - Issue-level editor credits

**Usage:** Core metadata for matching local comic files to GCD database entries.

### 7. Series Table
**Purpose:** Comic book series information

**Key Fields:**
- `id` - Unique series identifier
- `name` - Series name
- `sort_name` - Sortable name
- `format` - Format (comic, magazine, etc.)
- `year_began` - Start year
- `year_ended` - End year
- `publication_dates` - Human-readable publication dates
- `publisher` - Foreign key to Publisher
- `country` - Foreign key to Country
- `language` - Foreign key to Language
- `notes` - Additional notes
- `color` - Color/B&W indicator
- `dimensions` - Physical dimensions
- `paper_stock` - Paper type
- `binding` - Binding type
- `publishing_format` - Publishing format details
- `is_comics_publication` - Boolean flag

**Usage:** Series-level metadata for classification and organization.

### 8. StoryType Table
**Purpose:** Types of story content

**Common Story Types:**
- `cover` - Cover image
- `comic story` - Main comic narrative
- `text story` - Text-based story
- `illustration` - Standalone illustration
- `advertisement` - Ad content
- `statement of ownership` - Legal statement
- `letters page` - Reader letters
- `foreword` - Introductory text
- `activity` - Puzzle, game, etc.
- `biography` - Biographical text
- `filler` - Filler content
- `preview` - Preview of upcoming content
- `pinup` - Character pinup/portrait

**Usage:** Filter content type, identify paratext vs. narrative content (critical for Comic-Analysis project's paratext classification goals).

### 9. StoryCharacter Table
**Purpose:** Character appearances in stories

**Key Fields:**
- `id` - Unique appearance identifier
- `character` - Foreign key to CharacterNameDetail
- `story` - Foreign key to Story
- `universe` - Foreign key to Universe
- `role` - Foreign key to CharacterRole
- `is_flashback` - Boolean
- `is_origin` - Boolean, origin story
- `is_death` - Boolean, character death
- `notes` - Additional notes

**Usage:** Track character appearances for reidentification projects (see Comic-Analysis future work on character reidentification).

### 10. Publisher Table
**Purpose:** Comic publishers

**Key Fields:**
- `id` - Unique publisher identifier
- `name` - Publisher name
- `country` - Foreign key to Country
- `year_began` - Year founded
- `year_ended` - Year ended
- `notes` - Additional notes
- `url` - Publisher website

**Usage:** Publisher metadata for organization and filtering.

## Supporting Tables

### NameType
Categorizes name types for creators:
- Legal name
- Pen name
- House name
- Studio name
- Etc.

### CharacterRole
Defines character roles in stories:
- Lead
- Villain
- Cameo
- Flashback
- Etc.

### StoryArc
Links related stories across issues:
- Name and description
- Year first published
- Notes

### Feature
Recurring features/characters:
- Name
- Sort name
- Genre
- Language

### Country, Language, Script
Lookup tables for geographic and linguistic metadata.

## Database Relationships

### Many-to-Many Relationships

1. **Creator ↔ Story** (via StoryCredit)
   - One creator can work on many stories
   - One story can have many creators
   - StoryCredit provides the role information

2. **Character ↔ Story** (via StoryCharacter)
   - One character can appear in many stories
   - One story can feature many characters
   - StoryCharacter provides appearance details

3. **Series ↔ Series** (via SeriesBond)
   - Series can have relationships (continuations, spin-offs, etc.)

### One-to-Many Relationships

1. **Publisher → Series**
   - One publisher publishes many series

2. **Series → Issue**
   - One series contains many issues

3. **Issue → Story**
   - One issue contains many stories (cover, multiple comic stories, ads, etc.)

4. **Creator → CreatorNameDetail**
   - One creator can have many names/aliases

## Query Patterns for Comic-Analysis

### 1. Get All Credits for an Issue

```sql
SELECT 
    c.gcd_official_name AS creator_name,
    cnd.name AS credited_as_name,
    ct.name AS role,
    sc.credit_name,
    sc.is_credited,
    sc.is_signed,
    s.title AS story_title,
    st.name AS story_type
FROM gcd_storycredit sc
JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
JOIN gcd_creator c ON cnd.creator_id = c.id
JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
JOIN gcd_story s ON sc.story_id = s.id
JOIN gcd_storytype st ON s.type_id = st.id
WHERE s.issue_id = ?
ORDER BY s.sequence_number, ct.sort_code;
```

### 2. Find Issues by Series Name and Issue Number

```sql
SELECT 
    i.id,
    i.number,
    i.publication_date,
    s.name AS series_name,
    p.name AS publisher_name
FROM gcd_issue i
JOIN gcd_series s ON i.series_id = s.id
JOIN gcd_publisher p ON s.publisher_id = p.id
WHERE s.name LIKE ?
  AND i.number = ?;
```

### 3. Get Creator Bibliography

```sql
SELECT 
    s.name AS series_name,
    i.number AS issue_number,
    i.publication_date,
    st.title AS story_title,
    ct.name AS role
FROM gcd_storycredit sc
JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
JOIN gcd_story st ON sc.story_id = st.id
JOIN gcd_storytype stype ON st.type_id = stype.id
JOIN gcd_issue i ON st.issue_id = i.id
JOIN gcd_series s ON i.series_id = s.id
WHERE cnd.creator_id = ?
  AND stype.name = 'comic story'
ORDER BY i.key_date, s.sort_name;
```

### 4. Get Storyline/Synopsis Information

```sql
SELECT 
    s.name AS series_name,
    i.number,
    st.title,
    st.feature,
    st.genre,
    st.characters,
    st.synopsis,
    st.page_count
FROM gcd_story st
JOIN gcd_issue i ON st.issue_id = i.id
JOIN gcd_series s ON i.series_id = s.id
JOIN gcd_storytype stype ON st.type_id = stype.id
WHERE i.id = ?
  AND stype.name = 'comic story'
ORDER BY st.sequence_number;
```

### 5. Extract Age Rating Information

```sql
SELECT 
    s.name AS series_name,
    i.number,
    i.rating,
    i.publication_date
FROM gcd_issue i
JOIN gcd_series s ON i.series_id = s.id
WHERE i.rating IS NOT NULL
  AND i.rating != '';
```

### 6. Get Character Appearances

```sql
SELECT 
    c.name AS character_name,
    sc.role_id,
    sc.is_flashback,
    sc.is_origin,
    sc.is_death,
    st.title AS story_title
FROM gcd_storycharacter sc
JOIN gcd_characternamedetail cnd ON sc.character_id = cnd.id
JOIN gcd_character c ON cnd.character_id = c.id
JOIN gcd_story st ON sc.story_id = st.id
WHERE st.issue_id = ?
ORDER BY st.sequence_number;
```

## Integration Strategy for Comic-Analysis

### Phase 1: Database Setup
1. Download GCD database dump from https://www.comics.org/download/
2. Import into local MySQL/MariaDB or convert to SQLite for portability
3. Create indexes on frequently queried fields (series.name, issue.number, etc.)

### Phase 2: Filename Matching
Implement filename parsing to extract:
- Series name
- Issue number
- Volume (if present)
- Publisher (if present)

Example filenames:
- `Amazing Spider-Man 001 (1963).cbz`
- `Batman v1 #400.cbr`
- `2000 AD Prog 2000.pdf`

### Phase 3: Database Querying
For each comic file:
1. Parse filename → extract metadata
2. Query GCD database for matching issue
3. If found: Extract creator credits, storyline, age rating
4. If not found: Log for manual review or VLM fallback

### Phase 4: VLM Fallback (as per Comic-Databases.md)
For comics not found in GCD:
- Extract first 5 pages
- Use VLM (Gemini, Gemma, etc.) to extract creator information
- Store results with confidence scores

### Phase 5: Data Export
Export extracted data in format suitable for Comic-Analysis project:
- JSON or Parquet format
- Fields: comic_id, creators (by role), storyline, genre, age_rating, characters
- Link to original filename/path

## Notes on Data Quality

### Strengths
- Highly detailed creator credits with role specificity
- Strong coverage of mainstream American comics (Marvel, DC, Image, etc.)
- Good historical coverage (Golden Age through present)
- Community-vetted data quality

### Limitations
- Variable coverage of:
  - Non-English language comics
  - Very recent releases (volunteer indexing lag)
  - Indie/small press titles
  - Manga (better covered by other databases)
- Some older entries use legacy credit fields instead of structured StoryCredit table

### Recommendations
1. Use StoryCredit table as primary source for credits
2. Fall back to legacy Story credit fields if StoryCredit is empty
3. Implement fuzzy matching for series names (accounting for "The", punctuation, etc.)
4. Consider supplementary data sources:
   - Comic Vine API for modern comics
   - Manga-specific databases for manga titles
   - Publisher-specific APIs when available

## References

- GCD Django Repository: https://github.com/RichardScottOZ/gcd-django
- GCD Official Site: https://www.comics.org/
- GCD Documentation: https://docs.comics.org/
- GCD Data Download: https://www.comics.org/download/
- GCD API Documentation: https://github.com/GrandComicsDatabase/gcd-django/wiki/API
- Comic-Analysis Project: https://github.com/RichardScottOZ/Comic-Analysis
