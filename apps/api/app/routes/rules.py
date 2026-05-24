from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.schemas.domain import KeywordRule, RuleCreateRequest, RuleUpdateRequest
from app.services.rule_service import create_rule, delete_rule_detail, get_rule_detail, list_rules, update_rule_detail

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=list[KeywordRule])
def rules_list() -> list[KeywordRule]:
    return list_rules()


@router.post("", response_model=KeywordRule, status_code=status.HTTP_201_CREATED)
def rules_create(payload: RuleCreateRequest) -> KeywordRule:
    return create_rule(payload)


@router.get("/{rule_id}", response_model=KeywordRule)
def rules_detail(rule_id: str) -> KeywordRule:
    try:
        return get_rule_detail(rule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Rule not found") from exc


@router.put("/{rule_id}", response_model=KeywordRule)
def rules_update(rule_id: str, payload: RuleUpdateRequest) -> KeywordRule:
    try:
        return update_rule_detail(rule_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Rule not found") from exc


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def rules_delete(rule_id: str) -> Response:
    try:
        delete_rule_detail(rule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Rule not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
