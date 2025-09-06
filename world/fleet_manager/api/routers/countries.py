# world/fleet_manager/api/routers/countries.py
from fastapi import APIRouter, Depends, HTTPException
from .. import deps
from ..schemas.country import CountryCreate, CountryRead, CountryUpdate

router = APIRouter(prefix="/api/v1/countries", tags=["countries"])

@router.get("/", response_model=list[CountryRead])
def list_countries(fm=Depends(deps.get_fm)):
    # ✅ return [] instead of 404
    return fm.countries.list_countries()

@router.get("/{country_id}", response_model=CountryRead)
def get_country(country_id: str, fm=Depends(deps.get_fm)):
    country = fm.countries.get_country(country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@router.get("/iso/{iso_code}", response_model=CountryRead)
def get_country_by_iso(iso_code: str, fm=Depends(deps.get_fm)):
    country = fm.countries.get_by_iso(iso_code.upper())
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@router.post("/", response_model=CountryRead, status_code=201)
def create_country(payload: CountryCreate, fm=Depends(deps.get_fm)):
    existing = fm.countries.get_by_iso(payload.iso_code.upper())
    if existing:
        raise HTTPException(status_code=409, detail=f"Country {payload.iso_code} already exists")

    return fm.countries.create_country(
        iso_code=payload.iso_code.upper(),
        name=payload.name
    )

@router.patch("/{country_id}", response_model=CountryRead)
def update_country(country_id: str, payload: CountryUpdate, fm=Depends(deps.get_fm)):
    country = fm.countries.update_country(country_id, **payload.dict(exclude_unset=True))
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@router.delete("/{country_id}", status_code=204)
def delete_country(country_id: str, fm=Depends(deps.get_fm)):
    ok = fm.countries.delete_country(country_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Country not found")
    return
