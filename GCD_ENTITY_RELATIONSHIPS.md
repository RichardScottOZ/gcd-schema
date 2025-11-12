# GCD Database Entity Relationships

## Entity-Relationship Diagram (Text Format)

```
┌─────────────────┐
│   Publisher     │
└────────┬────────┘
         │ 1
         │
         │ *
┌────────▼────────┐
│     Series      │
└────────┬────────┘
         │ 1
         │
         │ *
┌────────▼────────┐
│     Issue       │
└────────┬────────┘
         │ 1
         │
         │ *
┌────────▼────────┐
│     Story       │◄──────────────┐
└────────┬────────┘               │
         │ 1                      │
         │                        │
         │ *                      │
┌────────▼────────┐               │
│  StoryCredit    │               │
└────────┬────────┘               │
         │ *                      │
         │                        │
         │ 1                      │
┌────────▼────────────┐           │
│ CreatorNameDetail   │           │
└────────┬────────────┘           │
         │ *                      │
         │                        │
         │ 1                      │
┌────────▼────────┐               │
│    Creator      │               │
└─────────────────┘               │
                                  │
┌────────────────┐                │
│  StoryType     │───────────────┘
│  (lookup)      │
└────────────────┘

┌────────────────┐                ┌────────────────┐
│  CreditType    │                │  Character     │
│  (lookup)      │                └────────┬───────┘
└────────┬───────┘                         │ 1
         │ 1                               │
         │                                 │ *
         │                        ┌────────▼────────────┐
         └───────────────────────►│ CharacterNameDetail │
                                  └────────┬────────────┘
                                           │ *
                                           │
                                           │ 1
                                  ┌────────▼────────┐
                                  │ StoryCharacter  │
                                  │                 │
                                  │ (M:M bridge)    │
                                  └────────┬────────┘
                                           │ *
                                           │
                                           │ 1
                                           └────────► Story

```

## Core Relationships

### Publisher → Series → Issue → Story

This is the primary hierarchy for comic content:

1. **Publisher** (e.g., Marvel, DC Comics)
   - Has many **Series** (e.g., Amazing Spider-Man, Batman)

2. **Series** 
   - Belongs to one **Publisher**
   - Has many **Issues** (individual comic books)

3. **Issue**
   - Belongs to one **Series**
   - Has many **Stories** (cover, main story, backup stories, ads)

4. **Story**
   - Belongs to one **Issue**
   - Has one **StoryType** (cover, comic story, text story, etc.)
   - Has many **StoryCredit** entries (creator attributions)
   - Has many **StoryCharacter** entries (character appearances)

### Creator Attribution Chain

```
Creator
  ├── has many CreatorNameDetail (aliases, pen names)
  │     └── used in many StoryCredit
  │           └── for one Story
  │
  └── has many CreatorSignature
        └── referenced by StoryCredit (when signed)
```

**Relationship Flow:**
1. A **Creator** (person) can have multiple names/aliases (**CreatorNameDetail**)
2. Each specific name is used in **StoryCredit** entries
3. Each **StoryCredit** links a creator name to a specific **Story**
4. Each **StoryCredit** has a **CreditType** (script, pencils, inks, colors, letters, editing)

### Character Appearances Chain

```
Character
  └── has many CharacterNameDetail (aliases, alternate names)
        └── used in many StoryCharacter
              └── for one Story
```

**Relationship Flow:**
1. A **Character** (e.g., Spider-Man) can have multiple names (**CharacterNameDetail**)
2. Each appearance is tracked via **StoryCharacter**
3. **StoryCharacter** links a character name to a specific **Story**
4. Additional flags track: is_flashback, is_origin, is_death

## Detailed Entity Descriptions

### Publisher
- **Primary Key:** id
- **Key Attributes:** name, country, year_began, year_ended
- **Relationships:**
  - One-to-Many with Series
  - One-to-Many with Brand
  - One-to-Many with IndPublisher (imprint relationships)

### Series
- **Primary Key:** id
- **Key Attributes:** name, sort_name, year_began, year_ended, format
- **Foreign Keys:**
  - publisher_id → Publisher
  - country_id → Country
  - language_id → Language
- **Relationships:**
  - Many-to-One with Publisher
  - One-to-Many with Issue
  - Many-to-Many with Series (via SeriesBond - for continuations, spin-offs)

### Issue
- **Primary Key:** id
- **Key Attributes:** number, volume, publication_date, key_date, price, page_count, isbn, barcode, rating
- **Foreign Keys:**
  - series_id → Series
- **Relationships:**
  - Many-to-One with Series
  - One-to-Many with Story

### Story
- **Primary Key:** id
- **Key Attributes:** title, feature, genre, characters, synopsis, page_count, sequence_number
- **Foreign Keys:**
  - issue_id → Issue
  - type_id → StoryType
  - feature_id → Feature (optional)
- **Relationships:**
  - Many-to-One with Issue
  - Many-to-One with StoryType
  - One-to-Many with StoryCredit
  - One-to-Many with StoryCharacter
  - One-to-Many with StoryGroup
  - Many-to-Many with Feature (via StoryFeature)

