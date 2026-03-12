"""Resume parser module for extracting text from PDF resumes."""

from typing import Optional
from pathlib import Path

from PyPDF2 import PdfReader


class ResumeParser:
    """Extract and parse text from PDF resume files."""

    @staticmethod
    def extract_text(pdf_path: str) -> Optional[str]:
        """
        Extract all text from a PDF resume.
        
        Args:
            pdf_path: Path to the PDF resume file
            
        Returns:
            Full resume text as a single string, or None if parsing fails
            
        Raises:
            FileNotFoundError: If the PDF file does not exist
            ValueError: If the file is not a valid PDF
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"Resume file not found: {pdf_path}")
        
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"File must be a PDF, got: {pdf_path.suffix}")
        
        try:
            reader = PdfReader(pdf_path)
            
            if len(reader.pages) == 0:
                return None
            
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            
            # Join all pages with page separator
            full_text = "\n\n--- PAGE BREAK ---\n\n".join(text)
            return full_text
        
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {e}")

    @staticmethod
    def extract_skills(resume_text: str) -> list[str]:
        """
        Extract common programming skills and technologies from resume text.
        
        Args:
            resume_text: Full resume text
            
        Returns:
            List of identified skills (case-insensitive)
        """
        # Common technical skills/keywords to look for
        common_skills = {
            # Programming languages
            "python", "javascript", "java", "c++", "csharp", "c#", "php", "ruby", "go", "rust",
            "typescript", "kotlin", "swift", "objective-c", "perl", "r", "matlab", "scala",
            
            # Web frameworks
            "django", "flask", "fastapi", "react", "angular", "vue", "next.js", "nextjs",
            "express", "node.js", "nodejs", "spring", "asp.net", "laravel", "rails",
            
            # Databases
            "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
            "dynamodb", "cassandra", "oracle", "sqlite", "firestore",
            
            # Cloud/DevOps
            "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s", "jenkins",
            "terraform", "ansible", "ci/cd", "devops",
            
            # Data/ML
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "spark", "hadoop",
            "machine learning", "deep learning", "nlp", "computer vision",
            
            # Tools/Platforms
            "git", "github", "gitlab", "jira", "confluence", "linux", "windows", "macos",
            "unix", "shell", "bash", "rest", "graphql", "grpc", "soap",
            
            # Methodologies
            "agile", "scrum", "kanban", "waterfall", "tdd", "bdd",
        }
        
        # Convert resume to lowercase for matching
        resume_lower = resume_text.lower()
        
        # Find all skills that appear in the resume
        found_skills = []
        for skill in common_skills:
            # Use word boundaries to avoid partial matches (e.g., "c#" matching "react")
            import re
            # Match skill as whole word or with common separators
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, resume_lower):
                found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates

    @staticmethod
    def extract_text_sections(resume_text: str) -> dict[str, str]:
        """
        Attempt to segment resume into common sections.
        
        Args:
            resume_text: Full resume text
            
        Returns:
            Dictionary with sections (e.g., "summary", "experience", "skills", etc.)
        """
        sections = {
            "full_text": resume_text,
            "summary": "",
            "experience": "",
            "skills": "",
            "education": "",
            "projects": "",
        }
        
        # Common section headers (case-insensitive)
        section_patterns = {
            "summary": [r"(?:professional\s)?summary", r"objective", r"about\s(?:me|myself)"],
            "experience": [r"(?:work\s)?experience", r"employment", r"professional\s(?:history|background)"],
            "skills": [r"skills", r"technical\s(?:skills|expertise)", r"core\s(?:competencies|skills)"],
            "education": [r"education", r"academic", r"degrees?", r"certifications?"],
            "projects": [r"projects?", r"portfolio", r"(?:notable\s)?work"],
        }
        
        import re
        resume_lower = resume_text.lower()
        
        # Try to identify section boundaries
        section_starts = {}
        for section, patterns in section_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, resume_lower)
                if match:
                    section_starts[section] = match.start()
                    break
        
        # Sort sections by position
        sorted_sections = sorted(section_starts.items(), key=lambda x: x[1])
        
        # Extract text between section headers
        for i, (section, start) in enumerate(sorted_sections):
            if i + 1 < len(sorted_sections):
                end = sorted_sections[i + 1][1]
                sections[section] = resume_text[start:end].strip()
            else:
                sections[section] = resume_text[start:].strip()
        
        return sections


def main():
    """Example usage of ResumeParser."""
    # Example (requires a sample.pdf in the current directory)
    try:
        parser = ResumeParser()
        
        # Extract full text
        text = parser.extract_text("sample.pdf")
        print("Resume text extracted successfully")
        print(f"Total characters: {len(text)}")
        print()
        
        # Extract skills
        skills = parser.extract_skills(text)
        print(f"Identified skills ({len(skills)}):")
        print(", ".join(skills))
        print()
        
        # Extract sections
        sections = parser.extract_text_sections(text)
        print("Sections found:")
        for section, content in sections.items():
            if section != "full_text" and content:
                print(f"  - {section}: {len(content)} characters")
    
    except FileNotFoundError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
