from __future__ import annotations

import re

NORMALIZATION_MAP: dict[str, str] = {
    "e-mail": "email",
    "email address": "email",
    "primary email": "email",
    "work email": "email",
    "alternate email": "email",
    "phone number": "phone",
    "telephone": "phone",
    "mobile phone": "phone",
    "mobile": "phone",
    "cell phone": "phone",
    "contact number": "phone",
    "daytime phone": "phone",
    "home phone": "phone",
    "phone #": "phone",
    "linkedin url": "linkedin",
    "linkedin profile": "linkedin",
    "linkedin profile url": "linkedin",
    "linkedin": "linkedin",
    "github url": "github",
    "github profile": "github",
    "github profile url": "github",
    "git hub": "github",
    "github": "github",
    "portfolio url": "portfolio",
    "portfolio website": "portfolio",
    "personal website": "personal_website",
    "website": "website",
    "first name": "first_name",
    "firstname": "first_name",
    "given name": "first_name",
    "last name": "last_name",
    "lastname": "last_name",
    "family name": "last_name",
    "surname": "last_name",
    "full name": "full_name",
    "your name": "full_name",
    "name": "full_name",
    "street address": "address",
    "address line 1": "address",
    "address line1": "address",
    "address line 2": "address",
    "address line2": "address",
    "current address": "address",
    "zip code": "zip_code",
    "zip": "zip_code",
    "postal code": "zip_code",
    "post code": "zip_code",
    "work authorization": "work_authorization",
    "authorization to work": "work_authorization",
    "eligible to work": "work_authorization",
    "legally authorized": "work_authorization",
    "require visa sponsorship": "visa_status",
    "visa sponsorship": "visa_status",
    "visa status": "visa_status",
    "sponsorship": "visa_status",
    "notice period": "notice_period",
    "notice": "notice_period",
    "relocation": "relocation",
    "willing to relocate": "relocation",
    "remote preference": "remote_preference",
    "remote work": "remote_preference",
    "work remotely": "remote_preference",
    "expected salary": "expected_salary",
    "desired salary": "expected_salary",
    "salary expectations": "expected_salary",
    "salary requirement": "expected_salary",
    "current salary": "salary",
    "years of experience": "years_of_experience",
    "years experience": "years_of_experience",
    "work experience": "experience",
    "relevant experience": "experience",
    "graduation date": "graduation_date",
    "graduation year": "graduation_date",
    "date of graduation": "graduation_date",
    "cover letter": "cover_letter",
    "coverletter": "cover_letter",
    "resume": "resume",
    "resume/cv": "resume",
    "upload resume": "resume",
    "upload cv": "resume",
    "attach resume": "resume",
    "cv": "resume",
    "employer": "company",
    "company": "company",
    "current employer": "company",
    "job title": "job_title",
    "title": "job_title",
    "position": "job_title",
    "position title": "job_title",
    "highest education": "education",
    "education level": "education",
    "skills": "skills",
    "skill set": "skills",
    "technical skills": "skills",
    "start date": "start_date",
    "end date": "end_date",
    "summary": "summary",
    "professional summary": "summary",
    "headline": "headline",
    "professional headline": "headline",
    "gender": "gender",
    "race/ethnicity": "race",
    "ethnicity": "race",
    "veteran status": "veteran_status",
    "military service": "veteran_status",
    "disability": "disability",
    "disability status": "disability",
    "language": "language",
    "languages": "language",
    "certification": "certification",
    "certifications": "certification",
    "school": "school",
    "college": "school",
    "university": "school",
    "degree": "degree",
    "field of study": "field_of_study",
    "major": "field_of_study",
    "linkedin profile link": "linkedin",
    "link to linkedin profile": "linkedin",
    "link to portfolio": "portfolio",
    "link to github": "github",
    "url to resume": "resume",
}


def normalize_label(label: str) -> str:
    normalized = label.lower().strip()
    normalized = re.sub(r"[:\*\s]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"[\(\)\[\]]", "", normalized)
    return normalized


def lookup_normalized(label: str) -> str | None:
    normalized = normalize_label(label)
    if normalized in NORMALIZATION_MAP:
        return NORMALIZATION_MAP[normalized]
    return None


def normalize_for_comparison(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def fuzzy_match(text: str, pattern: str) -> bool:
    n1 = normalize_for_comparison(text)
    n2 = normalize_for_comparison(pattern)
    return bool(n1 == n2 or n2 in n1 or n1 in n2)
