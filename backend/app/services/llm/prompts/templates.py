import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_template import PromptTemplate
from app.schemas.llm import (
    PromptTemplateCreate,
    PromptTemplateResponse,
    PromptTemplateUpdate,
)

logger = logging.getLogger(__name__)

VARIABLE_PATTERN = re.compile(r"\{\{(\w+)\}\}")


class PromptTemplateService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, data: PromptTemplateCreate
    ) -> PromptTemplateResponse:
        variables = data.variables or self._extract_variables(data.template)
        pt = PromptTemplate(
            name=data.name,
            version=1,
            template=data.template,
            variables=variables,
            description=data.description,
            model=data.model,
            is_active=True,
        )
        self.session.add(pt)
        await self.session.flush()
        await self.session.refresh(pt)
        return self._to_response(pt)

    async def get(
        self, name: str, version: int | None = None
    ) -> PromptTemplateResponse | None:
        stmt = select(PromptTemplate).where(
            PromptTemplate.name == name,
            PromptTemplate.is_active.is_(True),
        )
        if version:
            stmt = stmt.where(PromptTemplate.version == version)
        else:
            stmt = stmt.order_by(PromptTemplate.version.desc()).limit(1)
        result = await self.session.execute(stmt)
        pt = result.scalar_one_or_none()
        return self._to_response(pt) if pt else None

    async def list_templates(
        self, name: str | None = None
    ) -> list[PromptTemplateResponse]:
        stmt = select(PromptTemplate)
        if name:
            stmt = stmt.where(PromptTemplate.name == name)
        stmt = stmt.order_by(PromptTemplate.name, PromptTemplate.version.desc())
        result = await self.session.execute(stmt)
        return [self._to_response(pt) for pt in result.scalars().all()]

    async def update(
        self, name: str, version: int, data: PromptTemplateUpdate
    ) -> PromptTemplateResponse | None:
        stmt = select(PromptTemplate).where(
            PromptTemplate.name == name,
            PromptTemplate.version == version,
        )
        result = await self.session.execute(stmt)
        pt = result.scalar_one_or_none()
        if not pt:
            return None
        if data.template is not None:
            pt.template = data.template
        if data.variables is not None:
            pt.variables = data.variables
        else:
            pt.variables = self._extract_variables(pt.template)
        if data.description is not None:
            pt.description = data.description
        if data.model is not None:
            pt.model = data.model
        if data.is_active is not None:
            pt.is_active = data.is_active
        await self.session.flush()
        await self.session.refresh(pt)
        return self._to_response(pt)

    async def create_new_version(
        self, name: str, data: PromptTemplateCreate
    ) -> PromptTemplateResponse | None:
        latest = await self.get(name)
        new_version = (latest.version + 1) if latest else 1
        variables = data.variables or self._extract_variables(data.template)
        pt = PromptTemplate(
            name=name,
            version=new_version,
            template=data.template,
            variables=variables,
            description=data.description or (latest.description if latest else None),
            model=data.model or (latest.model if latest else None),
            is_active=True,
        )
        if latest:
            stmt = select(PromptTemplate).where(
                PromptTemplate.name == name,
                PromptTemplate.version == latest.version,
            )
            result = await self.session.execute(stmt)
            old = result.scalar_one_or_none()
            if old:
                old.is_active = False
        self.session.add(pt)
        await self.session.flush()
        await self.session.refresh(pt)
        return self._to_response(pt)

    async def render(
        self, name: str, variables: dict[str, str], version: int | None = None
    ) -> str | None:
        pt = await self.get(name, version)
        if not pt:
            return None
        rendered = pt.template
        for key, value in variables.items():
            rendered = rendered.replace("{{" + key + "}}", value)
        return rendered

    def _extract_variables(self, template: str) -> list[str]:
        return sorted(set(VARIABLE_PATTERN.findall(template)))

    def _to_response(self, pt: PromptTemplate) -> PromptTemplateResponse:
        return PromptTemplateResponse(
            id=str(pt.id),
            name=pt.name,
            version=pt.version,
            template=pt.template,
            variables=pt.variables or [],
            description=pt.description,
            model=pt.model,
            is_active=pt.is_active,
            created_at=pt.created_at,
            updated_at=pt.updated_at,
        )
