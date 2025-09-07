"""Update schema

Revision ID: 27767909c816
Revises: 15d8f14a1d06
Create Date: 2025-09-07 12:41:32.730872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = '27767909c816'
down_revision: Union[str, Sequence[str], None] = '15d8f14a1d06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop all foreign key constraints first
    try:
        op.drop_constraint(op.f('routes_country_id_fkey'), 'routes', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint(op.f('services_country_id_fkey'), 'services', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint(op.f('blocks_country_id_fkey'), 'blocks', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint(op.f('depots_country_id_fkey'), 'depots', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint(op.f('vehicles_country_id_fkey'), 'vehicles', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint(op.f('stops_country_id_fkey'), 'stops', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint(op.f('drivers_country_id_fkey'), 'drivers', type_='foreignkey')
    except:
        pass

    # Drop all views with CASCADE to ensure no dependency issues
    op.execute('DROP VIEW IF EXISTS block_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS route_trip_stats CASCADE')
    op.execute('DROP VIEW IF EXISTS route_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS block_trip_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS vehicle_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS driver_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS stop_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS timetable_summary CASCADE')

    # Drop foreign key constraints on driver_assignments and vehicle_assignments
    op.execute('DROP TABLE IF EXISTS driver_assignments CASCADE')
    op.execute('DROP TABLE IF EXISTS vehicle_assignments CASCADE')

    # Drop dependent tables with CASCADE to handle complex relationships
    op.execute('DROP TABLE IF EXISTS stop_times CASCADE')
    op.execute('DROP TABLE IF EXISTS timetables CASCADE')
    op.execute('DROP TABLE IF EXISTS vehicle_status_events CASCADE')
    op.execute('DROP INDEX IF EXISTS stops_loc_gix CASCADE')
    op.execute('DROP TABLE IF EXISTS stops CASCADE')
    op.execute('DROP TABLE IF EXISTS block_trips CASCADE')
    op.execute('DROP TABLE IF EXISTS trips CASCADE')
    op.execute('DROP TABLE IF EXISTS services CASCADE')
    op.execute('DROP TABLE IF EXISTS block_breaks CASCADE')
    op.execute('DROP TABLE IF EXISTS frequencies CASCADE')
    op.execute('DROP TABLE IF EXISTS blocks CASCADE')
    op.execute('DROP TABLE IF EXISTS route_shapes CASCADE')
    op.execute('DROP TABLE IF EXISTS shapes CASCADE')
    
    # Drop reference tables
    op.execute('DROP INDEX IF EXISTS depots_country_name_uidx CASCADE')
    op.execute('DROP INDEX IF EXISTS depots_loc_gix CASCADE')
    op.execute('DROP TABLE IF EXISTS depots CASCADE')
    op.execute('DROP TABLE IF EXISTS drivers CASCADE')
    
    # Finally drop the country reference table
    op.execute('DROP TABLE IF EXISTS countries CASCADE')
    # Drop all views with CASCADE first to ensure no dependency issues
    op.execute('DROP VIEW IF EXISTS block_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS route_trip_stats CASCADE')
    op.execute('DROP VIEW IF EXISTS route_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS block_trip_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS vehicle_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS driver_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS stop_summary CASCADE')
    op.execute('DROP VIEW IF EXISTS timetable_summary CASCADE')

    # Drop all foreign key constraints
    op.execute('ALTER TABLE vehicles DROP CONSTRAINT IF EXISTS vehicles_preferred_route_id_fkey CASCADE')
    op.execute('ALTER TABLE routes DROP CONSTRAINT IF EXISTS routes_pkey CASCADE')

    # Add the required new columns as nullable first
    op.add_column('routes', sa.Column('id', sa.Integer(), nullable=True))
    op.add_column('routes', sa.Column('name', sa.String(), nullable=True))
    op.add_column('routes', sa.Column('shape', geoalchemy2.types.Geometry(geometry_type='LINESTRING', dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True))

    # Fill the id column with sequential numbers starting from 1
    op.execute("""
        WITH RECURSIVE number_generator AS (
            SELECT 1 as num
            UNION ALL
            SELECT num + 1
            FROM number_generator
            WHERE num < (SELECT COUNT(*) FROM routes)
        )
        UPDATE routes
        SET id = number_generator.num
        FROM (SELECT num FROM number_generator LIMIT (SELECT COUNT(*) FROM routes)) as number_generator,
            (SELECT route_id, ROW_NUMBER() OVER (ORDER BY route_id) as rn FROM routes) as ordered_routes
        WHERE routes.route_id = ordered_routes.route_id AND ordered_routes.rn = number_generator.num;
    """)

    # Make id non-nullable and create the primary key constraint
    op.alter_column('routes', 'id', nullable=False)
    op.execute('DROP INDEX IF EXISTS idx_routes_shape CASCADE')
    op.execute('ALTER TABLE routes ADD CONSTRAINT routes_pkey PRIMARY KEY (id)')
    op.execute('CREATE INDEX idx_routes_shape ON routes USING gist (shape)')

    # Change route_id type from UUID to String and ensure it's still unique
    op.alter_column('routes', 'route_id',
               existing_type=sa.UUID(),
               type_=sa.String(),
               existing_nullable=False)
    op.create_unique_constraint('routes_route_id_key', 'routes', ['route_id'])
    # Drop index and constraints safely with IF EXISTS
    op.execute('DROP INDEX IF EXISTS routes_country_short_name_uidx')
    op.execute('ALTER TABLE IF EXISTS routes DROP CONSTRAINT IF EXISTS routes_country_id_fkey CASCADE')
    
    # Add the unique constraint on route_id
    op.create_unique_constraint(None, 'routes', ['route_id'])
    
    # Drop columns
    op.drop_column('routes', 'valid_to')
    op.drop_column('routes', 'country_id')
    op.drop_column('routes', 'valid_from')
    op.drop_column('routes', 'parishes')
    op.drop_column('routes', 'created_at')
    op.drop_column('routes', 'long_name')
    op.drop_column('routes', 'updated_at')
    op.drop_column('routes', 'short_name')
    op.drop_column('routes', 'is_active')
    
    # Handle vehicles table migration
    op.add_column('vehicles', sa.Column('id', sa.Integer(), nullable=True))
    op.add_column('vehicles', sa.Column('route_id', sa.String(), nullable=True))
    
    # Fill the id column with sequential numbers
    op.execute("""
        WITH RECURSIVE number_generator AS (
            SELECT 1 as num
            UNION ALL
            SELECT num + 1
            FROM number_generator
            WHERE num < (SELECT COUNT(*) FROM vehicles)
        )
        UPDATE vehicles
        SET id = number_generator.num
        FROM (SELECT num FROM number_generator LIMIT (SELECT COUNT(*) FROM vehicles)) as number_generator,
            (SELECT vehicle_id, ROW_NUMBER() OVER (ORDER BY vehicle_id) as rn FROM vehicles) as ordered_vehicles
        WHERE vehicles.vehicle_id = ordered_vehicles.vehicle_id AND ordered_vehicles.rn = number_generator.num;
    """)
    
    # Now make id non-nullable
    op.alter_column('vehicles', 'id', nullable=False)
    
    # Change vehicle_id type
    # Update vehicles table
    op.alter_column('vehicles', 'vehicle_id',
               existing_type=sa.UUID(),
               type_=sa.String(),
               existing_nullable=False,
               existing_server_default=sa.text('gen_random_uuid()'))
    
    op.alter_column('vehicles', 'status',
               existing_type=postgresql.ENUM('available', 'in_service', 'maintenance', 'retired', name='vehicle_status'),
               type_=sa.String(),
               nullable=True,
               existing_server_default=sa.text("'available'::vehicle_status"))
    
    # Drop indexes and constraints safely
    op.execute('DROP INDEX IF EXISTS vehicles_country_reg_code_uidx')
    op.execute('ALTER TABLE IF EXISTS vehicles DROP CONSTRAINT IF EXISTS vehicles_country_id_fkey CASCADE')
    op.execute('ALTER TABLE IF EXISTS vehicles DROP CONSTRAINT IF EXISTS vehicles_home_depot_id_fkey CASCADE')
    op.execute('ALTER TABLE IF EXISTS vehicles DROP CONSTRAINT IF EXISTS vehicles_preferred_route_id_fkey CASCADE')
    
    # Create new constraints
    op.create_unique_constraint(None, 'vehicles', ['vehicle_id'])
    op.create_foreign_key(None, 'vehicles', 'routes', ['route_id'], ['route_id'])
    
    # Drop unused columns
    op.drop_column('vehicles', 'country_id')
    op.drop_column('vehicles', 'notes')
    op.drop_column('vehicles', 'home_depot_id')
    op.drop_column('vehicles', 'reg_code')
    op.drop_column('vehicles', 'profile_id')
    op.drop_column('vehicles', 'created_at')
    op.drop_column('vehicles', 'updated_at')
    op.drop_column('vehicles', 'preferred_route_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('vehicles', sa.Column('preferred_route_id', sa.UUID(), autoincrement=False, nullable=True))
    op.add_column('vehicles', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False))
    op.add_column('vehicles', sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False))
    op.add_column('vehicles', sa.Column('profile_id', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('vehicles', sa.Column('reg_code', sa.TEXT(), autoincrement=False, nullable=False))
    op.add_column('vehicles', sa.Column('home_depot_id', sa.UUID(), autoincrement=False, nullable=True))
    op.add_column('vehicles', sa.Column('notes', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('vehicles', sa.Column('country_id', sa.UUID(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'vehicles', type_='foreignkey')
    op.create_foreign_key(op.f('vehicles_preferred_route_id_fkey'), 'vehicles', 'routes', ['preferred_route_id'], ['route_id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('vehicles_home_depot_id_fkey'), 'vehicles', 'depots', ['home_depot_id'], ['depot_id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('vehicles_country_id_fkey'), 'vehicles', 'countries', ['country_id'], ['country_id'], ondelete='CASCADE')
    op.drop_constraint(None, 'vehicles', type_='unique')
    op.create_index(op.f('vehicles_country_reg_code_uidx'), 'vehicles', ['country_id', 'reg_code'], unique=True)
    op.alter_column('vehicles', 'status',
               existing_type=sa.String(),
               type_=postgresql.ENUM('available', 'in_service', 'maintenance', 'retired', name='vehicle_status'),
               nullable=False,
               existing_server_default=sa.text("'available'::vehicle_status"))
    op.alter_column('vehicles', 'vehicle_id',
               existing_type=sa.String(),
               type_=sa.UUID(),
               existing_nullable=False,
               existing_server_default=sa.text('gen_random_uuid()'))
    op.drop_column('vehicles', 'route_id')
    op.drop_column('vehicles', 'id')
    op.add_column('routes', sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False))
    op.add_column('routes', sa.Column('short_name', sa.TEXT(), autoincrement=False, nullable=False))
    op.add_column('routes', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False))
    op.add_column('routes', sa.Column('long_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('routes', sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False))
    op.add_column('routes', sa.Column('parishes', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('routes', sa.Column('valid_from', sa.DATE(), server_default=sa.text('CURRENT_DATE'), autoincrement=False, nullable=True))
    op.add_column('routes', sa.Column('country_id', sa.UUID(), autoincrement=False, nullable=False))
    op.add_column('routes', sa.Column('valid_to', sa.DATE(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('routes_country_id_fkey'), 'routes', 'countries', ['country_id'], ['country_id'], ondelete='CASCADE')
    op.drop_constraint(None, 'routes', type_='unique')
    op.drop_index('idx_routes_shape', table_name='routes', postgresql_using='gist')
    op.create_index(op.f('routes_country_short_name_uidx'), 'routes', ['country_id', 'short_name'], unique=True)
    op.alter_column('routes', 'route_id',
               existing_type=sa.String(),
               type_=sa.UUID(),
               existing_nullable=False,
               existing_server_default=sa.text('gen_random_uuid()'))
    op.drop_column('routes', 'shape')
    op.drop_column('routes', 'name')
    op.drop_column('routes', 'id')
    op.create_table('shapes',
    sa.Column('shape_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='LINESTRING', srid=4326, dimension=2, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry', nullable=False, _spatial_index_reflected=True), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('shape_id', name='shapes_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('route_shapes',
    sa.Column('route_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('shape_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('variant_code', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('is_default', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['route_id'], ['routes.route_id'], name=op.f('route_shapes_route_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['shape_id'], ['shapes.shape_id'], name=op.f('route_shapes_shape_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('route_id', 'shape_id', name=op.f('route_shapes_pkey'))
    )
    op.create_table('blocks',
    sa.Column('block_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('country_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('route_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('service_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('start_time', postgresql.TIME(), autoincrement=False, nullable=False),
    sa.Column('end_time', postgresql.TIME(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['country_id'], ['countries.country_id'], name='blocks_country_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['route_id'], ['routes.route_id'], name='blocks_route_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['service_id'], ['services.service_id'], name='blocks_service_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('block_id', name='blocks_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('spatial_ref_sys',
    sa.Column('srid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('auth_name', sa.VARCHAR(length=256), autoincrement=False, nullable=True),
    sa.Column('auth_srid', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('srtext', sa.VARCHAR(length=2048), autoincrement=False, nullable=True),
    sa.Column('proj4text', sa.VARCHAR(length=2048), autoincrement=False, nullable=True),
    sa.CheckConstraint('srid > 0 AND srid <= 998999', name=op.f('spatial_ref_sys_srid_check')),
    sa.PrimaryKeyConstraint('srid', name=op.f('spatial_ref_sys_pkey'))
    )
    op.create_table('drivers',
    sa.Column('driver_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('country_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('license_no', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('home_depot_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('employment_status', sa.TEXT(), server_default=sa.text("'active'::text"), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['country_id'], ['countries.country_id'], name='drivers_country_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['home_depot_id'], ['depots.depot_id'], name='drivers_home_depot_id_fkey', ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('driver_id', name='drivers_pkey'),
    sa.UniqueConstraint('license_no', name='drivers_license_no_key', postgresql_include=[], postgresql_nulls_not_distinct=False),
    postgresql_ignore_search_path=False
    )
    op.create_table('frequencies',
    sa.Column('frequency_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('service_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('route_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('start_time', postgresql.TIME(), autoincrement=False, nullable=False),
    sa.Column('end_time', postgresql.TIME(), autoincrement=False, nullable=False),
    sa.Column('headway_s', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.CheckConstraint('headway_s > 0', name=op.f('frequencies_headway_s_check')),
    sa.ForeignKeyConstraint(['route_id'], ['routes.route_id'], name=op.f('frequencies_route_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['service_id'], ['services.service_id'], name=op.f('frequencies_service_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('frequency_id', name=op.f('frequencies_pkey'))
    )
    op.create_table('block_breaks',
    sa.Column('break_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('block_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('break_start', postgresql.TIME(), autoincrement=False, nullable=False),
    sa.Column('break_end', postgresql.TIME(), autoincrement=False, nullable=False),
    sa.Column('break_duration', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.CheckConstraint('break_duration > 0', name=op.f('block_breaks_break_duration_check')),
    sa.ForeignKeyConstraint(['block_id'], ['blocks.block_id'], name=op.f('block_breaks_block_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('break_id', name=op.f('block_breaks_pkey'))
    )
    op.create_table('services',
    sa.Column('service_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('country_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('mon', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('tue', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('wed', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('thu', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('fri', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('sat', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('sun', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('date_start', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('date_end', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['country_id'], ['countries.country_id'], name='services_country_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('service_id', name='services_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('trips',
    sa.Column('trip_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('route_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('service_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('shape_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('trip_headsign', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('direction_id', sa.SMALLINT(), autoincrement=False, nullable=True),
    sa.Column('block_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.CheckConstraint('direction_id = ANY (ARRAY[0, 1])', name='trips_direction_id_check'),
    sa.ForeignKeyConstraint(['block_id'], ['blocks.block_id'], name='trips_block_id_fkey', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['route_id'], ['routes.route_id'], name='trips_route_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['service_id'], ['services.service_id'], name='trips_service_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['shape_id'], ['shapes.shape_id'], name='trips_shape_id_fkey', ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('trip_id', name='trips_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('vehicle_assignments',
    sa.Column('assignment_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('vehicle_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('block_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('assigned_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['block_id'], ['blocks.block_id'], name=op.f('vehicle_assignments_block_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.vehicle_id'], name=op.f('vehicle_assignments_vehicle_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('assignment_id', name=op.f('vehicle_assignments_pkey'))
    )
    op.create_table('driver_assignments',
    sa.Column('assignment_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('driver_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('block_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('assigned_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['block_id'], ['blocks.block_id'], name=op.f('driver_assignments_block_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['driver_id'], ['drivers.driver_id'], name=op.f('driver_assignments_driver_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('assignment_id', name=op.f('driver_assignments_pkey'))
    )
    op.create_table('depots',
    sa.Column('depot_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('country_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry', _spatial_index_reflected=True), autoincrement=False, nullable=True),
    sa.Column('capacity', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('notes', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.CheckConstraint('capacity IS NULL OR capacity >= 0', name='depots_capacity_check'),
    sa.ForeignKeyConstraint(['country_id'], ['countries.country_id'], name='depots_country_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('depot_id', name='depots_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index(op.f('depots_loc_gix'), 'depots', ['location'], unique=False, postgresql_using='gist')
    op.create_index(op.f('depots_country_name_uidx'), 'depots', ['country_id', 'name'], unique=True)
    op.create_table('block_trips',
    sa.Column('block_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('trip_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('layover_minutes', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['block_id'], ['blocks.block_id'], name=op.f('block_trips_block_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['trip_id'], ['trips.trip_id'], name=op.f('block_trips_trip_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('block_id', 'trip_id', name=op.f('block_trips_pkey'))
    )
    op.create_table('stops',
    sa.Column('stop_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('country_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('code', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry', nullable=False, _spatial_index_reflected=True), autoincrement=False, nullable=False),
    sa.Column('zone_id', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['country_id'], ['countries.country_id'], name='stops_country_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('stop_id', name='stops_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index(op.f('stops_loc_gix'), 'stops', ['location'], unique=False, postgresql_using='gist')
    op.create_table('vehicle_status_events',
    sa.Column('event_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('vehicle_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('status', postgresql.ENUM('available', 'in_service', 'maintenance', 'retired', name='vehicle_status'), autoincrement=False, nullable=False),
    sa.Column('event_time', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('notes', sa.TEXT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.vehicle_id'], name=op.f('vehicle_status_events_vehicle_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('event_id', name=op.f('vehicle_status_events_pkey'))
    )
    op.create_table('timetables',
    sa.Column('timetable_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('vehicle_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('route_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('departure_time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.Column('arrival_time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('notes', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['route_id'], ['routes.route_id'], name=op.f('timetables_route_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.vehicle_id'], name=op.f('timetables_vehicle_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('timetable_id', name=op.f('timetables_pkey'))
    )
    op.create_table('countries',
    sa.Column('country_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('iso_code', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('country_id', name='countries_pkey'),
    sa.UniqueConstraint('iso_code', name='countries_iso_code_key', postgresql_include=[], postgresql_nulls_not_distinct=False),
    postgresql_ignore_search_path=False
    )
    op.create_table('stop_times',
    sa.Column('trip_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('stop_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('arrival_time', postgresql.TIME(), autoincrement=False, nullable=False),
    sa.Column('departure_time', postgresql.TIME(), autoincrement=False, nullable=False),
    sa.Column('stop_sequence', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['stop_id'], ['stops.stop_id'], name=op.f('stop_times_stop_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['trip_id'], ['trips.trip_id'], name=op.f('stop_times_trip_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('trip_id', 'stop_id', 'stop_sequence', name=op.f('stop_times_pkey'))
    )
    # ### end Alembic commands ###
