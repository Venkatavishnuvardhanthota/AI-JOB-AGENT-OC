from __future__ import annotations

from datetime import datetime, timedelta

import structlog

from app.jobs.config import JobDiscoveryConfig
from app.jobs.interfaces import JobProvider
from app.jobs.schemas import (
    CompanyInfo,
    EmploymentType,
    ExperienceLevel,
    JobPosting,
    JobProviderInfo,
    JobSearchRequest,
    JobSearchResponse,
    LocationInfo,
    RemoteType,
    SalaryInfo,
    SearchMetadata,
)

logger = structlog.get_logger(__name__)

MOCK_JOBS: list[dict] = [
    {
        "title": "Senior Software Engineer",
        "company": {"name": "TechCorp", "industry": "Technology", "size": "1000-5000"},
        "location": {"city": "San Francisco", "state": "CA", "country": "US", "remote_type": "hybrid"},
        "description": "Build and maintain scalable microservices. Work with Python, Go, and Kubernetes.",
        "url": "https://techcorp.example.com/jobs/sse-123",
        "provider_job_id": "mock-tc-001",
        "employment_type": "full_time",
        "experience_level": "senior",
        "salary": {"min": 150000, "max": 220000, "currency": "USD", "period": "yearly"},
        "skills": ["Python", "Go", "Kubernetes", "PostgreSQL", "AWS"],
        "posted_date": datetime.utcnow() - timedelta(days=2),
    },
    {
        "title": "Frontend Developer",
        "company": {"name": "WebStudio", "industry": "Design", "size": "50-200"},
        "location": {"city": "New York", "state": "NY", "country": "US", "remote_type": "remote"},
        "description": "Create beautiful React interfaces. Experience with TypeScript and CSS-in-JS required.",
        "url": "https://webstudio.example.com/careers/fed-456",
        "provider_job_id": "mock-ws-002",
        "employment_type": "full_time",
        "experience_level": "mid",
        "salary": {"min": 120000, "max": 160000, "currency": "USD", "period": "yearly"},
        "skills": ["React", "TypeScript", "CSS", "GraphQL", "Jest"],
        "posted_date": datetime.utcnow() - timedelta(days=5),
    },
    {
        "title": "DevOps Engineer",
        "company": {"name": "CloudBase", "industry": "Cloud Infrastructure", "size": "200-1000"},
        "location": {"city": "Austin", "state": "TX", "country": "US", "remote_type": "remote"},
        "description": "Manage CI/CD pipelines and cloud infrastructure. Terraform and AWS expertise needed.",
        "url": "https://cloudbase.example.com/jobs/devops-789",
        "provider_job_id": "mock-cb-003",
        "employment_type": "full_time",
        "experience_level": "senior",
        "salary": {"min": 140000, "max": 190000, "currency": "USD", "period": "yearly"},
        "skills": ["Terraform", "AWS", "Docker", "Kubernetes", "CI/CD"],
        "posted_date": datetime.utcnow() - timedelta(days=1),
    },
    {
        "title": "Junior Python Developer",
        "company": {"name": "StartupXYZ", "industry": "Technology", "size": "10-50"},
        "location": {"city": "Remote", "country": "US", "remote_type": "remote"},
        "description": "Join our fast-paced team building AI-powered tools. Python and SQL skills required.",
        "url": "https://startupxyz.example.com/jobs/py-101",
        "provider_job_id": "mock-sx-004",
        "employment_type": "full_time",
        "experience_level": "junior",
        "salary": {"min": 80000, "max": 110000, "currency": "USD", "period": "yearly"},
        "skills": ["Python", "SQL", "FastAPI", "Docker"],
        "posted_date": datetime.utcnow() - timedelta(days=7),
    },
    {
        "title": "Product Manager",
        "company": {"name": "EnterpriseCo", "industry": "Enterprise Software", "size": "5000+"},
        "location": {"city": "Chicago", "state": "IL", "country": "US", "remote_type": "on_site"},
        "description": "Drive product strategy for our B2B SaaS platform. 5+ years PM experience required.",
        "url": "https://enterpriseco.example.com/jobs/pm-202",
        "provider_job_id": "mock-ec-005",
        "employment_type": "full_time",
        "experience_level": "senior",
        "salary": {"min": 130000, "max": 180000, "currency": "USD", "period": "yearly"},
        "skills": ["Product Strategy", "Agile", "Data Analysis", "A/B Testing"],
        "posted_date": datetime.utcnow() - timedelta(days=10),
    },
    {
        "title": "UX Designer Intern",
        "company": {"name": "DesignLab", "industry": "Design", "size": "50-200"},
        "location": {"city": "Los Angeles", "state": "CA", "country": "US", "remote_type": "hybrid"},
        "description": "Learn from senior designers. Work on real products from day one.",
        "url": "https://designlab.example.com/internships/ux-303",
        "provider_job_id": "mock-dl-006",
        "employment_type": "internship",
        "experience_level": "entry",
        "salary": {"min": 40000, "max": 50000, "currency": "USD", "period": "yearly"},
        "skills": ["Figma", "User Research", "Prototyping", "Wireframing"],
        "posted_date": datetime.utcnow() - timedelta(days=3),
    },
    {
        "title": "Data Scientist",
        "company": {"name": "DataDriven Inc", "industry": "Analytics", "size": "200-1000"},
        "location": {"city": "Seattle", "state": "WA", "country": "US", "remote_type": "hybrid"},
        "description": "Apply ML to business problems. Experience with Python, TensorFlow, and SQL required.",
        "url": "https://datadriven.example.com/jobs/ds-404",
        "provider_job_id": "mock-dd-007",
        "employment_type": "full_time",
        "experience_level": "mid",
        "salary": {"min": 130000, "max": 170000, "currency": "USD", "period": "yearly"},
        "skills": ["Python", "TensorFlow", "SQL", "Statistics", "Machine Learning"],
        "posted_date": datetime.utcnow() - timedelta(hours=12),
    },
    {
        "title": "Freelance Graphic Designer",
        "company": {"name": "CreativeAgency", "industry": "Design", "size": "10-50"},
        "location": {"city": "Remote", "remote_type": "remote"},
        "description": "Design marketing materials and brand identities for diverse clients.",
        "url": "https://creativeagency.example.com/freelance/gd-505",
        "provider_job_id": "mock-ca-008",
        "employment_type": "freelance",
        "experience_level": "mid",
        "salary": {"min": 50000, "max": 80000, "currency": "USD", "period": "yearly"},
        "skills": ["Adobe Creative Suite", "Typography", "Branding"],
        "posted_date": datetime.utcnow() - timedelta(days=14),
    },
    {
        "title": "Senior Software Engineer",
        "company": {"name": "TechCorp", "industry": "Technology", "size": "1000-5000"},
        "location": {"city": "San Francisco", "state": "CA", "country": "US", "remote_type": "hybrid"},
        "description": "Lead backend team building next-gen APIs.",
        "url": "https://techcorp.example.com/jobs/sse-123",
        "provider_job_id": "mock-tc-001",
        "employment_type": "full_time",
        "experience_level": "senior",
        "salary": {"min": 150000, "max": 220000, "currency": "USD", "period": "yearly"},
        "skills": ["Python", "Go", "Kubernetes", "PostgreSQL", "AWS"],
        "posted_date": datetime.utcnow() - timedelta(days=2),
        "_duplicate": True,
    },
]


