#!/usr/bin/env python3
"""
COMPREHENSIVE GEOMETRY TABLE ANALYSIS
====================================
Deep validation of geometry-related tables across all databases.
This will identify the correct database, table structure, and data format.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel
import psycopg2
from psycopg2.extras import RealDictCursor
import json

def analyze_database_structure():
    """Comprehensive analysis of all databases for geometry data"""
    print("🔍 COMPREHENSIVE GEOMETRY TABLE ANALYSIS")
    print("=" * 80)
    
    # Set up SSH tunnel
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    analysis_results = {}
    
    try:
        # Test all possible databases
        databases_to_check = [
            'arknettransit',
            'barbados_transit_gtfs', 
            'postgres',
            'template1'
        ]
        
        for db_name in databases_to_check:
            print(f"\n📊 ANALYZING DATABASE: {db_name}")
            print("=" * 60)
            
            try:
                conn = psycopg2.connect(
                    host='127.0.0.1',
                    port=6543, 
                    database=db_name,
                    user='david',
                    password='Ga25w123!'
                )
                
                analysis_results[db_name] = analyze_single_database(conn, db_name)
                conn.close()
                
            except Exception as e:
                print(f"❌ Cannot connect to {db_name}: {e}")
                analysis_results[db_name] = {"error": str(e)}
        
        # Generate comprehensive summary
        generate_analysis_summary(analysis_results)
        
    finally:
        tunnel.stop()

def analyze_single_database(conn, db_name):
    """Analyze a single database for geometry-related tables"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    db_analysis = {
        "accessible": True,
        "tables": {},
        "postgis_enabled": False,
        "geometry_tables": [],
        "gtfs_tables": []
    }
    
    try:
        # Check if PostGIS is enabled
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis');")
        db_analysis["postgis_enabled"] = cursor.fetchone()[0]
        print(f"PostGIS Enabled: {'✅ Yes' if db_analysis['postgis_enabled'] else '❌ No'}")
        
        if db_analysis["postgis_enabled"]:
            cursor.execute("SELECT PostGIS_Version();")
            postgis_version = cursor.fetchone()[0]
            print(f"PostGIS Version: {postgis_version}")
    
    except Exception as e:
        print(f"⚠️  PostGIS check failed: {e}")
    
    # Get all table names
    cursor.execute("""
        SELECT table_name, table_type
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    all_tables = cursor.fetchall()
    print(f"\n📋 Found {len(all_tables)} tables in {db_name}")
    
    # Look for geometry-related tables
    geometry_related_tables = []
    gtfs_tables = []
    
    for table in all_tables:
        table_name = table['table_name']
        
        if any(keyword in table_name.lower() for keyword in ['shape', 'geom', 'route', 'stop', 'trip']):
            if 'shape' in table_name.lower() or 'geom' in table_name.lower():
                geometry_related_tables.append(table_name)
            
            if table_name in ['shapes', 'routes', 'stops', 'trips', 'route_shapes']:
                gtfs_tables.append(table_name)
            
            print(f"  🎯 {table_name} - {'GEOMETRY' if table_name in geometry_related_tables else 'GTFS'}")
    
    db_analysis["geometry_tables"] = geometry_related_tables
    db_analysis["gtfs_tables"] = gtfs_tables
    
    # Analyze each relevant table in detail
    relevant_tables = list(set(geometry_related_tables + gtfs_tables))
    
    for table_name in relevant_tables:
        print(f"\n🔍 DETAILED ANALYSIS: {table_name}")
        print("-" * 40)
        
        try:
            # Get column information
            cursor.execute("""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    character_maximum_length,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            # Check for geometry columns specifically
            cursor.execute("""
                SELECT 
                    f_geometry_column,
                    coord_dimension,
                    srid,
                    type
                FROM geometry_columns 
                WHERE f_table_name = %s;
            """, (table_name,))
            
            geometry_columns = cursor.fetchall()
            
            # Count records
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            record_count = cursor.fetchone()[0]
            
            # Sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            sample_data = cursor.fetchall()
            
            # Store analysis
            table_analysis = {
                "columns": [dict(col) for col in columns],
                "geometry_columns": [dict(geom_col) for geom_col in geometry_columns] if geometry_columns else [],
                "record_count": record_count,
                "sample_data": [dict(row) for row in sample_data]
            }
            
            db_analysis["tables"][table_name] = table_analysis
            
            # Display results
            print(f"📊 Records: {record_count}")
            print(f"📝 Columns ({len(columns)}):")
            
            for col in columns:
                geom_marker = ""
                if geometry_columns:
                    for geom_col in geometry_columns:
                        if geom_col['f_geometry_column'] == col['column_name']:
                            geom_marker = f" [GEOMETRY: {geom_col['type']}, SRID: {geom_col['srid']}]"
                            break
                
                print(f"   - {col['column_name']}: {col['data_type']}{geom_marker}")
            
            if geometry_columns:
                print(f"🌍 Geometry Columns: {len(geometry_columns)}")
                for geom_col in geometry_columns:
                    print(f"   - {geom_col['f_geometry_column']}: {geom_col['type']} (SRID: {geom_col['srid']})")
            
            # Show sample data (first row only, truncated)
            if sample_data:
                print(f"📄 Sample Data (first record):")
                sample_row = sample_data[0]
                for key, value in sample_row.items():
                    if value is not None:
                        # Truncate long values
                        str_value = str(value)
                        if len(str_value) > 100:
                            str_value = str_value[:100] + "..."
                        print(f"   - {key}: {str_value}")
        
        except Exception as e:
            print(f"❌ Error analyzing {table_name}: {e}")
            db_analysis["tables"][table_name] = {"error": str(e)}
    
    cursor.close()
    return db_analysis

def generate_analysis_summary(analysis_results):
    """Generate comprehensive summary of findings"""
    print(f"\n🎯 COMPREHENSIVE ANALYSIS SUMMARY")
    print("=" * 80)
    
    total_geometry_tables = 0
    databases_with_geometry = []
    recommended_database = None
    recommended_tables = []
    
    for db_name, analysis in analysis_results.items():
        if "error" in analysis:
            print(f"❌ {db_name}: {analysis['error']}")
            continue
        
        geometry_count = len(analysis.get("geometry_tables", []))
        gtfs_count = len(analysis.get("gtfs_tables", []))
        postgis = analysis.get("postgis_enabled", False)
        
        print(f"\n📊 {db_name}:")
        print(f"   PostGIS: {'✅' if postgis else '❌'}")
        print(f"   Geometry Tables: {geometry_count}")
        print(f"   GTFS Tables: {gtfs_count}")
        
        if geometry_count > 0:
            total_geometry_tables += geometry_count
            databases_with_geometry.append(db_name)
            print(f"   🎯 Geometry Tables: {', '.join(analysis['geometry_tables'])}")
            
            # Find tables with actual geometry data
            for table_name, table_info in analysis.get("tables", {}).items():
                if "error" not in table_info:
                    geom_cols = table_info.get("geometry_columns", [])
                    record_count = table_info.get("record_count", 0)
                    
                    if geom_cols and record_count > 0:
                        print(f"      ✅ {table_name}: {record_count} records with geometry")
                        if not recommended_database:
                            recommended_database = db_name
                            recommended_tables.append(table_name)
                        elif db_name == recommended_database:
                            recommended_tables.append(table_name)
    
    # Final recommendations
    print(f"\n🚀 MIGRATION RECOMMENDATIONS")
    print("=" * 80)
    
    if recommended_database:
        print(f"✅ PRIMARY DATABASE: {recommended_database}")
        print(f"✅ GEOMETRY TABLES: {', '.join(recommended_tables)}")
        
        # Get detailed info about recommended tables
        if recommended_database in analysis_results:
            db_analysis = analysis_results[recommended_database]
            
            for table_name in recommended_tables:
                if table_name in db_analysis.get("tables", {}):
                    table_info = db_analysis["tables"][table_name]
                    if "error" not in table_info:
                        geom_cols = table_info.get("geometry_columns", [])
                        record_count = table_info.get("record_count", 0)
                        
                        print(f"\n📋 {table_name} Migration Plan:")
                        print(f"   Records: {record_count}")
                        
                        for geom_col in geom_cols:
                            print(f"   Geometry: {geom_col['f_geometry_column']} ({geom_col['type']}, SRID: {geom_col['srid']})")
                        
                        # Show conversion strategy
                        if geom_cols:
                            geom_type = geom_cols[0]['type'].upper()
                            if 'LINESTRING' in geom_type:
                                print(f"   🔄 Conversion: PostGIS LINESTRING → GTFS coordinate points")
                                print(f"   📊 Expected Points: Use ST_DumpPoints() to extract coordinates")
                            elif 'POINT' in geom_type:
                                print(f"   🔄 Conversion: PostGIS POINT → GTFS lat/lon pair")
                            else:
                                print(f"   🔄 Conversion: PostGIS {geom_type} → GTFS format (custom)")
        
        print(f"\n💡 NEXT STEPS:")
        print(f"1. Update geometry migration script to use database: {recommended_database}")
        print(f"2. Focus on tables: {', '.join(recommended_tables)}")
        print(f"3. Use PostGIS functions to convert geometry to GTFS coordinates")
        
    else:
        print(f"❌ NO GEOMETRY DATA FOUND")
        print(f"💡 Check if geometry data exists in other databases or schemas")
    
    # Save analysis to file
    with open('geometry_analysis_results.json', 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    print(f"\n💾 Full analysis saved to: geometry_analysis_results.json")

if __name__ == "__main__":
    analyze_database_structure()