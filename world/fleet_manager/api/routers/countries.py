# world/fleet_manager/api/routers/countries.py
from fastapi import APIRouter, Depends, HTTPException
from .. import deps
from ..schemas.country import CountryCreate, CountryRead, CountryUpdate

router = APIRouter(prefix="/api/v1/countries", tags=["countries"])


@router.get("/", response_model=list[CountryRead])
def list_countries(fm=Depends(deps.get_fm)):
    countries = fm.countries.list_countries()
    if not countries:
        raise HTTPException(status_code=404, detail="No countries found")
    return countries


@router.get("/{country_id}", response_model=CountryRead)
def get_country(country_id: str, fm=Depends(deps.get_fm)):
    """Lookup by UUID only"""
    country = fm.countries.get_country(country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


@router.get("/iso/{iso_code}", response_model=CountryRead)
def get_country_by_iso(iso_code: str, fm=Depends(deps.get_fm)):
    """Lookup by ISO Alpha-2 code (case-insensitive)"""
    country = fm.countries.get_by_iso(iso_code.upper())
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


@router.post("/", response_model=CountryRead)
def create_country(payload: CountryCreate, fm=Depends(deps.get_fm)):
    return fm.countries.create_country(iso_code=payload.iso_code, name=payload.name)


@router.put("/{country_id}", response_model=CountryRead)
def update_country(country_id: str, payload: CountryUpdate, fm=Depends(deps.get_fm)):
    country = fm.countries.update_country(country_id, **payload.dict(exclude_unset=True))
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


@router.delete("/{country_id}")
def delete_country(country_id: str, fm=Depends(deps.get_fm)):
    ok = fm.countries.delete_country(country_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"deleted": True}
