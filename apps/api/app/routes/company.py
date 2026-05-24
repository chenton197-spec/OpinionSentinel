from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from app.schemas.domain import CompanyBootstrapResult, CompanyProfile, CompanyProfileUpdateRequest
from app.services.company_service import read_company_profile, refresh_company_news, save_company_profile_fast, save_company_profile_llm_background, enrich_company_profile

router = APIRouter(prefix="/company", tags=["company"])


@router.get("", response_model=CompanyProfile)
def company_profile() -> CompanyProfile:
    return read_company_profile()


@router.put("", response_model=CompanyProfile)
def company_profile_update(payload: CompanyProfileUpdateRequest, background_tasks: BackgroundTasks) -> CompanyProfile:
    saved = save_company_profile_fast(payload)
    background_tasks.add_task(save_company_profile_llm_background, payload)
    return saved


@router.post("/refresh-news", response_model=CompanyBootstrapResult)
def company_refresh_news() -> CompanyBootstrapResult:
    return refresh_company_news()

from pydantic import BaseModel

class EnrichRequest(BaseModel):
    company_name: str

@router.post("/enrich")
def company_profile_enrich(payload: EnrichRequest) -> dict:
    return enrich_company_profile(payload.company_name)
