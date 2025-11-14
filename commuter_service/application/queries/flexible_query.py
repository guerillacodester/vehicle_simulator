"""
Flexible Query Engine for Passenger Data
=========================================

Provides a unified query interface with dynamic filtering, grouping, and formatting.
Supports SQL-like operations without reinventing wheels - uses pandas for heavy lifting.
"""

from __future__ import annotations

import pandas as pd
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
import httpx


async def execute_flexible_query(
    strapi_url: str,
    filters: Dict[str, Any],
    group_by: Optional[str] = None,
    aggregate: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: Optional[int] = None,
    format: Literal["json", "table", "barchart", "csv"] = "json",
    geocode: bool = False,
    geo_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a flexible query on passenger data.
    
    Args:
        strapi_url: Strapi API base URL
        filters: Dictionary of filters (route, depot, status, date, hour_start, hour_end, etc.)
        group_by: Field to group by (hour, route, depot, status, date)
        aggregate: Aggregation function (count, avg, sum, min, max)
        sort_by: Field to sort by
        limit: Maximum number of results
        format: Output format (json, table, barchart, csv)
        geocode: Whether to geocode addresses
        geo_url: Geospatial service URL for geocoding
    
    Returns:
        Dict with query results in requested format
    """
    
    # Step 1: Fetch all passengers from Strapi with pagination
    all_passengers = await _fetch_all_passengers(strapi_url)
    
    # Step 2: Convert to pandas DataFrame for easy manipulation
    df = pd.DataFrame(all_passengers)
    
    if df.empty:
        return {"data": [], "count": 0, "message": "No passengers found"}
    
    # Step 3: Apply filters
    df = _apply_filters(df, filters)
    
    if df.empty:
        return {"data": [], "count": 0, "message": "No passengers match filters"}
    
    # Step 4: Geocode if requested
    if geocode and geo_url:
        df = await _geocode_dataframe(df, geo_url)
    
    # Step 5: Group and aggregate if requested
    if group_by:
        result_data = _group_and_aggregate(df, group_by, aggregate)
    else:
        # Sort if requested
        if sort_by and sort_by in df.columns:
            df = df.sort_values(sort_by)
        
        # Limit if requested
        if limit:
            df = df.head(limit)
        
        result_data = df.to_dict('records')
    
    # Step 6: Format output
    formatted_result = _format_output(result_data, format, group_by, aggregate)
    
    return {
        "data": formatted_result,
        "count": len(result_data) if isinstance(result_data, list) else len(result_data.get('data', [])),
        "filters_applied": filters,
        "format": format
    }


async def _fetch_all_passengers(strapi_url: str) -> List[Dict[str, Any]]:
    """Fetch all passengers from Strapi with pagination"""
    all_passengers = []
    page = 1
    max_pages = 100
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while page <= max_pages:
            url = f"{strapi_url}/api/active-passengers?pagination[page]={page}&pagination[pageSize]=100"
            response = await client.get(url)
            
            if response.status_code != 200:
                break
            
            data = response.json()
            passengers = data.get('data', [])
            
            if not passengers:
                break
            
            # Handle both wrapped (page 1) and flat (page 2+) formats
            for p in passengers:
                if "attributes" in p:
                    attrs = p.get("attributes", {})
                    all_passengers.append({"id": p.get("id"), "documentId": p.get("documentId"), **attrs})
                else:
                    all_passengers.append(p)
            
            meta = data.get('meta', {})
            pagination = meta.get('pagination', {})
            total_pages = pagination.get('pageCount', 1)
            
            if page >= total_pages:
                break
            
            page += 1
    
    return all_passengers


def _apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Apply filters to DataFrame"""
    
    # Route filter
    if 'route' in filters and filters['route']:
        df = df[df['route_id'] == filters['route']]
    
    # Depot filter
    if 'depot' in filters and filters['depot']:
        df = df[df['depot_id'] == filters['depot']]
    
    # Status filter
    if 'status' in filters and filters['status']:
        df = df[df['status'] == filters['status']]
    
    # Date filter
    if 'date' in filters and filters['date']:
        df['spawned_date'] = pd.to_datetime(df['spawned_at']).dt.date
        target_date = pd.to_datetime(filters['date']).date()
        df = df[df['spawned_date'] == target_date]
    
    # Hour range filter
    if 'hour_start' in filters or 'hour_end' in filters:
        df['spawned_hour'] = pd.to_datetime(df['spawned_at']).dt.hour
        
        if 'hour_start' in filters:
            df = df[df['spawned_hour'] >= filters['hour_start']]
        
        if 'hour_end' in filters:
            df = df[df['spawned_hour'] <= filters['hour_end']]
    
    # Vehicle filter
    if 'vehicle' in filters and filters['vehicle']:
        df = df[df['vehicle_id'] == filters['vehicle']]
    
    return df


async def _geocode_dataframe(df: pd.DataFrame, geo_url: str) -> pd.DataFrame:
    """Add geocoded addresses to DataFrame"""
    from commuter_service.application.queries.manifest_query import reverse_geocode
    import asyncio
    
    cache = {}
    sem = asyncio.Semaphore(20)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async def geocode_row(idx, row):
            async with sem:
                start_addr = await reverse_geocode(
                    client, geo_url, 
                    row.get('latitude'), row.get('longitude'), 
                    cache
                )
            async with sem:
                dest_addr = await reverse_geocode(
                    client, geo_url,
                    row.get('destination_lat'), row.get('destination_lon'),
                    cache
                )
            return idx, start_addr, dest_addr
        
        tasks = [geocode_row(idx, row) for idx, row in df.iterrows()]
        results = await asyncio.gather(*tasks)
        
        for idx, start_addr, dest_addr in results:
            df.at[idx, 'start_address'] = start_addr or '-'
            df.at[idx, 'dest_address'] = dest_addr or '-'
    
    return df


def _group_and_aggregate(df: pd.DataFrame, group_by: str, aggregate: Optional[str]) -> List[Dict[str, Any]]:
    """Group and aggregate DataFrame"""
    
    # Map group_by to actual column
    group_column = group_by
    if group_by == 'hour':
        df['hour'] = pd.to_datetime(df['spawned_at']).dt.hour
        group_column = 'hour'
    elif group_by == 'date':
        df['date'] = pd.to_datetime(df['spawned_at']).dt.date
        group_column = 'date'
    
    # Default to count if no aggregate specified
    if not aggregate:
        aggregate = 'count'
    
    if aggregate == 'count':
        result = df.groupby(group_column).size().reset_index(name='count')
    elif aggregate == 'avg':
        # Average of numeric columns
        result = df.groupby(group_column).mean(numeric_only=True).reset_index()
    elif aggregate == 'sum':
        result = df.groupby(group_column).sum(numeric_only=True).reset_index()
    elif aggregate == 'min':
        result = df.groupby(group_column).min(numeric_only=True).reset_index()
    elif aggregate == 'max':
        result = df.groupby(group_column).max(numeric_only=True).reset_index()
    else:
        result = df.groupby(group_column).size().reset_index(name='count')
    
    return result.to_dict('records')


def _format_output(data: Any, format: str, group_by: Optional[str], aggregate: Optional[str]) -> Any:
    """Format output based on requested format"""
    
    if format == "json":
        return data
    
    elif format == "csv":
        # Convert to CSV string
        df = pd.DataFrame(data)
        return df.to_csv(index=False)
    
    elif format == "barchart":
        # Format for barchart visualization
        if group_by == 'hour' and aggregate == 'count':
            # Create 24-hour array
            hourly_counts = [0] * 24
            for item in data:
                hour = item.get('hour', 0)
                count = item.get('count', 0)
                if 0 <= hour < 24:
                    hourly_counts[hour] = count
            
            max_count = max(hourly_counts) if hourly_counts else 0
            peak_hour = hourly_counts.index(max_count) if max_count > 0 else 0
            
            return {
                "hourly_counts": hourly_counts,
                "total": sum(hourly_counts),
                "peak_hour": peak_hour,
                "peak_count": max_count
            }
        else:
            # Generic bar chart
            return {
                "categories": [str(item.get(group_by, '')) for item in data],
                "values": [item.get('count', 0) for item in data],
                "total": sum(item.get('count', 0) for item in data)
            }
    
    elif format == "table":
        # Return as-is for table rendering
        return data
    
    return data
