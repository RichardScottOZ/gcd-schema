"""
GCD Database Extractor for Comic-Analysis Integration

This module provides utilities to extract creator, storyline, and metadata
information from the Grand Comics Database (GCD) for use in the Comic-Analysis
project.

Usage:
    # Initialize with database connection
    extractor = GCDExtractor(db_path='gcd.sqlite')
    
    # Extract issue information
    issue_data = extractor.get_issue_by_series_and_number('Amazing Spider-Man', '1')
    
    # Get all credits for an issue
    credits = extractor.get_issue_credits(issue_id)
    
    # Search for series
    series_list = extractor.search_series('Spider-Man')

Requirements:
    - GCD database dump loaded into SQLite or MySQL/MariaDB
    - Python 3.8+
    - sqlalchemy (for database abstraction)
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass
class CreatorCredit:
    """Represents a creator credit on a story."""
    creator_name: str
    creator_id: int
    role: str  # script, pencils, inks, colors, letters, editing
    credit_name: Optional[str] = None
    is_credited: bool = False
    is_signed: bool = False
    uncertain: bool = False
    signed_as: Optional[str] = None
    credited_as: Optional[str] = None


@dataclass
class StoryInfo:
    """Represents a story within an issue."""
    story_id: int
    title: Optional[str]
    sequence_number: int
    story_type: str  # cover, comic story, text story, etc.
    page_count: Optional[float]
    feature: Optional[str]
    genre: Optional[str]
    characters: Optional[str]
    synopsis: Optional[str]
    credits: List[CreatorCredit]


@dataclass
class IssueInfo:
    """Represents a comic book issue."""
    issue_id: int
    series_name: str
    series_id: int
    issue_number: str
    volume: Optional[str]
    publication_date: Optional[str]
    publisher: str
    page_count: Optional[int]
    price: Optional[str]
    isbn: Optional[str]
    barcode: Optional[str]
    rating: Optional[str]  # age rating
    stories: List[StoryInfo]


@dataclass
class SeriesInfo:
    """Represents a comic series."""
    series_id: int
    name: str
    publisher: str
    year_began: Optional[int]
    year_ended: Optional[int]
    issue_count: int
    format: Optional[str]
    color: Optional[str]


class FilenameParser:
    """Parse comic filenames to extract metadata."""
    
    # Common patterns for comic filenames
    PATTERNS = [
        # "Series Name 001 (Year).ext"
        r'^(.+?)\s+(\d+)\s*\((\d{4})\)',
        # "Series Name #001.ext"
        r'^(.+?)\s+#(\d+)',
        # "Series Name v1 001.ext"
        r'^(.+?)\s+v(\d+)\s+(\d+)',
        # "Series Name vol 1 #001.ext"
        r'^(.+?)\s+vol\s+(\d+)\s+#?(\d+)',
    ]
    
    @staticmethod
    def parse(filename: str) -> Dict[str, str]:
        """
        Parse a comic filename to extract series name, issue number, etc.
        
        Args:
            filename: Comic filename (e.g., "Amazing Spider-Man 001 (1963).cbz")
            
        Returns:
            Dictionary with keys: series_name, issue_number, volume, year
        """
        # Remove file extension
        name = Path(filename).stem
        
        result = {
            'series_name': None,
            'issue_number': None,
            'volume': None,
            'year': None,
            'original': name
        }
        
        for pattern in FilenameParser.PATTERNS:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                groups = match.groups()
                result['series_name'] = groups[0].strip()
                
                # Pattern-specific extraction
                if len(groups) == 3 and groups[2].isdigit() and len(groups[2]) == 4:
                    # Pattern with year
                    result['issue_number'] = groups[1]
                    result['year'] = groups[2]
                elif len(groups) == 2:
                    # Simple pattern
                    result['issue_number'] = groups[1]
                elif len(groups) == 3:
                    # Pattern with volume
                    result['volume'] = groups[1]
                    result['issue_number'] = groups[2]
                
                break
        
        return result


class GCDExtractor:
    """
    Extract data from GCD database.
    
    This class provides high-level methods to query the GCD database
    and extract information relevant to the Comic-Analysis project.
    """
    
    def __init__(self, connection_string: str = None, db_type: str = 'sqlite'):
        """
        Initialize the extractor.
        
        Args:
            connection_string: Database connection string
                SQLite: 'sqlite:///path/to/gcd.db'
                MySQL: 'mysql://user:pass@localhost/gcd'
            db_type: 'sqlite' or 'mysql'
        """
        self.connection_string = connection_string
        self.db_type = db_type
        self.conn = None
        
        # Note: Actual database connection would be established here
        # using sqlalchemy or direct database drivers
        # For now, this is a template structure
    
    def connect(self):
        """Establish database connection."""
        # Implementation would use sqlalchemy or database-specific drivers
        pass
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def search_series(self, series_name: str, limit: int = 10) -> List[SeriesInfo]:
        """
        Search for series by name (fuzzy matching).
        
        Args:
            series_name: Series name to search for
            limit: Maximum number of results
            
        Returns:
            List of matching SeriesInfo objects
        """
        # SQL query template
        query = """
        SELECT 
            s.id,
            s.name,
            p.name AS publisher,
            s.year_began,
            s.year_ended,
            COUNT(i.id) AS issue_count,
            s.format,
            s.color
        FROM gcd_series s
        JOIN gcd_publisher p ON s.publisher_id = p.id
        LEFT JOIN gcd_issue i ON i.series_id = s.id
        WHERE s.name LIKE ?
        GROUP BY s.id, s.name, p.name, s.year_began, s.year_ended, s.format, s.color
        ORDER BY s.year_began DESC, s.name
        LIMIT ?
        """
        
        # Implementation would execute query and return results
        # This is a template showing the expected structure
        return []
    
    def get_issue_by_series_and_number(
        self, 
        series_name: str, 
        issue_number: str,
        volume: Optional[str] = None
    ) -> Optional[IssueInfo]:
        """
        Find an issue by series name and issue number.
        
        Args:
            series_name: Name of the series
            issue_number: Issue number (as string, e.g., "1", "Annual 1")
            volume: Optional volume number
            
        Returns:
            IssueInfo object if found, None otherwise
        """
        # SQL query template
        query = """
        SELECT 
            i.id,
            s.name AS series_name,
            s.id AS series_id,
            i.number,
            i.volume,
            i.publication_date,
            p.name AS publisher,
            i.page_count,
            i.price,
            i.isbn,
            i.barcode,
            i.rating
        FROM gcd_issue i
        JOIN gcd_series s ON i.series_id = s.id
        JOIN gcd_publisher p ON s.publisher_id = p.id
        WHERE s.name LIKE ?
          AND i.number = ?
        """
        
        if volume:
            query += " AND i.volume = ?"
        
        query += " LIMIT 1"
        
        # Implementation would execute query, then get stories
        # This is a template showing the expected structure
        return None
    
    def get_issue_credits(self, issue_id: int) -> List[CreatorCredit]:
        """
        Get all creator credits for an issue (across all stories).
        
        Args:
            issue_id: GCD issue ID
            
        Returns:
            List of CreatorCredit objects
        """
        query = """
        SELECT DISTINCT
            c.gcd_official_name AS creator_name,
            c.id AS creator_id,
            ct.name AS role,
            sc.credit_name,
            sc.is_credited,
            sc.is_signed,
            sc.uncertain,
            sc.signed_as,
            sc.credited_as
        FROM gcd_storycredit sc
        JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
        JOIN gcd_creator c ON cnd.creator_id = c.id
        JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
        JOIN gcd_story s ON sc.story_id = s.id
        JOIN gcd_storytype st ON s.type_id = st.id
        WHERE s.issue_id = ?
          AND st.name = 'comic story'
        ORDER BY ct.sort_code, c.gcd_official_name
        """
        
        # Implementation would execute query and return results
        return []
    
    def get_issue_stories(self, issue_id: int) -> List[StoryInfo]:
        """
        Get all stories in an issue with their credits.
        
        Args:
            issue_id: GCD issue ID
            
        Returns:
            List of StoryInfo objects
        """
        # First get stories
        story_query = """
        SELECT 
            s.id AS story_id,
            s.title,
            s.sequence_number,
            st.name AS story_type,
            s.page_count,
            s.feature,
            s.genre,
            s.characters,
            s.synopsis
        FROM gcd_story s
        JOIN gcd_storytype st ON s.type_id = st.id
        WHERE s.issue_id = ?
        ORDER BY s.sequence_number
        """
        
        # For each story, get credits
        credits_query = """
        SELECT 
            c.gcd_official_name AS creator_name,
            c.id AS creator_id,
            ct.name AS role,
            sc.credit_name,
            sc.is_credited,
            sc.is_signed,
            sc.uncertain,
            sc.signed_as,
            sc.credited_as
        FROM gcd_storycredit sc
        JOIN gcd_creatornamedetail cnd ON sc.creator_id = cnd.id
        JOIN gcd_creator c ON cnd.creator_id = c.id
        JOIN gcd_credittype ct ON sc.credit_type_id = ct.id
        WHERE sc.story_id = ?
        ORDER BY ct.sort_code
        """
        
        # Implementation would execute queries and build StoryInfo objects
        return []
    
    def get_storyline_info(self, issue_id: int) -> Dict[str, Any]:
        """
        Extract storyline and synopsis information for an issue.
        
        Args:
            issue_id: GCD issue ID
            
        Returns:
            Dictionary with storyline information
        """
        query = """
        SELECT 
            s.title,
            s.feature,
            s.genre,
            s.characters,
            s.synopsis,
            st.name AS story_type
        FROM gcd_story s
        JOIN gcd_storytype st ON s.type_id = st.id
        WHERE s.issue_id = ?
          AND st.name IN ('comic story', 'text story')
        ORDER BY s.sequence_number
        """
        
        # Implementation would combine multiple stories into coherent storyline info
        return {}
    
    def get_age_rating(self, issue_id: int) -> Optional[str]:
        """
        Get age rating for an issue.
        
        Args:
            issue_id: GCD issue ID
            
        Returns:
            Age rating string or None
        """
        query = """
        SELECT rating
        FROM gcd_issue
        WHERE id = ?
        """
        
        return None
    
    def get_character_appearances(self, issue_id: int) -> List[Dict[str, Any]]:
        """
        Get character appearance information for an issue.
        
        Args:
            issue_id: GCD issue ID
            
        Returns:
            List of character appearance dictionaries
        """
        query = """
        SELECT 
            c.name AS character_name,
            cr.name AS role,
            sc.is_flashback,
            sc.is_origin,
            sc.is_death,
            s.title AS story_title
        FROM gcd_storycharacter sc
        JOIN gcd_characternamedetail cnd ON sc.character_id = cnd.id
        JOIN gcd_character c ON cnd.character_id = c.id
        JOIN gcd_story s ON sc.story_id = s.id
        LEFT JOIN gcd_characterrole cr ON sc.role_id = cr.id
        WHERE s.issue_id = ?
        ORDER BY s.sequence_number
        """
        
        return []
    
    def batch_extract(self, comic_files: List[str], output_path: str):
        """
        Extract metadata for a batch of comic files.
        
        Args:
            comic_files: List of comic file paths
            output_path: Path to save extracted data (JSON or Parquet)
        """
        results = []
        parser = FilenameParser()
        
        for file_path in comic_files:
            filename = Path(file_path).name
            parsed = parser.parse(filename)
            
            if parsed['series_name'] and parsed['issue_number']:
                issue = self.get_issue_by_series_and_number(
                    parsed['series_name'],
                    parsed['issue_number'],
                    parsed.get('volume')
                )
                
                if issue:
                    results.append({
                        'file': file_path,
                        'parsed': parsed,
                        'gcd_data': asdict(issue),
                        'matched': True
                    })
                else:
                    results.append({
                        'file': file_path,
                        'parsed': parsed,
                        'matched': False
                    })
            else:
                results.append({
                    'file': file_path,
                    'parsed': parsed,
                    'matched': False,
                    'error': 'Could not parse filename'
                })
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results


def create_hybrid_extractor(gcd_db: str, vlm_client=None):
    """
    Create a hybrid extractor that uses GCD database first,
    then falls back to VLM extraction for unmatched comics.
    
    This implements the hybrid approach recommended in Comic-Databases.md
    
    Args:
        gcd_db: Path to GCD database
        vlm_client: Optional VLM client for fallback extraction
        
    Returns:
        Configured GCDExtractor instance
    """
    extractor = GCDExtractor(connection_string=f'sqlite:///{gcd_db}')
    
    # Add VLM fallback logic here
    # If GCD lookup fails, extract first 5 pages and use VLM
    
    return extractor


# Example usage
if __name__ == '__main__':
    # Initialize extractor
    extractor = GCDExtractor(connection_string='sqlite:///gcd.db')
    
    # Parse a filename
    parser = FilenameParser()
    parsed = parser.parse('Amazing Spider-Man 001 (1963).cbz')
    print(f"Parsed: {parsed}")
    
    # Search for series
    series = extractor.search_series('Spider-Man')
    print(f"Found {len(series)} series")
    
    # Get issue information
    issue = extractor.get_issue_by_series_and_number('Amazing Spider-Man', '1')
    if issue:
        print(f"Issue: {issue.series_name} #{issue.issue_number}")
        print(f"Publisher: {issue.publisher}")
        print(f"Credits:")
        
        credits = extractor.get_issue_credits(issue.issue_id)
        for credit in credits:
            print(f"  {credit.creator_name} - {credit.role}")
    
    # Batch process multiple files
    comic_files = [
        'Amazing Spider-Man 001 (1963).cbz',
        'Batman 400.cbr',
        '2000 AD Prog 2000.pdf',
    ]
    
    results = extractor.batch_extract(comic_files, 'extraction_results.json')
    print(f"Processed {len(results)} files")
    
    extractor.close()
