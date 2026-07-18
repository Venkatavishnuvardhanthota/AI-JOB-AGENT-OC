import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class ResumeParserService:
    SECTION_PATTERNS = [
        re.compile(r"^(education|academic|academic\s+background)(?!\w)", re.IGNORECASE),
        re.compile(r"^(experience|work\s+experience|professional\s+experience|employment)(?!\w)", re.IGNORECASE),
        re.compile(r"^(skills|technical\s+skills|core\s+competencies|expertise)(?!\w)", re.IGNORECASE),
        re.compile(r"^(projects|project\s+experience|key\s+projects)(?!\w)", re.IGNORECASE),
        re.compile(r"^(certifications|certification|certificates|licenses)(?!\w)", re.IGNORECASE),
        re.compile(r"^(summary|professional\s+summary|profile|objective|about\s+me)(?!\w)", re.IGNORECASE),
        re.compile(r"^(languages|language)(?!\w)", re.IGNORECASE),
        re.compile(r"^(publications|patents)(?!\w)", re.IGNORECASE),
        re.compile(r"^(awards|honors|achievements)(?!\w)", re.IGNORECASE),
        re.compile(r"^(volunteer|volunteering)(?!\w)", re.IGNORECASE),
    ]

    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
    URL_PATTERN = re.compile(r"(https?://[^\s]+)")
    DATE_PATTERN = re.compile(
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]*\d{4}|"
        r"\d{4}[\s-]+\d{4}|\d{4}|"
        r"(?:19|20)\d{2})"
    )

    def parse_text(self, text: str) -> dict:
        sections = self._split_into_sections(text)
        result: dict = {}

        for section_name, section_text in sections.items():
            if section_name in ("summary", "professional summary", "profile", "objective", "about me"):
                result["summary"] = section_text.strip()[:1000]
            elif section_name in ("education", "academic", "academic background"):
                result["education"] = self._parse_education_section(section_text)
            elif section_name in ("experience", "work experience", "professional experience", "employment"):
                result["experience"] = self._parse_experience_section(section_text)
            elif section_name in ("skills", "technical skills", "core competencies", "expertise"):
                result["skills"] = self._parse_skills_section(section_text)
            elif section_name in ("projects", "project experience", "key projects"):
                result["projects"] = self._parse_projects_section(section_text)
            elif section_name in ("certifications", "certification", "certificates", "licenses"):
                result["certifications"] = self._parse_certifications_section(section_text)
            elif section_name in ("languages", "language"):
                result["languages"] = self._parse_languages_section(section_text)

        contact = self._extract_contact(text)
        result.update(contact)

        name = self._extract_name(text, sections)
        if name:
            result["full_name"] = name

        return result

    def parse_file(self, file_path: str) -> dict:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        text = ""

        if ext == ".docx":
            text = self._read_docx(path)
        elif ext == ".pdf":
            text = self._read_pdf(path)
        elif ext == ".txt":
            text = path.read_text(encoding="utf-8", errors="ignore")
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return self.parse_text(text)

    def _read_docx(self, path: Path) -> str:
        try:
            from docx import Document
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            logger.warning("python-docx not available, using fallback")
            return path.read_text(encoding="utf-8", errors="ignore")

    def _read_pdf(self, path: Path) -> str:
        try:
            import fitz
            doc = fitz.open(str(path))
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        except ImportError:
            logger.warning("PyMuPDF not available, trying fallback")
            try:
                import pdfplumber
                with pdfplumber.open(str(path)) as pdf:
                    return "\n".join(page.extract_text() or "" for page in pdf.pages)
            except ImportError:
                logger.warning("pdfplumber not available either")
                return path.read_text(encoding="utf-8", errors="ignore")

    def _split_into_sections(self, text: str) -> dict[str, str]:
        lines = text.split("\n")
        sections: dict[str, str] = {}
        current_section = "header"
        current_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                current_lines.append(line)
                continue
            matched = False
            for pattern in self.SECTION_PATTERNS:
                m = pattern.match(stripped)
                if m:
                    sections[current_section] = "\n".join(current_lines).strip()
                    current_section = m.group(1).lower().strip()
                    current_lines = []
                    rest = stripped[m.end():].strip().strip(":;,")
                    if rest:
                        current_lines.append(rest)
                    matched = True
                    break
            if not matched:
                current_lines.append(line)

        sections[current_section] = "\n".join(current_lines).strip()
        return sections

    def _extract_contact(self, text: str) -> dict:
        contact: dict = {}
        emails = self.EMAIL_PATTERN.findall(text)
        if emails:
            contact["email"] = emails[0]
        phones = self.PHONE_PATTERN.findall(text)
        if phones:
            phone_matches = self.PHONE_PATTERN.finditer(text)
            for pm in phone_matches:
                full_match = pm.group(0).strip()
                if full_match:
                    contact["phone"] = full_match
                    break
        urls = self.URL_PATTERN.findall(text)
        linkedin = [u for u in urls if "linkedin" in u.lower()]
        github = [u for u in urls if "github" in u.lower()]
        if linkedin:
            contact["linkedin_url"] = linkedin[0]
        if github:
            contact["github_url"] = github[0]
        return contact

    def _extract_name(self, text: str, sections: dict[str, str]) -> str | None:
        header = sections.get("header", "")
        lines = [ln.strip() for ln in header.split("\n") if ln.strip()]
        for line in lines[:5]:
            if (
                not any(kw in line.lower() for kw in ("@", "http", "phone", "email", "+", "resume", "cv"))
                and len(line.split()) in (2, 3, 4)
            ):
                return line
        return None

    def _parse_education_section(self, text: str) -> list[dict]:
        entries: list[dict] = []
        blocks = re.split(r"\n\s*\n", text.strip())
        for block in blocks:
            if not block.strip():
                continue
            lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
            entry: dict = {}
            degree_keywords = [
                "bachelor", "master", "phd", "doctor", "associate",
                "b.", "m.", "ph.d", "bs", "ba", "ms", "ma", "mba", "phd",
            ]
            if lines:
                first_lower = lines[0].lower()
                if any(kw in first_lower for kw in degree_keywords):
                    entry["degree"] = lines[0]
                    if len(lines) > 1:
                        entry["institution"] = lines[1]
                else:
                    entry["institution"] = lines[0]
                    if len(lines) > 1:
                        degree_match = re.match(
                            r"((?:Bachelor|Master|PhD|Doctor|Associate|B\.|M\.|Ph\.D|BS|BA|MS|MA|MBA)[^,]*),?\s*(.*)",
                            lines[1], re.IGNORECASE
                        )
                        if degree_match:
                            entry["degree"] = degree_match.group(1).strip()
                            entry["field_of_study"] = degree_match.group(2).strip() or None
                        else:
                            entry["degree"] = lines[1]
            dates = self.DATE_PATTERN.findall(block)
            if dates:
                entry["date_range"] = dates[0]
            if lines and not entry.get("institution"):
                entry["institution"] = lines[1] if len(lines) > 1 else lines[0]
            entries.append(entry)
        return entries

    def _parse_experience_section(self, text: str) -> list[dict]:
        entries: list[dict] = []
        blocks = re.split(r"\n\s*\n", text.strip())
        for block in blocks:
            if not block.strip():
                continue
            lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
            if not lines:
                continue
            entry: dict = {}
            # Check if first line looks like a title (ends with common title keywords)
            title_keywords = ["engineer", "developer", "manager", "director", "lead", "head", "architect",
                             "analyst", "designer", "consultant", "specialist", "coordinator", "associate"]
            first_lower = lines[0].lower()
            has_keyword = any(kw in first_lower for kw in title_keywords)
            has_at = " at " in first_lower or " @ " in first_lower

            if has_at:
                # Format: "Title at Company"
                parts = first_lower.split(" at ") if " at " in first_lower else first_lower.split(" @ ")
                entry["title"] = lines[0][:len(parts[0])].strip() if not has_at else parts[0].strip()
                entry["company"] = parts[1].strip() if len(parts) > 1 else lines[0]
            elif has_keyword and len(lines) > 1:
                entry["title"] = lines[0]
                entry["company"] = lines[1]
            else:
                entry["company"] = lines[0]
                if len(lines) > 1:
                    title_match = re.match(r"([A-Za-z\s/]+)", lines[1])
                    if title_match:
                        entry["title"] = title_match.group(1).strip()
            dates = self.DATE_PATTERN.findall(block)
            if dates:
                entry["date_range"] = dates[0]
            desc_lines = [dl for dl in lines[2:] if not self.DATE_PATTERN.match(dl)]
            if desc_lines:
                entry["description"] = "\n".join(desc_lines)[:2000]
            entries.append(entry)
        return entries

    def _parse_skills_section(self, text: str) -> list[dict]:
        skills: list[dict] = []
        text = text.strip()
        parts = re.split(r"[,;•|\n]+", text)
        for part in parts:
            part = part.strip().strip("-*•")
            if not part or len(part) > 50:
                continue
            # check for category: skill pattern
            if ":" in part:
                category, rest = part.split(":", 1)
                for s in re.split(r"[,;]", rest):
                    s = s.strip()
                    if s and len(s) <= 50:
                        skills.append({"name": s, "category": category.strip()})
            else:
                skills.append({"name": part})
        return skills

    def _parse_projects_section(self, text: str) -> list[dict]:
        entries: list[dict] = []
        blocks = re.split(r"\n\s*\n", text.strip())
        for block in blocks:
            if not block.strip():
                continue
            lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
            if not lines:
                continue
            entry: dict = {"name": lines[0]}
            if len(lines) > 1:
                entry["description"] = "\n".join(lines[1:])[:2000]
            urls = self.URL_PATTERN.findall(block)
            github = [u for u in urls if "github" in u.lower()]
            if github:
                entry["github_url"] = github[0]
            elif urls:
                entry["url"] = urls[0]
            entries.append(entry)
        return entries

    def _parse_certifications_section(self, text: str) -> list[dict]:
        entries: list[dict] = []
        blocks = re.split(r"\n\s*\n", text.strip())
        for block in blocks:
            if not block.strip():
                continue
            lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
            if not lines:
                continue
            entry: dict = {"name": lines[0]}
            if len(lines) > 1:
                entry["issuer"] = lines[1]
            dates = self.DATE_PATTERN.findall(block)
            if dates:
                entry["date_range"] = dates[0]
            entries.append(entry)
        return entries

    def _parse_languages_section(self, text: str) -> list[dict]:
        languages: list[dict] = []
        parts = re.split(r"[,;•|\n]+", text.strip())
        for part in parts:
            part = part.strip().strip("-*•")
            if not part:
                continue
            # look for proficiency indicators
            proficiency = None
            for level in ["native", "fluent", "advanced", "intermediate", "basic", "bilingual"]:
                if level in part.lower():
                    proficiency = level
                    break
            name = part
            if proficiency:
                name = re.sub(
                    r"(native|fluent|advanced|intermediate|basic|bilingual)",
                    "", part, flags=re.IGNORECASE
                ).strip().strip("-:;,")
            if proficiency:
                languages.append({"name": name, "proficiency": proficiency})
            else:
                languages.append({"name": part})
        return languages