**Note:** Story also has legacy credit fields (script, pencils, inks, colors, letters, editing) that contain text strings. These are deprecated in favor of the structured StoryCredit table.

### Creator
- **Primary Key:** id
- **Key Attributes:** gcd_official_name, sort_name, bio, birth_date, death_date
- **Foreign Keys:**
  - birth_date_id → Date
  - death_date_id → Date
  - birth_country_id → Country
  - death_country_id → Country
- **Relationships:**
  - One-to-Many with CreatorNameDetail
  - One-to-Many with CreatorSignature
  - Many-to-Many with CreatorRelation (creator relationships)
  - Many-to-Many with CreatorSchool (educational background)
  - Many-to-Many with DataSource

### CreatorNameDetail
- **Primary Key:** id
- **Key Attributes:** name, sort_name, given_name, family_name, is_official_name
- **Foreign Keys:**
  - creator_id → Creator
  - type_id → NameType
  - in_script_id → Script
- **Relationships:**
  - Many-to-One with Creator
  - Many-to-One with NameType
  - One-to-Many with StoryCredit

**Purpose:** Allows tracking of pen names, aliases, legal name changes. Essential because a creator might be credited under different names across their career.

### StoryCredit
- **Primary Key:** id
- **Key Attributes:** credit_name, is_credited, is_signed, uncertain, signed_as, credited_as
- **Foreign Keys:**
  - creator_id → CreatorNameDetail (not Creator directly!)
  - credit_type_id → CreditType
  - story_id → Story
  - signature_id → CreatorSignature (optional)
- **Relationships:**
  - Many-to-One with CreatorNameDetail
  - Many-to-One with CreditType
  - Many-to-One with Story
  - Many-to-One with CreatorSignature (optional)

**Purpose:** This is the junction table that links creators to stories with role information. Each row represents one credit (e.g., "Alan Moore - script" for a specific story).

### CreditType (Lookup Table)
- **Primary Key:** id
- **Key Attributes:** name, sort_code
- **Standard Values:**
  - script (1)
  - pencils (2)
  - inks (3)
  - colors (4)
  - letters (5)
  - editing (6)
  - [and others]

### StoryType (Lookup Table)
- **Primary Key:** id
- **Key Attributes:** name, sort_code
- **Standard Values:**
  - cover
  - comic story
  - text story
  - illustration
  - advertisement
  - statement of ownership
  - letters page
  - foreword
  - activity
  - biography
  - filler
  - preview
  - pinup

**Purpose:** Distinguishes narrative content from paratext (ads, letters pages, etc.). Critical for Comic-Analysis project's paratext classification goals.

### Character
- **Primary Key:** id
- **Key Attributes:** name, sort_name, disambiguation, description
- **Foreign Keys:**
  - language_id → Language
- **Relationships:**
  - One-to-Many with CharacterNameDetail
  - Many-to-Many with Group (via CharacterGroup)

### CharacterNameDetail
- **Primary Key:** id
- **Key Attributes:** name, sort_name, is_primary
- **Foreign Keys:**
  - character_id → Character
- **Relationships:**
  - Many-to-One with Character
  - One-to-Many with StoryCharacter

**Purpose:** Similar to CreatorNameDetail, allows tracking of character name variations (e.g., "Spider-Man", "Peter Parker", "The Amazing Spider-Man").

### StoryCharacter
- **Primary Key:** id
- **Key Attributes:** is_flashback, is_origin, is_death, notes
- **Foreign Keys:**
  - character_id → CharacterNameDetail
  - story_id → Story
  - universe_id → Universe (optional)
  - role_id → CharacterRole (optional)
- **Relationships:**
  - Many-to-One with CharacterNameDetail
  - Many-to-One with Story
  - Many-to-One with Universe (optional)
  - Many-to-One with CharacterRole (optional)
  - Many-to-Many with Group
  - Many-to-Many with GroupNameDetail

**Purpose:** Junction table linking characters to stories with appearance metadata.

### CharacterRole (Lookup Table)
- **Primary Key:** id
- **Key Attributes:** name, sort_code
- **Values:**
  - Lead
  - Villain
  - Cameo
  - Supporting
  - etc.

## Supporting Entities

### Feature
- **Purpose:** Recurring features within series (e.g., "Batman" feature in Detective Comics)
- **Key Attributes:** name, sort_name, genre
- **Relationships:**
  - Many-to-Many with Story (via StoryFeature)
  - One-to-Many with FeatureRelation

### StoryArc
- **Purpose:** Multi-issue storylines
- **Key Attributes:** name, sort_name, year_first_published, description
- **Relationships:**
  - Many-to-Many with Story (via StoryArcRelation)

### Universe
- **Purpose:** Fictional universes (Marvel Universe, DC Universe, etc.)
- **Key Attributes:** name, designation, description
- **Relationships:**
  - Referenced by Character
  - Referenced by Group
  - Referenced by StoryCharacter

