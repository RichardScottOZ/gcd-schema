# GCD SQL Query Examples

This document provides practical SQL query examples for extracting data from the Grand Comics Database for the Comic-Analysis project.

## Table of Contents
1. [Basic Queries](#basic-queries)
2. [Creator Attribution](#creator-attribution)
3. [Storyline Extraction](#storyline-extraction)
4. [Character Tracking](#character-tracking)
5. [Series and Publisher Info](#series-and-publisher-info)
6. [Complex Analytical Queries](#complex-analytical-queries)

## Basic Queries

### Find Series by Name

```sql
-- Simple search
SELECT 
    id,
    name,
    year_began,
    year_ended,
    publisher_id
FROM gcd_series
WHERE name LIKE '%Spider-Man%'
ORDER BY year_began;

-- With publisher information
SELECT 
    s.id,
    s.name,
    s.year_began,
    s.year_ended,
    p.name AS publisher
FROM gcd_series s
JOIN gcd_publisher p ON s.publisher_id = p.id
WHERE s.name LIKE '%Spider-Man%'
ORDER BY p.name, s.year_began;
```

### Find Issue by Series and Number

```sql
-- Basic issue lookup
SELECT 
    i.id,
    i.number,
    i.volume,
    i.publication_date,
    i.key_date,
    s.name AS series_name,
    p.name AS publisher
FROM gcd_issue i
JOIN gcd_series s ON i.series_id = s.id
JOIN gcd_publisher p ON s.publisher_id = p.id
WHERE s.name = 'Amazing Spider-Man'
  AND i.number = '1'
  AND s.year_began = 1963;
```

### Get Issue Count for a Series

```sql
SELECT 
    s.name,
    s.year_began,
    COUNT(i.id) AS issue_count,
    MIN(i.key_date) AS first_issue_date,
    MAX(i.key_date) AS last_issue_date
FROM gcd_series s
LEFT JOIN gcd_issue i ON i.series_id = s.id
WHERE s.name LIKE '%Batman%'
GROUP BY s.id, s.name, s.year_began
ORDER BY s.year_began;
```

## Creator Attribution

### Get All Credits for an Issue

```sql
-- Using StoryCredit table (modern, structured)
SELECT 
    c.gcd_official_name AS creator_name,
    c.id AS creator_id,
    cnd.name AS credited_name,
    ct.name AS role,
    ct.sort_code,
    sc.is_credited,
    sc.is_signed,
    sc.uncertain,
    s.title AS story_title,
    st.name AS story_type
FROM gcd_storycredit sc
JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
JOIN gcd_creator c ON cnd.creator_id = c.id
JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
JOIN gcd_story s ON sc.story_id = s.id
JOIN gcd_storytype st ON s.type_id = st.id
WHERE s.issue_id = 12345  -- Replace with actual issue ID
  AND st.name = 'comic story'
ORDER BY s.sequence_number, ct.sort_code;
```

### Get Credits Grouped by Role

```sql
-- Aggregate credits by role
SELECT 
    ct.name AS role,
    ct.sort_code,
    GROUP_CONCAT(
        DISTINCT c.gcd_official_name 
        ORDER BY c.gcd_official_name 
        SEPARATOR '; '
    ) AS creators
FROM gcd_storycredit sc
JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
JOIN gcd_creator c ON cnd.creator_id = c.id
JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
JOIN gcd_story s ON sc.story_id = s.id
JOIN gcd_storytype st ON s.type_id = st.id
WHERE s.issue_id = 12345
  AND st.name = 'comic story'
GROUP BY ct.name, ct.sort_code
ORDER BY ct.sort_code;
```

### Get Creator Bibliography

```sql
-- All works by a creator
SELECT 
    s.name AS series_name,
    i.number AS issue_number,
    i.publication_date,
    st.title AS story_title,
    ct.name AS role,
    stype.name AS story_type,
    p.name AS publisher
FROM gcd_storycredit sc
JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
JOIN gcd_creator c ON cnd.creator_id = c.id
JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
JOIN gcd_story st ON sc.story_id = st.id
JOIN gcd_storytype stype ON st.type_id = stype.id
JOIN gcd_issue i ON st.issue_id = i.id
JOIN gcd_series s ON i.series_id = s.id
JOIN gcd_publisher p ON s.publisher_id = p.id
WHERE c.gcd_official_name = 'Stan Lee'
  AND stype.name = 'comic story'
ORDER BY i.key_date, s.sort_name;
```

### Find Collaborations Between Creators

```sql
-- Find issues where two creators worked together
SELECT 
    s.name AS series_name,
    i.number AS issue_number,
    i.publication_date,
    st.title AS story_title,
    c1.gcd_official_name AS creator1_name,
    ct1.name AS creator1_role,
    c2.gcd_official_name AS creator2_name,
    ct2.name AS creator2_role
FROM gcd_storycredit sc1
JOIN gcd_storycredit sc2 ON sc1.story_id = sc2.story_id AND sc1.id != sc2.id
JOIN gcd_creatornamedetail cnd1 ON sc1.creator_id = cnd1.id
JOIN gcd_creatornamedetail cnd2 ON sc2.creator_id = cnd2.id
JOIN gcd_creator c1 ON cnd1.creator_id = c1.id
JOIN gcd_creator c2 ON cnd2.creator_id = c2.id
JOIN gcd_credittype ct1 ON sc1.credit_type_id = ct1.id
JOIN gcd_credittype ct2 ON sc2.credit_type_id = ct2.id
JOIN gcd_story st ON sc1.story_id = st.id
JOIN gcd_issue i ON st.issue_id = i.id
JOIN gcd_series s ON i.series_id = s.id
WHERE c1.gcd_official_name = 'Stan Lee'
  AND c2.gcd_official_name = 'Jack Kirby'
ORDER BY i.key_date;
```

## Storyline Extraction

### Get Stories from an Issue

```sql
-- All stories with metadata
SELECT 
    s.id AS story_id,
    s.sequence_number,
    st.name AS story_type,
    s.title,
    s.feature,
    s.genre,
    s.page_count,
    s.characters,
    s.synopsis,
    s.notes
FROM gcd_story s
JOIN gcd_storytype st ON s.type_id = st.id
WHERE s.issue_id = 12345
ORDER BY s.sequence_number;
```

### Get Comic Story Content Only (No Ads, etc.)

```sql
-- Filter to narrative content
SELECT 
    s.sequence_number,
    s.title,
    s.feature,
    s.genre,
    s.characters,
    s.synopsis,
    s.page_count
FROM gcd_story s
JOIN gcd_storytype st ON s.type_id = st.id
WHERE s.issue_id = 12345
  AND st.name IN ('comic story', 'text story')
ORDER BY s.sequence_number;
```

### Get Story Type Distribution

```sql
-- Count story types in an issue
SELECT 
    st.name AS story_type,
    COUNT(*) AS count,
    SUM(s.page_count) AS total_pages
FROM gcd_story s
JOIN gcd_storytype st ON s.type_id = st.id
WHERE s.issue_id = 12345
GROUP BY st.name
ORDER BY total_pages DESC;
```

### Find Stories by Genre

```sql
-- Search stories by genre
SELECT 
    s.name AS series_name,
    i.number AS issue_number,
    st.title AS story_title,
    st.genre,
    st.page_count
FROM gcd_story st
JOIN gcd_issue i ON st.issue_id = i.id
JOIN gcd_series s ON i.series_id = s.id
WHERE st.genre LIKE '%horror%'
  AND st.type_id = (SELECT id FROM gcd_storytype WHERE name = 'comic story')
ORDER BY i.key_date DESC
LIMIT 100;
```

### Extract Synopsis Text

```sql
-- Get all synopses for a series
SELECT 
    i.number AS issue_number,
    st.title,
    st.synopsis
FROM gcd_story st
JOIN gcd_issue i ON st.issue_id = i.id
JOIN gcd_series s ON i.series_id = s.id
WHERE s.name = 'Amazing Spider-Man'
  AND s.year_began = 1963
  AND st.synopsis IS NOT NULL
  AND st.synopsis != ''
  AND st.type_id = (SELECT id FROM gcd_storytype WHERE name = 'comic story')
ORDER BY i.key_date;
```

## Character Tracking

### Get Character Appearances in an Issue

```sql
-- All characters in an issue
SELECT 
    c.name AS character_name,
    cnd.name AS name_variant,
    cr.name AS role,
    u.name AS universe,
    sc.is_flashback,
    sc.is_origin,
    sc.is_death,
    s.title AS story_title,
    s.sequence_number
FROM gcd_storycharacter sc
JOIN gcd_characternamedetail cnd ON sc.character_id = cnd.id
JOIN gcd_character c ON cnd.character_id = c.id
LEFT JOIN gcd_characterrole cr ON sc.role_id = cr.id
LEFT JOIN gcd_universe u ON sc.universe_id = u.id
JOIN gcd_story s ON sc.story_id = s.id
WHERE s.issue_id = 12345
ORDER BY s.sequence_number, cr.sort_code;
```

### Track Character Across Series

```sql
-- All appearances of a character
SELECT 
    s.name AS series_name,
    i.number AS issue_number,
    i.publication_date,
    st.title AS story_title,
    cr.name AS role,
    sc.is_origin,
    sc.is_death
FROM gcd_storycharacter sc
JOIN gcd_characternamedetail cnd ON sc.character_id = cnd.id
JOIN gcd_character c ON cnd.character_id = c.id
JOIN gcd_story st ON sc.story_id = st.id
JOIN gcd_issue i ON st.issue_id = i.id
JOIN gcd_series s ON i.series_id = s.id
LEFT JOIN gcd_characterrole cr ON sc.role_id = cr.id
WHERE c.name = 'Spider-Man'
  AND cnd.is_primary = TRUE
ORDER BY i.key_date, s.name;
```

### Find Origin Stories

```sql
-- Character origin stories
SELECT 
    c.name AS character_name,
    s.name AS series_name,
    i.number AS issue_number,
    i.publication_date,
    st.title AS story_title
FROM gcd_storycharacter sc
JOIN gcd_characternamedetail cnd ON sc.character_id = cnd.id
JOIN gcd_character c ON cnd.character_id = c.id
JOIN gcd_story st ON sc.story_id = st.id
JOIN gcd_issue i ON st.issue_id = i.id
JOIN gcd_series s ON i.series_id = s.id
WHERE sc.is_origin = TRUE
  AND c.name LIKE '%Spider%'
ORDER BY i.key_date;
```

### Get Character's Team Affiliations

```sql
-- Groups a character appears with
SELECT DISTINCT
    c.name AS character_name,
    g.name AS group_name,
    s.name AS series_name,
    COUNT(*) AS appearance_count
FROM gcd_storycharacter sc
JOIN gcd_characternamedetail cnd ON sc.character_id = cnd.id
JOIN gcd_character c ON cnd.character_id = c.id
JOIN gcd_storycharacter_group scg ON sc.id = scg.storycharacter_id
JOIN gcd_group g ON scg.group_id = g.id
JOIN gcd_story st ON sc.story_id = st.id
JOIN gcd_issue i ON st.issue_id = i.id
JOIN gcd_series s ON i.series_id = s.id
WHERE c.name = 'Spider-Man'
GROUP BY c.name, g.name, s.name
ORDER BY appearance_count DESC;
```

## Series and Publisher Info

### Get Complete Series Information

```sql
-- Detailed series metadata
SELECT 
    s.id,
    s.name,
    s.sort_name,
    s.year_began,
    s.year_ended,
    s.publication_dates,
    s.format,
    s.color,
    s.dimensions,
    s.paper_stock,
    s.binding,
    s.publishing_format,
    p.name AS publisher,
    c.name AS country,
    l.name AS language,
    COUNT(i.id) AS issue_count
FROM gcd_series s
JOIN gcd_publisher p ON s.publisher_id = p.id
JOIN gcd_country c ON s.country_id = c.id
JOIN gcd_language l ON s.language_id = l.id
LEFT JOIN gcd_issue i ON i.series_id = s.id
WHERE s.name = 'Amazing Spider-Man'
  AND s.year_began = 1963
GROUP BY s.id;
```

### Get Publisher's Series

```sql
-- All series by a publisher
SELECT 
    s.name,
    s.year_began,
    s.year_ended,
    s.format,
    COUNT(i.id) AS issue_count
FROM gcd_series s
JOIN gcd_publisher p ON s.publisher_id = p.id
LEFT JOIN gcd_issue i ON i.series_id = s.id
WHERE p.name = 'Marvel Comics'
  AND s.year_began >= 1960
  AND s.year_began < 1970
GROUP BY s.id, s.name, s.year_began, s.year_ended, s.format
ORDER BY s.year_began, s.name;
```

### Find Series Relationships (Spin-offs, Continuations)

```sql
-- Related series
SELECT 
    s1.name AS from_series,
    rt.name AS relationship_type,
    s2.name AS to_series,
    sb.notes
FROM gcd_seriesbond sb
JOIN gcd_series s1 ON sb.origin_id = s1.id
JOIN gcd_series s2 ON sb.target_id = s2.id
JOIN gcd_seriesbondtype rt ON sb.bond_type_id = rt.id
WHERE s1.name LIKE '%Spider-Man%'
ORDER BY s1.year_began, s2.year_began;
```

## Complex Analytical Queries

### Creator Productivity by Year

```sql
-- Count stories by creator per year
SELECT 
    YEAR(i.key_date) AS year,
    c.gcd_official_name AS creator_name,
    ct.name AS role,
    COUNT(DISTINCT st.id) AS story_count,
    COUNT(DISTINCT i.id) AS issue_count
FROM gcd_storycredit sc
JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
JOIN gcd_creator c ON cnd.creator_id = c.id
JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
JOIN gcd_story st ON sc.story_id = st.id
JOIN gcd_issue i ON st.issue_id = i.id
WHERE c.gcd_official_name = 'Stan Lee'
  AND i.key_date IS NOT NULL
GROUP BY year, c.gcd_official_name, ct.name
ORDER BY year, ct.sort_code;
```

### Most Prolific Creator Collaborations

```sql
-- Top creator pairs
SELECT 
    c1.gcd_official_name AS creator1,
    c2.gcd_official_name AS creator2,
    ct1.name AS role1,
    ct2.name AS role2,
    COUNT(DISTINCT st.id) AS collaboration_count
FROM gcd_storycredit sc1
JOIN gcd_storycredit sc2 ON sc1.story_id = sc2.story_id AND sc1.id < sc2.id
JOIN gcd_creatornamedetail cnd1 ON sc1.creator_id = cnd1.id
JOIN gcd_creatornamedetail cnd2 ON sc2.creator_id = cnd2.id
JOIN gcd_creator c1 ON cnd1.creator_id = c1.id
JOIN gcd_creator c2 ON cnd2.creator_id = c2.id
JOIN gcd_credittype ct1 ON sc1.credit_type_id = ct1.id
JOIN gcd_credittype ct2 ON sc2.credit_type_id = ct2.id
JOIN gcd_story st ON sc1.story_id = st.id
WHERE ct1.name = 'script'
  AND ct2.name = 'pencils'
GROUP BY c1.id, c2.id, ct1.name, ct2.name
ORDER BY collaboration_count DESC
LIMIT 20;
```

### Issues with Age Ratings

```sql
-- Distribution of age ratings
SELECT 
    i.rating,
    COUNT(*) AS issue_count,
    MIN(i.key_date) AS earliest,
    MAX(i.key_date) AS latest
FROM gcd_issue i
WHERE i.rating IS NOT NULL
  AND i.rating != ''
GROUP BY i.rating
ORDER BY issue_count DESC;
```

### Genre Analysis by Publisher

```sql
-- Genre distribution by publisher
SELECT 
    p.name AS publisher,
    s.genre,
    COUNT(*) AS story_count
FROM gcd_story s
JOIN gcd_issue i ON s.issue_id = i.id
JOIN gcd_series ser ON i.series_id = ser.id
JOIN gcd_publisher p ON ser.publisher_id = p.id
WHERE s.genre IS NOT NULL
  AND s.genre != ''
  AND p.name IN ('Marvel Comics', 'DC Comics')
GROUP BY p.name, s.genre
ORDER BY p.name, story_count DESC;
```

### Batch Issue Lookup for Comic Collection

```sql
-- Find multiple issues at once
SELECT 
    s.name AS series_name,
    i.number AS issue_number,
    i.id AS issue_id,
    i.publication_date,
    p.name AS publisher
FROM gcd_issue i
JOIN gcd_series s ON i.series_id = s.id
JOIN gcd_publisher p ON s.publisher_id = p.id
WHERE (s.name = 'Amazing Spider-Man' AND i.number = '1')
   OR (s.name = 'Batman' AND i.number = '400')
   OR (s.name = 'X-Men' AND i.number = '1')
ORDER BY s.name, CAST(i.number AS UNSIGNED);
```

### Get Page-Level Story Mapping

```sql
-- Calculate cumulative page positions for stories
SELECT 
    s.sequence_number,
    st.name AS story_type,
    s.title,
    s.page_count,
    SUM(COALESCE(s2.page_count, 0)) AS start_page,
    SUM(COALESCE(s2.page_count, 0)) + COALESCE(s.page_count, 0) - 1 AS end_page
FROM gcd_story s
JOIN gcd_storytype st ON s.type_id = st.id
LEFT JOIN gcd_story s2 ON s2.issue_id = s.issue_id 
    AND s2.sequence_number < s.sequence_number
WHERE s.issue_id = 12345
GROUP BY s.id, s.sequence_number, st.name, s.title, s.page_count
ORDER BY s.sequence_number;
```

### Find Issues Missing Credits

```sql
-- Issues with no creator credits
SELECT 
    s.name AS series_name,
    i.number AS issue_number,
    i.publication_date,
    COUNT(DISTINCT st.id) AS story_count
FROM gcd_issue i
JOIN gcd_series s ON i.series_id = s.id
JOIN gcd_story st ON st.issue_id = i.id
LEFT JOIN gcd_storycredit sc ON sc.story_id = st.id
WHERE sc.id IS NULL
  AND st.type_id = (SELECT id FROM gcd_storytype WHERE name = 'comic story')
  AND s.name = 'Amazing Spider-Man'
GROUP BY i.id, s.name, i.number, i.publication_date
ORDER BY i.key_date;
```

## Performance Optimization

### Add Custom Indexes

```sql
-- Recommended indexes for Comic-Analysis queries
CREATE INDEX idx_series_name ON gcd_series(name);
CREATE INDEX idx_issue_number ON gcd_issue(number);
CREATE INDEX idx_story_issue ON gcd_story(issue_id);
CREATE INDEX idx_storycredit_story ON gcd_storycredit(story_id);
CREATE INDEX idx_storycredit_creator ON gcd_storycredit(creator_id);
CREATE INDEX idx_issue_keydate ON gcd_issue(key_date);
```

### Use Prepared Statements

```python
# Python example with parameterized query
query = """
SELECT i.id, i.number, s.name
FROM gcd_issue i
JOIN gcd_series s ON i.series_id = s.id
WHERE s.name = %s AND i.number = %s
"""
cursor.execute(query, (series_name, issue_number))
```

### Batch Queries with IN Clause

```sql
-- Look up multiple issues efficiently
SELECT 
    i.id,
    s.name AS series_name,
    i.number
FROM gcd_issue i
JOIN gcd_series s ON i.series_id = s.id
WHERE i.id IN (12345, 12346, 12347, 12348, 12349);
```

## Tips for Working with GCD Data

### Handle Legacy vs. Modern Credits

```sql
-- Check if modern credits exist, fall back to legacy
SELECT 
    s.id AS story_id,
    -- Modern credits (preferred)
    (SELECT GROUP_CONCAT(c.gcd_official_name) 
     FROM gcd_storycredit sc
     JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
     JOIN gcd_creator c ON cnd.creator_id = c.id
     WHERE sc.story_id = s.id 
       AND sc.credit_type_id = (SELECT id FROM gcd_credittype WHERE name = 'script')
    ) AS modern_script,
    -- Legacy credit field (fallback)
    s.script AS legacy_script,
    -- Use COALESCE to prefer modern
    COALESCE(
        (SELECT GROUP_CONCAT(c.gcd_official_name) 
         FROM gcd_storycredit sc
         JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
         JOIN gcd_creator c ON cnd.creator_id = c.id
         WHERE sc.story_id = s.id 
           AND sc.credit_type_id = (SELECT id FROM gcd_credittype WHERE name = 'script')
        ),
        s.script
    ) AS final_script
FROM gcd_story s
WHERE s.issue_id = 12345;
```

### Fuzzy Series Name Matching

```sql
-- Handle variations in series names
SELECT 
    id,
    name,
    year_began,
    CASE 
        WHEN name LIKE 'The %' THEN SUBSTRING(name, 5)
        ELSE name
    END AS normalized_name
FROM gcd_series
WHERE normalized_name LIKE '%spider%man%'
   OR normalized_name LIKE '%spiderman%'
ORDER BY year_began;
```

### Parse Genre Lists

```sql
-- Extract individual genres from comma-separated field
SELECT DISTINCT
    TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(genre, ';', numbers.n), ';', -1)) AS individual_genre
FROM gcd_story
CROSS JOIN (
    SELECT 1 n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
) numbers
WHERE genre IS NOT NULL
  AND CHAR_LENGTH(genre) - CHAR_LENGTH(REPLACE(genre, ';', '')) >= numbers.n - 1
ORDER BY individual_genre;
```

## Complete Example: Extract Full Issue Data

```sql
-- Single query to get everything for an issue
SELECT 
    -- Issue info
    i.id AS issue_id,
    i.number,
    i.publication_date,
    i.page_count,
    i.price,
    i.rating,
    -- Series info
    s.id AS series_id,
    s.name AS series_name,
    s.year_began,
    s.volume,
    -- Publisher info
    p.name AS publisher,
    -- Story info
    st.id AS story_id,
    st.sequence_number,
    stype.name AS story_type,
    st.title AS story_title,
    st.feature,
    st.genre,
    st.page_count AS story_pages,
    -- Creator info (requires separate queries or concatenation)
    GROUP_CONCAT(
        DISTINCT CONCAT(c.gcd_official_name, ':', ct.name)
        SEPARATOR '; '
    ) AS credits
FROM gcd_issue i
JOIN gcd_series s ON i.series_id = s.id
JOIN gcd_publisher p ON s.publisher_id = p.id
JOIN gcd_story st ON st.issue_id = i.id
JOIN gcd_storytype stype ON st.type_id = stype.id
LEFT JOIN gcd_storycredit sc ON sc.story_id = st.id
LEFT JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
LEFT JOIN gcd_creator c ON cnd.creator_id = c.id
LEFT JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
WHERE i.id = 12345
GROUP BY 
    i.id, i.number, i.publication_date, i.page_count, i.price, i.rating,
    s.id, s.name, s.year_began, s.volume,
    p.name,
    st.id, st.sequence_number, stype.name, st.title, st.feature, st.genre, st.page_count
ORDER BY st.sequence_number;
```

## Notes

1. **Issue IDs:** Replace `12345` with actual GCD issue IDs from your queries
2. **NULL Handling:** Use `COALESCE()` or `IFNULL()` for fields that may be NULL
3. **Text Encoding:** GCD uses UTF-8, ensure your client connection uses UTF-8
4. **Date Formats:** `key_date` is a string (YYYY-MM-DD), use DATE functions for comparisons
5. **Performance:** Add LIMIT clauses when testing queries on large datasets
