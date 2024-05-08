import codecs
import json
import os

from fastapi import APIRouter, Depends, Header, HTTPException

router = APIRouter(
    prefix="/business",
    tags=["business"],
    responses={404: {"description": "Not found"}},
)


@router.get("/kaipiao-info")
def get_kaipiao_info():
    fp = os.path.join(os.getcwd(), "app", "kaipiao.json")
    with open(fp) as f:
        info = json.load(f)
    return info


@router.get("/company-info")
def get_company_info():
    fp = os.path.join(os.getcwd(), "app", "company.json")
    with open(fp) as f:
        info = json.load(f)
    return info


@router.put("/kaipiao-info")
def update_kaipiao_info(data: dict):
    fp = os.path.join(os.getcwd(), "app", "kaipiao.json")
    with open(fp, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False)
    return


@router.put("/company-info")
def update_company_info(data: dict):
    fp = os.path.join(os.getcwd(), "app", "company.json")
    with open(fp, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False)
    return {"success": True}