class MockJobProvider(JobProvider):
    name = "mock"
    display_name = "Mock Provider"
    description = "A mock job provider for testing and development"
    version = "1.0.0"
    supports_pagination = True
    supports_filters = True

    def __init__(self, config: JobDiscoveryConfig) -> None:
        super().__init__(config)

    async def search_jobs(self, request: JobSearchRequest) -> JobSearchResponse:
        results: list[JobPosting] = []
        for raw in MOCK_JOBS:
            if raw.get("_duplicate"):
                continue
            posting = self._raw_to_job_posting(raw)
            results.append(posting)

        total = len(results)
        paginated = results[request.offset : request.offset + request.limit]
        metadata = SearchMetadata(
            total_results=total,
            returned_results=len(paginated),
            providers_queried=[self.name],
            providers_succeeded=[self.name],
        )
        return JobSearchResponse(results=paginated, metadata=metadata)

    async def health_check(self) -> bool:
        return True

    async def provider_info(self) -> JobProviderInfo:
        return JobProviderInfo(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            is_available=True,
            supports_pagination=self.supports_pagination,
            supports_filters=self.supports_filters,
            version=self.version,
        )

    def _raw_to_job_posting(self, raw: dict) -> JobPosting:
        company_raw = raw.get("company", {})
        loc_raw = raw.get("location", {})
        sal_raw = raw.get("salary")

        company = CompanyInfo(
            name=company_raw.get("name", "Unknown"),
            industry=company_raw.get("industry"),
            size=company_raw.get("size"),
        )

        location = LocationInfo(
            city=loc_raw.get("city"),
            state=loc_raw.get("state"),
            country=loc_raw.get("country"),
            remote_type=RemoteType(loc_raw.get("remote_type", "unknown")),
        )

        salary = None
        if sal_raw:
            salary = SalaryInfo(
                min_amount=sal_raw.get("min"),
                max_amount=sal_raw.get("max"),
                currency=sal_raw.get("currency", "USD"),
                period=sal_raw.get("period", "yearly"),
            )

        return JobPosting(
            provider_job_id=raw.get("provider_job_id"),
            title=raw.get("title", "Untitled"),
            company=company,
            location=location,
            description=raw.get("description"),
            url=raw.get("url"),
            employment_type=EmploymentType(raw.get("employment_type", "other")),
            experience_level=ExperienceLevel(raw.get("experience_level", "unknown")),
            salary=salary,
            skills=raw.get("skills", []),
            posted_date=raw.get("posted_date"),
            provider=self.name,
        )