### Group
- **Purpose:** Teams, organizations (Avengers, Justice League, etc.)
- **Key Attributes:** name, sort_name, description
- **Relationships:**
  - Many-to-Many with Character (via CharacterGroup)
  - Many-to-Many with Story (via StoryGroup)

### Brand
- **Purpose:** Publisher brand groups
- **Relationships:**
  - Many-to-One with Publisher
  - Many-to-Many with Issue (via BrandGroup)

### IndPublisher
- **Purpose:** Tracks imprint/publisher relationships
- **Relationships:**
  - Links parent publishers to subsidiary publishers

## Lookup Tables (Reference Data)

### Country
- **Attributes:** code, name
- **Used by:** Publisher, Series, Creator (birth/death)

### Language
- **Attributes:** code, name
- **Used by:** Series, Creator names, Character names

### Script
- **Attributes:** name (Latin, Cyrillic, etc.)
- **Used by:** CreatorNameDetail, CharacterNameDetail

### Date
- **Attributes:** year, month, day, year_uncertain, month_uncertain, day_uncertain
- **Used by:** Creator (birth_date, death_date)

**Purpose:** Flexible date representation allowing for uncertain/partial dates (e.g., "circa 1920" or just "1920s").

### NameType
- **Attributes:** type (legal name, pen name, house name, etc.)
- **Used by:** CreatorNameDetail

### RelationType
- **Attributes:** type, reverse_type (spouse/spouse, teacher/student, etc.)
- **Used by:** CreatorRelation

## Data Integrity Constraints

### Cascading Deletes
Most relationships use `on_delete=models.CASCADE`, meaning:
- Deleting a Publisher deletes all its Series
- Deleting a Series deletes all its Issues
- Deleting an Issue deletes all its Stories
- Deleting a Story deletes all its StoryCredits, StoryCharacters, etc.

### Referential Integrity
- All foreign keys are enforced at the database level
- Many-to-Many relationships use junction tables

### Unique Constraints
- Creator.gcd_official_name (not unique - disambiguation field handles duplicates)
- Series.name (not unique - can have multiple series with same name from different publishers/eras)
- StoryType.name (unique)
- CreditType.name (unique)

## Indexes for Performance

Key indexes exist on:
- Series.name
- Issue.number
- Story.issue_id
- StoryCredit.story_id
- StoryCredit.creator_id
- Creator.gcd_official_name
- CreatorNameDetail.name
- Issue.key_date (sortable date string)

## Query Performance Considerations

### Efficient Patterns

1. **Get issue credits:**
   ```
   Issue → Story → StoryCredit → CreatorNameDetail → Creator
   ```
   Use index on Story.issue_id

2. **Search series by name:**
   ```
   Series (name LIKE) → Publisher
   ```
   Use index on Series.name

3. **Creator bibliography:**
   ```
   Creator → CreatorNameDetail → StoryCredit → Story → Issue → Series
   ```
   Use indexes on creator_id and story_id

### Expensive Operations

1. **Fuzzy name matching** (use LIKE '%pattern%')
   - Consider full-text search or trigram indexes

2. **Cross-publisher queries**
   - May require scanning large portions of Series table

3. **Character appearance tracking across series**
   - Requires joins through multiple tables

## Integration with Comic-Analysis

### Primary Use Cases

1. **Creator Attribution**
   - Query: Issue → Story → StoryCredit → CreatorNameDetail → Creator
   - Extract: Creator names by role (script, pencils, inks, etc.)

2. **Storyline Information**
   - Query: Issue → Story (where type = 'comic story')
   - Extract: title, feature, genre, synopsis, characters

3. **Age Rating**
   - Query: Issue
   - Extract: rating field

4. **Comic Type/Genre**
   - Query: Series (format, color) + Story (genre)
   - Extract: Series format, story genres

5. **Character Reidentification**
   - Query: Story → StoryCharacter → CharacterNameDetail → Character
   - Extract: Character names, appearances, roles

### Recommended Query Path

For a comic file:
1. Parse filename → extract series_name, issue_number
2. Search Series table (fuzzy match on name)
3. Find Issue (series_id + issue_number match)
4. Get Stories (filter by type = 'comic story')
5. Get StoryCredits for each Story
6. Join to Creator for full creator information

## Schema Evolution Notes

### Legacy Fields
The Story table contains legacy text fields (script, pencils, inks, colors, letters, editing) that predate the structured StoryCredit system. When querying:

1. **Prefer** StoryCredit table for credits
2. **Fall back** to legacy fields if StoryCredit is empty
3. Legacy fields contain unstructured text (names, question marks, etc.)

### Modern GCD Practices
- All new entries use StoryCredit table
- Legacy entries are being gradually migrated
- Both systems coexist in the current database

## Additional Resources

- GCD Schema Migrations: `/apps/gcd/migrations/` in gcd-django repo
- Model Definitions: `/apps/gcd/models/` in gcd-django repo
- GCD Wiki Documentation: https://docs.comics.org/
