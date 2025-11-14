import gql from 'graphql-tag';
import * as Urql from 'urql';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  Date: { input: any; output: any; }
  DateTime: { input: any; output: any; }
  I18NLocaleCode: { input: any; output: any; }
  JSON: { input: any; output: any; }
  Long: { input: any; output: any; }
  Time: { input: any; output: any; }
};

export type ActivePassenger = {
  __typename?: 'ActivePassenger';
  alighted_at?: Maybe<Scalars['DateTime']['output']>;
  boarded_at?: Maybe<Scalars['DateTime']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  depot_id?: Maybe<Scalars['String']['output']>;
  destination_lat: Scalars['Float']['output'];
  destination_lon: Scalars['Float']['output'];
  destination_name: Scalars['String']['output'];
  direction?: Maybe<Enum_Activepassenger_Direction>;
  documentId: Scalars['ID']['output'];
  expires_at: Scalars['DateTime']['output'];
  latitude: Scalars['Float']['output'];
  longitude: Scalars['Float']['output'];
  passenger_id: Scalars['String']['output'];
  priority: Scalars['Int']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  route_id: Scalars['String']['output'];
  spawned_at: Scalars['DateTime']['output'];
  status: Enum_Activepassenger_Status;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type ActivePassengerEntityResponseCollection = {
  __typename?: 'ActivePassengerEntityResponseCollection';
  nodes: Array<ActivePassenger>;
  pageInfo: Pagination;
};

export type ActivePassengerFiltersInput = {
  alighted_at?: InputMaybe<DateTimeFilterInput>;
  and?: InputMaybe<Array<InputMaybe<ActivePassengerFiltersInput>>>;
  boarded_at?: InputMaybe<DateTimeFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  depot_id?: InputMaybe<StringFilterInput>;
  destination_lat?: InputMaybe<FloatFilterInput>;
  destination_lon?: InputMaybe<FloatFilterInput>;
  destination_name?: InputMaybe<StringFilterInput>;
  direction?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  expires_at?: InputMaybe<DateTimeFilterInput>;
  latitude?: InputMaybe<FloatFilterInput>;
  longitude?: InputMaybe<FloatFilterInput>;
  not?: InputMaybe<ActivePassengerFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<ActivePassengerFiltersInput>>>;
  passenger_id?: InputMaybe<StringFilterInput>;
  priority?: InputMaybe<IntFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  route_id?: InputMaybe<StringFilterInput>;
  spawned_at?: InputMaybe<DateTimeFilterInput>;
  status?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type ActivePassengerInput = {
  alighted_at?: InputMaybe<Scalars['DateTime']['input']>;
  boarded_at?: InputMaybe<Scalars['DateTime']['input']>;
  depot_id?: InputMaybe<Scalars['String']['input']>;
  destination_lat?: InputMaybe<Scalars['Float']['input']>;
  destination_lon?: InputMaybe<Scalars['Float']['input']>;
  destination_name?: InputMaybe<Scalars['String']['input']>;
  direction?: InputMaybe<Enum_Activepassenger_Direction>;
  expires_at?: InputMaybe<Scalars['DateTime']['input']>;
  latitude?: InputMaybe<Scalars['Float']['input']>;
  longitude?: InputMaybe<Scalars['Float']['input']>;
  passenger_id?: InputMaybe<Scalars['String']['input']>;
  priority?: InputMaybe<Scalars['Int']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  route_id?: InputMaybe<Scalars['String']['input']>;
  spawned_at?: InputMaybe<Scalars['DateTime']['input']>;
  status?: InputMaybe<Enum_Activepassenger_Status>;
};

export type AdminLevel = {
  __typename?: 'AdminLevel';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  level: Scalars['Int']['output'];
  name: Scalars['String']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  regions: Array<Maybe<Region>>;
  regions_connection?: Maybe<RegionRelationResponseCollection>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};


export type AdminLevelRegionsArgs = {
  filters?: InputMaybe<RegionFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type AdminLevelRegions_ConnectionArgs = {
  filters?: InputMaybe<RegionFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type AdminLevelEntityResponseCollection = {
  __typename?: 'AdminLevelEntityResponseCollection';
  nodes: Array<AdminLevel>;
  pageInfo: Pagination;
};

export type AdminLevelFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<AdminLevelFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  level?: InputMaybe<IntFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<AdminLevelFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<AdminLevelFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  regions?: InputMaybe<RegionFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type AdminLevelInput = {
  description?: InputMaybe<Scalars['String']['input']>;
  level?: InputMaybe<Scalars['Int']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  regions?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
};

export type Agency = {
  __typename?: 'Agency';
  agency_email?: Maybe<Scalars['String']['output']>;
  agency_fare_url?: Maybe<Scalars['String']['output']>;
  agency_id?: Maybe<Scalars['String']['output']>;
  agency_lang?: Maybe<Scalars['String']['output']>;
  agency_name: Scalars['String']['output'];
  agency_phone?: Maybe<Scalars['String']['output']>;
  agency_timezone: Scalars['String']['output'];
  agency_url: Scalars['String']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  is_active?: Maybe<Scalars['Boolean']['output']>;
  locale?: Maybe<Scalars['String']['output']>;
  localizations: Array<Maybe<Agency>>;
  localizations_connection?: Maybe<AgencyRelationResponseCollection>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  routes: Array<Maybe<Route>>;
  routes_connection?: Maybe<RouteRelationResponseCollection>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};


export type AgencyLocalizationsArgs = {
  filters?: InputMaybe<AgencyFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type AgencyLocalizations_ConnectionArgs = {
  filters?: InputMaybe<AgencyFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type AgencyRoutesArgs = {
  filters?: InputMaybe<RouteFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type AgencyRoutes_ConnectionArgs = {
  filters?: InputMaybe<RouteFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type AgencyEntityResponseCollection = {
  __typename?: 'AgencyEntityResponseCollection';
  nodes: Array<Agency>;
  pageInfo: Pagination;
};

export type AgencyFiltersInput = {
  agency_email?: InputMaybe<StringFilterInput>;
  agency_fare_url?: InputMaybe<StringFilterInput>;
  agency_id?: InputMaybe<StringFilterInput>;
  agency_lang?: InputMaybe<StringFilterInput>;
  agency_name?: InputMaybe<StringFilterInput>;
  agency_phone?: InputMaybe<StringFilterInput>;
  agency_timezone?: InputMaybe<StringFilterInput>;
  agency_url?: InputMaybe<StringFilterInput>;
  and?: InputMaybe<Array<InputMaybe<AgencyFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  locale?: InputMaybe<StringFilterInput>;
  localizations?: InputMaybe<AgencyFiltersInput>;
  not?: InputMaybe<AgencyFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<AgencyFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  routes?: InputMaybe<RouteFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type AgencyInput = {
  agency_email?: InputMaybe<Scalars['String']['input']>;
  agency_fare_url?: InputMaybe<Scalars['String']['input']>;
  agency_id?: InputMaybe<Scalars['String']['input']>;
  agency_lang?: InputMaybe<Scalars['String']['input']>;
  agency_name?: InputMaybe<Scalars['String']['input']>;
  agency_phone?: InputMaybe<Scalars['String']['input']>;
  agency_timezone?: InputMaybe<Scalars['String']['input']>;
  agency_url?: InputMaybe<Scalars['String']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  routes?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
};

export type AgencyRelationResponseCollection = {
  __typename?: 'AgencyRelationResponseCollection';
  nodes: Array<Agency>;
};

export type Block = {
  __typename?: 'Block';
  block_id: Scalars['String']['output'];
  block_name?: Maybe<Scalars['String']['output']>;
  break_duration_minutes?: Maybe<Scalars['Int']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  end_time?: Maybe<Scalars['Time']['output']>;
  is_active: Scalars['Boolean']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  route?: Maybe<Route>;
  start_time?: Maybe<Scalars['Time']['output']>;
  total_distance_km?: Maybe<Scalars['Float']['output']>;
  total_duration_minutes?: Maybe<Scalars['Int']['output']>;
  total_revenue_km?: Maybe<Scalars['Float']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type BlockEntityResponseCollection = {
  __typename?: 'BlockEntityResponseCollection';
  nodes: Array<Block>;
  pageInfo: Pagination;
};

export type BlockFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<BlockFiltersInput>>>;
  block_id?: InputMaybe<StringFilterInput>;
  block_name?: InputMaybe<StringFilterInput>;
  break_duration_minutes?: InputMaybe<IntFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  end_time?: InputMaybe<TimeFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  not?: InputMaybe<BlockFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<BlockFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  route?: InputMaybe<RouteFiltersInput>;
  start_time?: InputMaybe<TimeFilterInput>;
  total_distance_km?: InputMaybe<FloatFilterInput>;
  total_duration_minutes?: InputMaybe<IntFilterInput>;
  total_revenue_km?: InputMaybe<FloatFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type BlockInput = {
  block_id?: InputMaybe<Scalars['String']['input']>;
  block_name?: InputMaybe<Scalars['String']['input']>;
  break_duration_minutes?: InputMaybe<Scalars['Int']['input']>;
  end_time?: InputMaybe<Scalars['Time']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  route?: InputMaybe<Scalars['ID']['input']>;
  start_time?: InputMaybe<Scalars['Time']['input']>;
  total_distance_km?: InputMaybe<Scalars['Float']['input']>;
  total_duration_minutes?: InputMaybe<Scalars['Int']['input']>;
  total_revenue_km?: InputMaybe<Scalars['Float']['input']>;
};

export type BlockRelationResponseCollection = {
  __typename?: 'BlockRelationResponseCollection';
  nodes: Array<Block>;
};

export type BooleanFilterInput = {
  and?: InputMaybe<Array<InputMaybe<Scalars['Boolean']['input']>>>;
  between?: InputMaybe<Array<InputMaybe<Scalars['Boolean']['input']>>>;
  contains?: InputMaybe<Scalars['Boolean']['input']>;
  containsi?: InputMaybe<Scalars['Boolean']['input']>;
  endsWith?: InputMaybe<Scalars['Boolean']['input']>;
  eq?: InputMaybe<Scalars['Boolean']['input']>;
  eqi?: InputMaybe<Scalars['Boolean']['input']>;
  gt?: InputMaybe<Scalars['Boolean']['input']>;
  gte?: InputMaybe<Scalars['Boolean']['input']>;
  in?: InputMaybe<Array<InputMaybe<Scalars['Boolean']['input']>>>;
  lt?: InputMaybe<Scalars['Boolean']['input']>;
  lte?: InputMaybe<Scalars['Boolean']['input']>;
  ne?: InputMaybe<Scalars['Boolean']['input']>;
  nei?: InputMaybe<Scalars['Boolean']['input']>;
  not?: InputMaybe<BooleanFilterInput>;
  notContains?: InputMaybe<Scalars['Boolean']['input']>;
  notContainsi?: InputMaybe<Scalars['Boolean']['input']>;
  notIn?: InputMaybe<Array<InputMaybe<Scalars['Boolean']['input']>>>;
  notNull?: InputMaybe<Scalars['Boolean']['input']>;
  null?: InputMaybe<Scalars['Boolean']['input']>;
  or?: InputMaybe<Array<InputMaybe<Scalars['Boolean']['input']>>>;
  startsWith?: InputMaybe<Scalars['Boolean']['input']>;
};

export type Building = {
  __typename?: 'Building';
  addr_city?: Maybe<Scalars['String']['output']>;
  addr_housenumber?: Maybe<Scalars['String']['output']>;
  addr_street?: Maybe<Scalars['String']['output']>;
  amenity?: Maybe<Scalars['String']['output']>;
  building_id: Scalars['String']['output'];
  building_type?: Maybe<Scalars['String']['output']>;
  country?: Maybe<Country>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  full_id?: Maybe<Scalars['String']['output']>;
  height?: Maybe<Scalars['Float']['output']>;
  levels?: Maybe<Scalars['Int']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  osm_id: Scalars['Long']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type BuildingEntityResponseCollection = {
  __typename?: 'BuildingEntityResponseCollection';
  nodes: Array<Building>;
  pageInfo: Pagination;
};

export type BuildingFiltersInput = {
  addr_city?: InputMaybe<StringFilterInput>;
  addr_housenumber?: InputMaybe<StringFilterInput>;
  addr_street?: InputMaybe<StringFilterInput>;
  amenity?: InputMaybe<StringFilterInput>;
  and?: InputMaybe<Array<InputMaybe<BuildingFiltersInput>>>;
  building_id?: InputMaybe<StringFilterInput>;
  building_type?: InputMaybe<StringFilterInput>;
  country?: InputMaybe<CountryFiltersInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  full_id?: InputMaybe<StringFilterInput>;
  height?: InputMaybe<FloatFilterInput>;
  levels?: InputMaybe<IntFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<BuildingFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<BuildingFiltersInput>>>;
  osm_id?: InputMaybe<LongFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type BuildingInput = {
  addr_city?: InputMaybe<Scalars['String']['input']>;
  addr_housenumber?: InputMaybe<Scalars['String']['input']>;
  addr_street?: InputMaybe<Scalars['String']['input']>;
  amenity?: InputMaybe<Scalars['String']['input']>;
  building_id?: InputMaybe<Scalars['String']['input']>;
  building_type?: InputMaybe<Scalars['String']['input']>;
  country?: InputMaybe<Scalars['ID']['input']>;
  full_id?: InputMaybe<Scalars['String']['input']>;
  height?: InputMaybe<Scalars['Float']['input']>;
  levels?: InputMaybe<Scalars['Int']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  osm_id?: InputMaybe<Scalars['Long']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
};

export type BuildingRelationResponseCollection = {
  __typename?: 'BuildingRelationResponseCollection';
  nodes: Array<Building>;
};

export type CalendarDate = {
  __typename?: 'CalendarDate';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  date: Scalars['Date']['output'];
  description?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  exception_type: Scalars['Int']['output'];
  is_active?: Maybe<Scalars['Boolean']['output']>;
  locale?: Maybe<Scalars['String']['output']>;
  localizations: Array<Maybe<CalendarDate>>;
  localizations_connection?: Maybe<CalendarDateRelationResponseCollection>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  service?: Maybe<Service>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};


export type CalendarDateLocalizationsArgs = {
  filters?: InputMaybe<CalendarDateFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CalendarDateLocalizations_ConnectionArgs = {
  filters?: InputMaybe<CalendarDateFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type CalendarDateEntityResponseCollection = {
  __typename?: 'CalendarDateEntityResponseCollection';
  nodes: Array<CalendarDate>;
  pageInfo: Pagination;
};

export type CalendarDateFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<CalendarDateFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  date?: InputMaybe<DateFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  exception_type?: InputMaybe<IntFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  locale?: InputMaybe<StringFilterInput>;
  localizations?: InputMaybe<CalendarDateFiltersInput>;
  not?: InputMaybe<CalendarDateFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<CalendarDateFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  service?: InputMaybe<ServiceFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type CalendarDateInput = {
  date?: InputMaybe<Scalars['Date']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  exception_type?: InputMaybe<Scalars['Int']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  service?: InputMaybe<Scalars['ID']['input']>;
};

export type CalendarDateRelationResponseCollection = {
  __typename?: 'CalendarDateRelationResponseCollection';
  nodes: Array<CalendarDate>;
};

export type ComponentSpawningBuildingWeight = {
  __typename?: 'ComponentSpawningBuildingWeight';
  building_type: Enum_Componentspawningbuildingweight_Building_Type;
  id: Scalars['ID']['output'];
  is_active?: Maybe<Scalars['Boolean']['output']>;
  peak_multiplier?: Maybe<Scalars['Float']['output']>;
  weight: Scalars['Float']['output'];
};

export type ComponentSpawningDayMultiplier = {
  __typename?: 'ComponentSpawningDayMultiplier';
  day_of_week: Enum_Componentspawningdaymultiplier_Day_Of_Week;
  id: Scalars['ID']['output'];
  multiplier: Scalars['Float']['output'];
};

export type ComponentSpawningDistributionParams = {
  __typename?: 'ComponentSpawningDistributionParams';
  day_multipliers?: Maybe<Scalars['JSON']['output']>;
  hourly_rates?: Maybe<Scalars['JSON']['output']>;
  id: Scalars['ID']['output'];
  max_trip_distance_ratio: Scalars['Float']['output'];
  min_spawn_interval_seconds: Scalars['Int']['output'];
  min_trip_distance_meters: Scalars['Int']['output'];
  passengers_per_building_per_hour: Scalars['Float']['output'];
  spatial_base?: Maybe<Scalars['Float']['output']>;
  spawn_radius_meters: Scalars['Int']['output'];
  trip_distance_mean_meters: Scalars['Int']['output'];
  trip_distance_std_meters: Scalars['Int']['output'];
};

export type ComponentSpawningHourlyPattern = {
  __typename?: 'ComponentSpawningHourlyPattern';
  hour: Scalars['Int']['output'];
  id: Scalars['ID']['output'];
  label?: Maybe<Scalars['String']['output']>;
  spawn_rate: Scalars['Float']['output'];
};

export type ComponentSpawningLanduseWeight = {
  __typename?: 'ComponentSpawningLanduseWeight';
  id: Scalars['ID']['output'];
  is_active?: Maybe<Scalars['Boolean']['output']>;
  landuse_type: Enum_Componentspawninglanduseweight_Landuse_Type;
  peak_multiplier?: Maybe<Scalars['Float']['output']>;
  weight: Scalars['Float']['output'];
};

export type ComponentSpawningPoiWeight = {
  __typename?: 'ComponentSpawningPoiWeight';
  id: Scalars['ID']['output'];
  is_active?: Maybe<Scalars['Boolean']['output']>;
  peak_multiplier?: Maybe<Scalars['Float']['output']>;
  poi_type: Enum_Componentspawningpoiweight_Poi_Type;
  weight: Scalars['Float']['output'];
};

export type Country = {
  __typename?: 'Country';
  buildings: Array<Maybe<Building>>;
  buildings_connection?: Maybe<BuildingRelationResponseCollection>;
  code: Scalars['String']['output'];
  country_id: Scalars['String']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  currency?: Maybe<Scalars['String']['output']>;
  depots: Array<Maybe<Depot>>;
  depots_connection?: Maybe<DepotRelationResponseCollection>;
  documentId: Scalars['ID']['output'];
  drivers: Array<Maybe<Driver>>;
  drivers_connection?: Maybe<DriverRelationResponseCollection>;
  geodata_import_status?: Maybe<Scalars['JSON']['output']>;
  geodata_last_import?: Maybe<Scalars['DateTime']['output']>;
  highways: Array<Maybe<Highway>>;
  highways_connection?: Maybe<HighwayRelationResponseCollection>;
  import_admin?: Maybe<Scalars['JSON']['output']>;
  import_amenity?: Maybe<Scalars['JSON']['output']>;
  import_building?: Maybe<Scalars['JSON']['output']>;
  import_highway?: Maybe<Scalars['JSON']['output']>;
  import_landuse?: Maybe<Scalars['JSON']['output']>;
  is_active: Scalars['Boolean']['output'];
  landuse_zones: Array<Maybe<LanduseZone>>;
  landuse_zones_connection?: Maybe<LanduseZoneRelationResponseCollection>;
  name: Scalars['String']['output'];
  places: Array<Maybe<Place>>;
  places_connection?: Maybe<PlaceRelationResponseCollection>;
  pois: Array<Maybe<Poi>>;
  pois_connection?: Maybe<PoiRelationResponseCollection>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  regions: Array<Maybe<Region>>;
  regions_connection?: Maybe<RegionRelationResponseCollection>;
  routes: Array<Maybe<Route>>;
  routes_connection?: Maybe<RouteRelationResponseCollection>;
  timezone?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  vehicles: Array<Maybe<Vehicle>>;
  vehicles_connection?: Maybe<VehicleRelationResponseCollection>;
};


export type CountryBuildingsArgs = {
  filters?: InputMaybe<BuildingFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryBuildings_ConnectionArgs = {
  filters?: InputMaybe<BuildingFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryDepotsArgs = {
  filters?: InputMaybe<DepotFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryDepots_ConnectionArgs = {
  filters?: InputMaybe<DepotFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryDriversArgs = {
  filters?: InputMaybe<DriverFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryDrivers_ConnectionArgs = {
  filters?: InputMaybe<DriverFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryHighwaysArgs = {
  filters?: InputMaybe<HighwayFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryHighways_ConnectionArgs = {
  filters?: InputMaybe<HighwayFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryLanduse_ZonesArgs = {
  filters?: InputMaybe<LanduseZoneFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryLanduse_Zones_ConnectionArgs = {
  filters?: InputMaybe<LanduseZoneFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryPlacesArgs = {
  filters?: InputMaybe<PlaceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryPlaces_ConnectionArgs = {
  filters?: InputMaybe<PlaceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryPoisArgs = {
  filters?: InputMaybe<PoiFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryPois_ConnectionArgs = {
  filters?: InputMaybe<PoiFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryRegionsArgs = {
  filters?: InputMaybe<RegionFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryRegions_ConnectionArgs = {
  filters?: InputMaybe<RegionFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryRoutesArgs = {
  filters?: InputMaybe<RouteFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryRoutes_ConnectionArgs = {
  filters?: InputMaybe<RouteFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryVehiclesArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type CountryVehicles_ConnectionArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type CountryEntityResponseCollection = {
  __typename?: 'CountryEntityResponseCollection';
  nodes: Array<Country>;
  pageInfo: Pagination;
};

export type CountryFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<CountryFiltersInput>>>;
  buildings?: InputMaybe<BuildingFiltersInput>;
  code?: InputMaybe<StringFilterInput>;
  country_id?: InputMaybe<StringFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  currency?: InputMaybe<StringFilterInput>;
  depots?: InputMaybe<DepotFiltersInput>;
  documentId?: InputMaybe<IdFilterInput>;
  drivers?: InputMaybe<DriverFiltersInput>;
  geodata_import_status?: InputMaybe<JsonFilterInput>;
  geodata_last_import?: InputMaybe<DateTimeFilterInput>;
  highways?: InputMaybe<HighwayFiltersInput>;
  import_admin?: InputMaybe<JsonFilterInput>;
  import_amenity?: InputMaybe<JsonFilterInput>;
  import_building?: InputMaybe<JsonFilterInput>;
  import_highway?: InputMaybe<JsonFilterInput>;
  import_landuse?: InputMaybe<JsonFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  landuse_zones?: InputMaybe<LanduseZoneFiltersInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<CountryFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<CountryFiltersInput>>>;
  places?: InputMaybe<PlaceFiltersInput>;
  pois?: InputMaybe<PoiFiltersInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  regions?: InputMaybe<RegionFiltersInput>;
  routes?: InputMaybe<RouteFiltersInput>;
  timezone?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  vehicles?: InputMaybe<VehicleFiltersInput>;
};

export type CountryInput = {
  buildings?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  code?: InputMaybe<Scalars['String']['input']>;
  country_id?: InputMaybe<Scalars['String']['input']>;
  currency?: InputMaybe<Scalars['String']['input']>;
  depots?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  drivers?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  geodata_import_status?: InputMaybe<Scalars['JSON']['input']>;
  geodata_last_import?: InputMaybe<Scalars['DateTime']['input']>;
  highways?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  import_admin?: InputMaybe<Scalars['JSON']['input']>;
  import_amenity?: InputMaybe<Scalars['JSON']['input']>;
  import_building?: InputMaybe<Scalars['JSON']['input']>;
  import_highway?: InputMaybe<Scalars['JSON']['input']>;
  import_landuse?: InputMaybe<Scalars['JSON']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  landuse_zones?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  name?: InputMaybe<Scalars['String']['input']>;
  places?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  pois?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  regions?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  routes?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  timezone?: InputMaybe<Scalars['String']['input']>;
  vehicles?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
};

export type DateFilterInput = {
  and?: InputMaybe<Array<InputMaybe<Scalars['Date']['input']>>>;
  between?: InputMaybe<Array<InputMaybe<Scalars['Date']['input']>>>;
  contains?: InputMaybe<Scalars['Date']['input']>;
  containsi?: InputMaybe<Scalars['Date']['input']>;
  endsWith?: InputMaybe<Scalars['Date']['input']>;
  eq?: InputMaybe<Scalars['Date']['input']>;
  eqi?: InputMaybe<Scalars['Date']['input']>;
  gt?: InputMaybe<Scalars['Date']['input']>;
  gte?: InputMaybe<Scalars['Date']['input']>;
  in?: InputMaybe<Array<InputMaybe<Scalars['Date']['input']>>>;
  lt?: InputMaybe<Scalars['Date']['input']>;
  lte?: InputMaybe<Scalars['Date']['input']>;
  ne?: InputMaybe<Scalars['Date']['input']>;
  nei?: InputMaybe<Scalars['Date']['input']>;
  not?: InputMaybe<DateFilterInput>;
  notContains?: InputMaybe<Scalars['Date']['input']>;
  notContainsi?: InputMaybe<Scalars['Date']['input']>;
  notIn?: InputMaybe<Array<InputMaybe<Scalars['Date']['input']>>>;
  notNull?: InputMaybe<Scalars['Boolean']['input']>;
  null?: InputMaybe<Scalars['Boolean']['input']>;
  or?: InputMaybe<Array<InputMaybe<Scalars['Date']['input']>>>;
  startsWith?: InputMaybe<Scalars['Date']['input']>;
};

export type DateTimeFilterInput = {
  and?: InputMaybe<Array<InputMaybe<Scalars['DateTime']['input']>>>;
  between?: InputMaybe<Array<InputMaybe<Scalars['DateTime']['input']>>>;
  contains?: InputMaybe<Scalars['DateTime']['input']>;
  containsi?: InputMaybe<Scalars['DateTime']['input']>;
  endsWith?: InputMaybe<Scalars['DateTime']['input']>;
  eq?: InputMaybe<Scalars['DateTime']['input']>;
  eqi?: InputMaybe<Scalars['DateTime']['input']>;
  gt?: InputMaybe<Scalars['DateTime']['input']>;
  gte?: InputMaybe<Scalars['DateTime']['input']>;
  in?: InputMaybe<Array<InputMaybe<Scalars['DateTime']['input']>>>;
  lt?: InputMaybe<Scalars['DateTime']['input']>;
  lte?: InputMaybe<Scalars['DateTime']['input']>;
  ne?: InputMaybe<Scalars['DateTime']['input']>;
  nei?: InputMaybe<Scalars['DateTime']['input']>;
  not?: InputMaybe<DateTimeFilterInput>;
  notContains?: InputMaybe<Scalars['DateTime']['input']>;
  notContainsi?: InputMaybe<Scalars['DateTime']['input']>;
  notIn?: InputMaybe<Array<InputMaybe<Scalars['DateTime']['input']>>>;
  notNull?: InputMaybe<Scalars['Boolean']['input']>;
  null?: InputMaybe<Scalars['Boolean']['input']>;
  or?: InputMaybe<Array<InputMaybe<Scalars['DateTime']['input']>>>;
  startsWith?: InputMaybe<Scalars['DateTime']['input']>;
};

export type DeleteMutationResponse = {
  __typename?: 'DeleteMutationResponse';
  documentId: Scalars['ID']['output'];
};

export type Depot = {
  __typename?: 'Depot';
  activity_level?: Maybe<Scalars['Float']['output']>;
  address?: Maybe<Scalars['String']['output']>;
  associated_routes: Array<Maybe<RouteDepot>>;
  associated_routes_connection?: Maybe<RouteDepotRelationResponseCollection>;
  capacity?: Maybe<Scalars['Int']['output']>;
  country?: Maybe<Country>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  depot_id: Scalars['String']['output'];
  documentId: Scalars['ID']['output'];
  drivers: Array<Maybe<Driver>>;
  drivers_connection?: Maybe<DriverRelationResponseCollection>;
  is_active: Scalars['Boolean']['output'];
  latitude: Scalars['Float']['output'];
  longitude: Scalars['Float']['output'];
  name: Scalars['String']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  vehicles: Array<Maybe<Vehicle>>;
  vehicles_connection?: Maybe<VehicleRelationResponseCollection>;
};


export type DepotAssociated_RoutesArgs = {
  filters?: InputMaybe<RouteDepotFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type DepotAssociated_Routes_ConnectionArgs = {
  filters?: InputMaybe<RouteDepotFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type DepotDriversArgs = {
  filters?: InputMaybe<DriverFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type DepotDrivers_ConnectionArgs = {
  filters?: InputMaybe<DriverFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type DepotVehiclesArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type DepotVehicles_ConnectionArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type DepotEntityResponseCollection = {
  __typename?: 'DepotEntityResponseCollection';
  nodes: Array<Depot>;
  pageInfo: Pagination;
};

export type DepotFiltersInput = {
  activity_level?: InputMaybe<FloatFilterInput>;
  address?: InputMaybe<StringFilterInput>;
  and?: InputMaybe<Array<InputMaybe<DepotFiltersInput>>>;
  associated_routes?: InputMaybe<RouteDepotFiltersInput>;
  capacity?: InputMaybe<IntFilterInput>;
  country?: InputMaybe<CountryFiltersInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  depot_id?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  drivers?: InputMaybe<DriverFiltersInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  latitude?: InputMaybe<FloatFilterInput>;
  longitude?: InputMaybe<FloatFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<DepotFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<DepotFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  vehicles?: InputMaybe<VehicleFiltersInput>;
};

export type DepotInput = {
  activity_level?: InputMaybe<Scalars['Float']['input']>;
  address?: InputMaybe<Scalars['String']['input']>;
  associated_routes?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  capacity?: InputMaybe<Scalars['Int']['input']>;
  country?: InputMaybe<Scalars['ID']['input']>;
  depot_id?: InputMaybe<Scalars['String']['input']>;
  drivers?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  latitude?: InputMaybe<Scalars['Float']['input']>;
  longitude?: InputMaybe<Scalars['Float']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  vehicles?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
};

export type DepotRelationResponseCollection = {
  __typename?: 'DepotRelationResponseCollection';
  nodes: Array<Depot>;
};

export type Driver = {
  __typename?: 'Driver';
  assigned_vehicles: Array<Maybe<Vehicle>>;
  assigned_vehicles_connection?: Maybe<VehicleRelationResponseCollection>;
  country?: Maybe<Country>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  driver_id: Scalars['String']['output'];
  email?: Maybe<Scalars['String']['output']>;
  employment_status: Enum_Driver_Employment_Status;
  hire_date?: Maybe<Scalars['Date']['output']>;
  home_depot?: Maybe<Depot>;
  license_no: Scalars['String']['output'];
  name: Scalars['String']['output'];
  phone?: Maybe<Scalars['String']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};


export type DriverAssigned_VehiclesArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type DriverAssigned_Vehicles_ConnectionArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type DriverEntityResponseCollection = {
  __typename?: 'DriverEntityResponseCollection';
  nodes: Array<Driver>;
  pageInfo: Pagination;
};

export type DriverFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<DriverFiltersInput>>>;
  assigned_vehicles?: InputMaybe<VehicleFiltersInput>;
  country?: InputMaybe<CountryFiltersInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  driver_id?: InputMaybe<StringFilterInput>;
  email?: InputMaybe<StringFilterInput>;
  employment_status?: InputMaybe<StringFilterInput>;
  hire_date?: InputMaybe<DateFilterInput>;
  home_depot?: InputMaybe<DepotFiltersInput>;
  license_no?: InputMaybe<StringFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<DriverFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<DriverFiltersInput>>>;
  phone?: InputMaybe<StringFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type DriverInput = {
  assigned_vehicles?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  country?: InputMaybe<Scalars['ID']['input']>;
  driver_id?: InputMaybe<Scalars['String']['input']>;
  email?: InputMaybe<Scalars['String']['input']>;
  employment_status?: InputMaybe<Enum_Driver_Employment_Status>;
  hire_date?: InputMaybe<Scalars['Date']['input']>;
  home_depot?: InputMaybe<Scalars['ID']['input']>;
  license_no?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  phone?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
};

export type DriverRelationResponseCollection = {
  __typename?: 'DriverRelationResponseCollection';
  nodes: Array<Driver>;
};

export enum Enum_Activepassenger_Direction {
  Inbound = 'INBOUND',
  Outbound = 'OUTBOUND'
}

export enum Enum_Activepassenger_Status {
  Completed = 'COMPLETED',
  Expired = 'EXPIRED',
  Onboard = 'ONBOARD',
  Waiting = 'WAITING'
}

export enum Enum_Componentspawningbuildingweight_Building_Type {
  Apartments = 'apartments',
  Civic = 'civic',
  Commercial = 'commercial',
  Government = 'government',
  Hospital = 'hospital',
  Hotel = 'hotel',
  House = 'house',
  Industrial = 'industrial',
  Office = 'office',
  Residential = 'residential',
  Retail = 'retail',
  School = 'school',
  University = 'university',
  Warehouse = 'warehouse'
}

export enum Enum_Componentspawningdaymultiplier_Day_Of_Week {
  Friday = 'friday',
  Monday = 'monday',
  Saturday = 'saturday',
  Sunday = 'sunday',
  Thursday = 'thursday',
  Tuesday = 'tuesday',
  Wednesday = 'wednesday'
}

export enum Enum_Componentspawninglanduseweight_Landuse_Type {
  Commercial = 'commercial',
  Farmland = 'farmland',
  Forest = 'forest',
  Industrial = 'industrial',
  Institutional = 'institutional',
  MixedUse = 'mixed_use',
  Recreation = 'recreation',
  Residential = 'residential',
  Retail = 'retail'
}

export enum Enum_Componentspawningpoiweight_Poi_Type {
  Airport = 'airport',
  Beach = 'beach',
  BusStation = 'bus_station',
  Church = 'church',
  Clinic = 'clinic',
  FerryTerminal = 'ferry_terminal',
  Government = 'government',
  Hospital = 'hospital',
  Hotel = 'hotel',
  Marketplace = 'marketplace',
  Office = 'office',
  Park = 'park',
  Restaurant = 'restaurant',
  School = 'school',
  ShoppingCenter = 'shopping_center',
  University = 'university'
}

export enum Enum_Driver_Employment_Status {
  Active = 'active',
  Inactive = 'inactive',
  Suspended = 'suspended',
  Terminated = 'terminated'
}

export enum Enum_Geofencegeometry_Geometry_Type {
  Circle = 'circle',
  Linestring = 'linestring',
  Polygon = 'polygon'
}

export enum Enum_Geofence_Type {
  BoardingZone = 'boarding_zone',
  Custom = 'custom',
  Depot = 'depot',
  Proximity = 'proximity',
  Restricted = 'restricted',
  ServiceArea = 'service_area'
}

export enum Enum_Highway_Highway_Type {
  Cycleway = 'cycleway',
  Footway = 'footway',
  LivingStreet = 'living_street',
  Motorway = 'motorway',
  Other = 'other',
  Path = 'path',
  Pedestrian = 'pedestrian',
  Primary = 'primary',
  Residential = 'residential',
  Secondary = 'secondary',
  Service = 'service',
  Steps = 'steps',
  Tertiary = 'tertiary',
  Track = 'track',
  Trunk = 'trunk',
  Unclassified = 'unclassified'
}

export enum Enum_Landusezone_Zone_Type {
  Commercial = 'commercial',
  Farmland = 'farmland',
  Forest = 'forest',
  Industrial = 'industrial',
  Institutional = 'institutional',
  MixedUse = 'mixed_use',
  Other = 'other',
  Recreation = 'recreation',
  Residential = 'residential',
  Transportation = 'transportation',
  Water = 'water'
}

export enum Enum_Operationalconfiguration_Value_Type {
  Boolean = 'boolean',
  Number = 'number',
  Object = 'object',
  String = 'string'
}

export enum Enum_Place_Place_Type {
  City = 'city',
  CommercialDistrict = 'commercial_district',
  District = 'district',
  Hamlet = 'hamlet',
  IndustrialZone = 'industrial_zone',
  Locality = 'locality',
  Neighborhood = 'neighborhood',
  Other = 'other',
  Quarter = 'quarter',
  ResidentialArea = 'residential_area',
  Settlement = 'settlement',
  Suburb = 'suburb',
  Town = 'town',
  Village = 'village'
}

export enum Enum_Poi_Poi_Type {
  Airport = 'airport',
  Beach = 'beach',
  BusStation = 'bus_station',
  Church = 'church',
  Clinic = 'clinic',
  FerryTerminal = 'ferry_terminal',
  Government = 'government',
  Hospital = 'hospital',
  Hotel = 'hotel',
  Industrial = 'industrial',
  Marketplace = 'marketplace',
  Office = 'office',
  Other = 'other',
  Park = 'park',
  Residential = 'residential',
  Restaurant = 'restaurant',
  School = 'school',
  ShoppingCenter = 'shopping_center',
  University = 'university'
}

export enum Enum_Stop_Location_Type {
  BoardingArea = 'boarding_area',
  Entrance = 'entrance',
  GenericNode = 'generic_node',
  Station = 'station',
  Stop = 'stop'
}

export enum Enum_Stop_Wheelchair_Boarding {
  Accessible = 'accessible',
  NotAccessible = 'not_accessible',
  Unknown = 'unknown'
}

export enum Enum_Trip_Bikes_Allowed {
  Allowed = 'allowed',
  NotAllowed = 'not_allowed',
  Unknown = 'unknown'
}

export enum Enum_Trip_Direction_Id {
  Inbound = 'inbound',
  Outbound = 'outbound'
}

export enum Enum_Trip_Wheelchair_Accessible {
  Accessible = 'accessible',
  NotAccessible = 'not_accessible',
  Unknown = 'unknown'
}

export enum Enum_Vehicleevent_Event_Type {
  ArriveStop = 'arrive_stop',
  DepartStop = 'depart_stop',
  DoorEvent = 'door_event',
  DriverConfirmAlighting = 'driver_confirm_alighting',
  DriverConfirmBoarding = 'driver_confirm_boarding',
  GpsPosition = 'gps_position',
  PassengerCount = 'passenger_count',
  RfidTap = 'rfid_tap'
}

export enum Enum_Vehicle_Performance_Profile {
  Eco = 'eco',
  Express = 'express',
  Performance = 'performance',
  Standard = 'standard'
}

export type FareAttribute = {
  __typename?: 'FareAttribute';
  agency?: Maybe<Agency>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  currency_type: Scalars['String']['output'];
  documentId: Scalars['ID']['output'];
  fare_id: Scalars['String']['output'];
  fare_rules: Array<Maybe<FareRule>>;
  fare_rules_connection?: Maybe<FareRuleRelationResponseCollection>;
  is_active?: Maybe<Scalars['Boolean']['output']>;
  locale?: Maybe<Scalars['String']['output']>;
  localizations: Array<Maybe<FareAttribute>>;
  localizations_connection?: Maybe<FareAttributeRelationResponseCollection>;
  payment_method: Scalars['Int']['output'];
  price: Scalars['Float']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  transfer_duration?: Maybe<Scalars['Int']['output']>;
  transfers?: Maybe<Scalars['Int']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};


export type FareAttributeFare_RulesArgs = {
  filters?: InputMaybe<FareRuleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type FareAttributeFare_Rules_ConnectionArgs = {
  filters?: InputMaybe<FareRuleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type FareAttributeLocalizationsArgs = {
  filters?: InputMaybe<FareAttributeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type FareAttributeLocalizations_ConnectionArgs = {
  filters?: InputMaybe<FareAttributeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type FareAttributeEntityResponseCollection = {
  __typename?: 'FareAttributeEntityResponseCollection';
  nodes: Array<FareAttribute>;
  pageInfo: Pagination;
};

export type FareAttributeFiltersInput = {
  agency?: InputMaybe<AgencyFiltersInput>;
  and?: InputMaybe<Array<InputMaybe<FareAttributeFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  currency_type?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  fare_id?: InputMaybe<StringFilterInput>;
  fare_rules?: InputMaybe<FareRuleFiltersInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  locale?: InputMaybe<StringFilterInput>;
  localizations?: InputMaybe<FareAttributeFiltersInput>;
  not?: InputMaybe<FareAttributeFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<FareAttributeFiltersInput>>>;
  payment_method?: InputMaybe<IntFilterInput>;
  price?: InputMaybe<FloatFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  transfer_duration?: InputMaybe<IntFilterInput>;
  transfers?: InputMaybe<IntFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type FareAttributeInput = {
  agency?: InputMaybe<Scalars['ID']['input']>;
  currency_type?: InputMaybe<Scalars['String']['input']>;
  fare_id?: InputMaybe<Scalars['String']['input']>;
  fare_rules?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  payment_method?: InputMaybe<Scalars['Int']['input']>;
  price?: InputMaybe<Scalars['Float']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  transfer_duration?: InputMaybe<Scalars['Int']['input']>;
  transfers?: InputMaybe<Scalars['Int']['input']>;
};

export type FareAttributeRelationResponseCollection = {
  __typename?: 'FareAttributeRelationResponseCollection';
  nodes: Array<FareAttribute>;
};

export type FareRule = {
  __typename?: 'FareRule';
  contains_id?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  destination_id?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  fare_attribute?: Maybe<FareAttribute>;
  is_active?: Maybe<Scalars['Boolean']['output']>;
  origin_id?: Maybe<Scalars['String']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  route?: Maybe<Route>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type FareRuleEntityResponseCollection = {
  __typename?: 'FareRuleEntityResponseCollection';
  nodes: Array<FareRule>;
  pageInfo: Pagination;
};

export type FareRuleFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<FareRuleFiltersInput>>>;
  contains_id?: InputMaybe<StringFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  destination_id?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  fare_attribute?: InputMaybe<FareAttributeFiltersInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  not?: InputMaybe<FareRuleFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<FareRuleFiltersInput>>>;
  origin_id?: InputMaybe<StringFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  route?: InputMaybe<RouteFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type FareRuleInput = {
  contains_id?: InputMaybe<Scalars['String']['input']>;
  destination_id?: InputMaybe<Scalars['String']['input']>;
  fare_attribute?: InputMaybe<Scalars['ID']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  origin_id?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  route?: InputMaybe<Scalars['ID']['input']>;
};

export type FareRuleRelationResponseCollection = {
  __typename?: 'FareRuleRelationResponseCollection';
  nodes: Array<FareRule>;
};

export type FeedInfo = {
  __typename?: 'FeedInfo';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  default_lang?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  feed_contact_email?: Maybe<Scalars['String']['output']>;
  feed_contact_url?: Maybe<Scalars['String']['output']>;
  feed_end_date?: Maybe<Scalars['Date']['output']>;
  feed_lang: Scalars['String']['output'];
  feed_publisher_name: Scalars['String']['output'];
  feed_publisher_url: Scalars['String']['output'];
  feed_start_date?: Maybe<Scalars['Date']['output']>;
  feed_version?: Maybe<Scalars['String']['output']>;
  is_active?: Maybe<Scalars['Boolean']['output']>;
  locale?: Maybe<Scalars['String']['output']>;
  localizations: Array<Maybe<FeedInfo>>;
  localizations_connection?: Maybe<FeedInfoRelationResponseCollection>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};


export type FeedInfoLocalizationsArgs = {
  filters?: InputMaybe<FeedInfoFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type FeedInfoLocalizations_ConnectionArgs = {
  filters?: InputMaybe<FeedInfoFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type FeedInfoEntityResponseCollection = {
  __typename?: 'FeedInfoEntityResponseCollection';
  nodes: Array<FeedInfo>;
  pageInfo: Pagination;
};

export type FeedInfoFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<FeedInfoFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  default_lang?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  feed_contact_email?: InputMaybe<StringFilterInput>;
  feed_contact_url?: InputMaybe<StringFilterInput>;
  feed_end_date?: InputMaybe<DateFilterInput>;
  feed_lang?: InputMaybe<StringFilterInput>;
  feed_publisher_name?: InputMaybe<StringFilterInput>;
  feed_publisher_url?: InputMaybe<StringFilterInput>;
  feed_start_date?: InputMaybe<DateFilterInput>;
  feed_version?: InputMaybe<StringFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  locale?: InputMaybe<StringFilterInput>;
  localizations?: InputMaybe<FeedInfoFiltersInput>;
  not?: InputMaybe<FeedInfoFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<FeedInfoFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type FeedInfoInput = {
  default_lang?: InputMaybe<Scalars['String']['input']>;
  feed_contact_email?: InputMaybe<Scalars['String']['input']>;
  feed_contact_url?: InputMaybe<Scalars['String']['input']>;
  feed_end_date?: InputMaybe<Scalars['Date']['input']>;
  feed_lang?: InputMaybe<Scalars['String']['input']>;
  feed_publisher_name?: InputMaybe<Scalars['String']['input']>;
  feed_publisher_url?: InputMaybe<Scalars['String']['input']>;
  feed_start_date?: InputMaybe<Scalars['Date']['input']>;
  feed_version?: InputMaybe<Scalars['String']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
};

export type FeedInfoRelationResponseCollection = {
  __typename?: 'FeedInfoRelationResponseCollection';
  nodes: Array<FeedInfo>;
};

export type FileInfoInput = {
  alternativeText?: InputMaybe<Scalars['String']['input']>;
  caption?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
};

export type FloatFilterInput = {
  and?: InputMaybe<Array<InputMaybe<Scalars['Float']['input']>>>;
  between?: InputMaybe<Array<InputMaybe<Scalars['Float']['input']>>>;
  contains?: InputMaybe<Scalars['Float']['input']>;
  containsi?: InputMaybe<Scalars['Float']['input']>;
  endsWith?: InputMaybe<Scalars['Float']['input']>;
  eq?: InputMaybe<Scalars['Float']['input']>;
  eqi?: InputMaybe<Scalars['Float']['input']>;
  gt?: InputMaybe<Scalars['Float']['input']>;
  gte?: InputMaybe<Scalars['Float']['input']>;
  in?: InputMaybe<Array<InputMaybe<Scalars['Float']['input']>>>;
  lt?: InputMaybe<Scalars['Float']['input']>;
  lte?: InputMaybe<Scalars['Float']['input']>;
  ne?: InputMaybe<Scalars['Float']['input']>;
  nei?: InputMaybe<Scalars['Float']['input']>;
  not?: InputMaybe<FloatFilterInput>;
  notContains?: InputMaybe<Scalars['Float']['input']>;
  notContainsi?: InputMaybe<Scalars['Float']['input']>;
  notIn?: InputMaybe<Array<InputMaybe<Scalars['Float']['input']>>>;
  notNull?: InputMaybe<Scalars['Boolean']['input']>;
  null?: InputMaybe<Scalars['Boolean']['input']>;
  or?: InputMaybe<Array<InputMaybe<Scalars['Float']['input']>>>;
  startsWith?: InputMaybe<Scalars['Float']['input']>;
};

export type Frequency = {
  __typename?: 'Frequency';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  end_time: Scalars['Time']['output'];
  exact_times?: Maybe<Scalars['Int']['output']>;
  headway_secs: Scalars['Int']['output'];
  is_active?: Maybe<Scalars['Boolean']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  start_time: Scalars['Time']['output'];
  trip?: Maybe<Trip>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type FrequencyEntityResponseCollection = {
  __typename?: 'FrequencyEntityResponseCollection';
  nodes: Array<Frequency>;
  pageInfo: Pagination;
};

export type FrequencyFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<FrequencyFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  end_time?: InputMaybe<TimeFilterInput>;
  exact_times?: InputMaybe<IntFilterInput>;
  headway_secs?: InputMaybe<IntFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  not?: InputMaybe<FrequencyFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<FrequencyFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  start_time?: InputMaybe<TimeFilterInput>;
  trip?: InputMaybe<TripFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type FrequencyInput = {
  end_time?: InputMaybe<Scalars['Time']['input']>;
  exact_times?: InputMaybe<Scalars['Int']['input']>;
  headway_secs?: InputMaybe<Scalars['Int']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  start_time?: InputMaybe<Scalars['Time']['input']>;
  trip?: InputMaybe<Scalars['ID']['input']>;
};

export type FrequencyRelationResponseCollection = {
  __typename?: 'FrequencyRelationResponseCollection';
  nodes: Array<Frequency>;
};

export type GenericMorph = ActivePassenger | AdminLevel | Agency | Block | Building | CalendarDate | ComponentSpawningBuildingWeight | ComponentSpawningDayMultiplier | ComponentSpawningDistributionParams | ComponentSpawningHourlyPattern | ComponentSpawningLanduseWeight | ComponentSpawningPoiWeight | Country | Depot | Driver | FareAttribute | FareRule | FeedInfo | Frequency | Geofence | GeofenceGeometry | GeometryPoint | GpsDevice | Highway | HighwayShape | I18NLocale | LanduseShape | LanduseZone | OperationalConfiguration | Place | Poi | PoiShape | Region | RegionShape | ReviewWorkflowsWorkflow | ReviewWorkflowsWorkflowStage | Route | RouteDepot | RouteShape | Service | Shape | SpawnConfig | Stop | StopTime | Transfer | Trip | UploadFile | UsersPermissionsPermission | UsersPermissionsRole | UsersPermissionsUser | Vehicle | VehicleEvent | VehicleStatus;

export type Geofence = {
  __typename?: 'Geofence';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  enabled: Scalars['Boolean']['output'];
  geofence_geometries: Array<Maybe<GeofenceGeometry>>;
  geofence_geometries_connection?: Maybe<GeofenceGeometryRelationResponseCollection>;
  geofence_id: Scalars['String']['output'];
  metadata?: Maybe<Scalars['JSON']['output']>;
  name: Scalars['String']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  type: Enum_Geofence_Type;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  valid_from?: Maybe<Scalars['DateTime']['output']>;
  valid_to?: Maybe<Scalars['DateTime']['output']>;
};


export type GeofenceGeofence_GeometriesArgs = {
  filters?: InputMaybe<GeofenceGeometryFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type GeofenceGeofence_Geometries_ConnectionArgs = {
  filters?: InputMaybe<GeofenceGeometryFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type GeofenceEntityResponseCollection = {
  __typename?: 'GeofenceEntityResponseCollection';
  nodes: Array<Geofence>;
  pageInfo: Pagination;
};

export type GeofenceFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<GeofenceFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  enabled?: InputMaybe<BooleanFilterInput>;
  geofence_geometries?: InputMaybe<GeofenceGeometryFiltersInput>;
  geofence_id?: InputMaybe<StringFilterInput>;
  metadata?: InputMaybe<JsonFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<GeofenceFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<GeofenceFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  type?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  valid_from?: InputMaybe<DateTimeFilterInput>;
  valid_to?: InputMaybe<DateTimeFilterInput>;
};

export type GeofenceGeometry = {
  __typename?: 'GeofenceGeometry';
  buffer_meters?: Maybe<Scalars['Float']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  geofence?: Maybe<Geofence>;
  geometry_id: Scalars['String']['output'];
  geometry_type: Enum_Geofencegeometry_Geometry_Type;
  is_primary?: Maybe<Scalars['Boolean']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type GeofenceGeometryEntityResponseCollection = {
  __typename?: 'GeofenceGeometryEntityResponseCollection';
  nodes: Array<GeofenceGeometry>;
  pageInfo: Pagination;
};

export type GeofenceGeometryFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<GeofenceGeometryFiltersInput>>>;
  buffer_meters?: InputMaybe<FloatFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  geofence?: InputMaybe<GeofenceFiltersInput>;
  geometry_id?: InputMaybe<StringFilterInput>;
  geometry_type?: InputMaybe<StringFilterInput>;
  is_primary?: InputMaybe<BooleanFilterInput>;
  not?: InputMaybe<GeofenceGeometryFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<GeofenceGeometryFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type GeofenceGeometryInput = {
  buffer_meters?: InputMaybe<Scalars['Float']['input']>;
  geofence?: InputMaybe<Scalars['ID']['input']>;
  geometry_id?: InputMaybe<Scalars['String']['input']>;
  geometry_type?: InputMaybe<Enum_Geofencegeometry_Geometry_Type>;
  is_primary?: InputMaybe<Scalars['Boolean']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
};

export type GeofenceGeometryRelationResponseCollection = {
  __typename?: 'GeofenceGeometryRelationResponseCollection';
  nodes: Array<GeofenceGeometry>;
};

export type GeofenceInput = {
  enabled?: InputMaybe<Scalars['Boolean']['input']>;
  geofence_geometries?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  geofence_id?: InputMaybe<Scalars['String']['input']>;
  metadata?: InputMaybe<Scalars['JSON']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  type?: InputMaybe<Enum_Geofence_Type>;
  valid_from?: InputMaybe<Scalars['DateTime']['input']>;
  valid_to?: InputMaybe<Scalars['DateTime']['input']>;
};

export type GeometryPoint = {
  __typename?: 'GeometryPoint';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  geometry_id: Scalars['String']['output'];
  is_active: Scalars['Boolean']['output'];
  point_elevation?: Maybe<Scalars['Float']['output']>;
  point_lat: Scalars['Float']['output'];
  point_lon: Scalars['Float']['output'];
  point_sequence: Scalars['Int']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type GeometryPointEntityResponseCollection = {
  __typename?: 'GeometryPointEntityResponseCollection';
  nodes: Array<GeometryPoint>;
  pageInfo: Pagination;
};

export type GeometryPointFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<GeometryPointFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  geometry_id?: InputMaybe<StringFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  not?: InputMaybe<GeometryPointFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<GeometryPointFiltersInput>>>;
  point_elevation?: InputMaybe<FloatFilterInput>;
  point_lat?: InputMaybe<FloatFilterInput>;
  point_lon?: InputMaybe<FloatFilterInput>;
  point_sequence?: InputMaybe<IntFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type GeometryPointInput = {
  geometry_id?: InputMaybe<Scalars['String']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  point_elevation?: InputMaybe<Scalars['Float']['input']>;
  point_lat?: InputMaybe<Scalars['Float']['input']>;
  point_lon?: InputMaybe<Scalars['Float']['input']>;
  point_sequence?: InputMaybe<Scalars['Int']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
};

export type GpsDevice = {
  __typename?: 'GpsDevice';
  assigned_vehicle?: Maybe<Vehicle>;
  battery_level?: Maybe<Scalars['Int']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  device_id: Scalars['String']['output'];
  device_serial: Scalars['String']['output'];
  device_type?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  firmware_version?: Maybe<Scalars['String']['output']>;
  installation_date?: Maybe<Scalars['DateTime']['output']>;
  is_active: Scalars['Boolean']['output'];
  last_seen?: Maybe<Scalars['DateTime']['output']>;
  manufacturer?: Maybe<Scalars['String']['output']>;
  model?: Maybe<Scalars['String']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  signal_strength?: Maybe<Scalars['Int']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type GpsDeviceEntityResponseCollection = {
  __typename?: 'GpsDeviceEntityResponseCollection';
  nodes: Array<GpsDevice>;
  pageInfo: Pagination;
};

export type GpsDeviceFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<GpsDeviceFiltersInput>>>;
  assigned_vehicle?: InputMaybe<VehicleFiltersInput>;
  battery_level?: InputMaybe<IntFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  device_id?: InputMaybe<StringFilterInput>;
  device_serial?: InputMaybe<StringFilterInput>;
  device_type?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  firmware_version?: InputMaybe<StringFilterInput>;
  installation_date?: InputMaybe<DateTimeFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  last_seen?: InputMaybe<DateTimeFilterInput>;
  manufacturer?: InputMaybe<StringFilterInput>;
  model?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<GpsDeviceFiltersInput>;
  notes?: InputMaybe<StringFilterInput>;
  or?: InputMaybe<Array<InputMaybe<GpsDeviceFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  signal_strength?: InputMaybe<IntFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type GpsDeviceInput = {
  assigned_vehicle?: InputMaybe<Scalars['ID']['input']>;
  battery_level?: InputMaybe<Scalars['Int']['input']>;
  device_id?: InputMaybe<Scalars['String']['input']>;
  device_serial?: InputMaybe<Scalars['String']['input']>;
  device_type?: InputMaybe<Scalars['String']['input']>;
  firmware_version?: InputMaybe<Scalars['String']['input']>;
  installation_date?: InputMaybe<Scalars['DateTime']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  last_seen?: InputMaybe<Scalars['DateTime']['input']>;
  manufacturer?: InputMaybe<Scalars['String']['input']>;
  model?: InputMaybe<Scalars['String']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  signal_strength?: InputMaybe<Scalars['Int']['input']>;
};

export type Highway = {
  __typename?: 'Highway';
  country?: Maybe<Country>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  full_id?: Maybe<Scalars['String']['output']>;
  highway_id: Scalars['String']['output'];
  highway_shapes: Array<Maybe<HighwayShape>>;
  highway_shapes_connection?: Maybe<HighwayShapeRelationResponseCollection>;
  highway_type?: Maybe<Enum_Highway_Highway_Type>;
  is_active: Scalars['Boolean']['output'];
  lanes?: Maybe<Scalars['Int']['output']>;
  maxspeed?: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  oneway?: Maybe<Scalars['Boolean']['output']>;
  osm_id?: Maybe<Scalars['String']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  ref?: Maybe<Scalars['String']['output']>;
  region?: Maybe<Region>;
  surface?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};


export type HighwayHighway_ShapesArgs = {
  filters?: InputMaybe<HighwayShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type HighwayHighway_Shapes_ConnectionArgs = {
  filters?: InputMaybe<HighwayShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type HighwayEntityResponseCollection = {
  __typename?: 'HighwayEntityResponseCollection';
  nodes: Array<Highway>;
  pageInfo: Pagination;
};

export type HighwayFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<HighwayFiltersInput>>>;
  country?: InputMaybe<CountryFiltersInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  full_id?: InputMaybe<StringFilterInput>;
  highway_id?: InputMaybe<StringFilterInput>;
  highway_shapes?: InputMaybe<HighwayShapeFiltersInput>;
  highway_type?: InputMaybe<StringFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  lanes?: InputMaybe<IntFilterInput>;
  maxspeed?: InputMaybe<StringFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<HighwayFiltersInput>;
  oneway?: InputMaybe<BooleanFilterInput>;
  or?: InputMaybe<Array<InputMaybe<HighwayFiltersInput>>>;
  osm_id?: InputMaybe<StringFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  ref?: InputMaybe<StringFilterInput>;
  region?: InputMaybe<RegionFiltersInput>;
  surface?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type HighwayInput = {
  country?: InputMaybe<Scalars['ID']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  full_id?: InputMaybe<Scalars['String']['input']>;
  highway_id?: InputMaybe<Scalars['String']['input']>;
  highway_shapes?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  highway_type?: InputMaybe<Enum_Highway_Highway_Type>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  lanes?: InputMaybe<Scalars['Int']['input']>;
  maxspeed?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  oneway?: InputMaybe<Scalars['Boolean']['input']>;
  osm_id?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  ref?: InputMaybe<Scalars['String']['input']>;
  region?: InputMaybe<Scalars['ID']['input']>;
  surface?: InputMaybe<Scalars['String']['input']>;
};

export type HighwayRelationResponseCollection = {
  __typename?: 'HighwayRelationResponseCollection';
  nodes: Array<Highway>;
};

export type HighwayShape = {
  __typename?: 'HighwayShape';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  highway?: Maybe<Highway>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  shape_pt_lat: Scalars['Float']['output'];
  shape_pt_lon: Scalars['Float']['output'];
  shape_pt_sequence: Scalars['Int']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type HighwayShapeEntityResponseCollection = {
  __typename?: 'HighwayShapeEntityResponseCollection';
  nodes: Array<HighwayShape>;
  pageInfo: Pagination;
};

export type HighwayShapeFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<HighwayShapeFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  highway?: InputMaybe<HighwayFiltersInput>;
  not?: InputMaybe<HighwayShapeFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<HighwayShapeFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  shape_pt_lat?: InputMaybe<FloatFilterInput>;
  shape_pt_lon?: InputMaybe<FloatFilterInput>;
  shape_pt_sequence?: InputMaybe<IntFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type HighwayShapeInput = {
  highway?: InputMaybe<Scalars['ID']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  shape_pt_lat?: InputMaybe<Scalars['Float']['input']>;
  shape_pt_lon?: InputMaybe<Scalars['Float']['input']>;
  shape_pt_sequence?: InputMaybe<Scalars['Int']['input']>;
};

export type HighwayShapeRelationResponseCollection = {
  __typename?: 'HighwayShapeRelationResponseCollection';
  nodes: Array<HighwayShape>;
};

export type I18NLocale = {
  __typename?: 'I18NLocale';
  code?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  name?: Maybe<Scalars['String']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type I18NLocaleEntityResponseCollection = {
  __typename?: 'I18NLocaleEntityResponseCollection';
  nodes: Array<I18NLocale>;
  pageInfo: Pagination;
};

export type I18NLocaleFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<I18NLocaleFiltersInput>>>;
  code?: InputMaybe<StringFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<I18NLocaleFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<I18NLocaleFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type IdFilterInput = {
  and?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  between?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  contains?: InputMaybe<Scalars['ID']['input']>;
  containsi?: InputMaybe<Scalars['ID']['input']>;
  endsWith?: InputMaybe<Scalars['ID']['input']>;
  eq?: InputMaybe<Scalars['ID']['input']>;
  eqi?: InputMaybe<Scalars['ID']['input']>;
  gt?: InputMaybe<Scalars['ID']['input']>;
  gte?: InputMaybe<Scalars['ID']['input']>;
  in?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  lt?: InputMaybe<Scalars['ID']['input']>;
  lte?: InputMaybe<Scalars['ID']['input']>;
  ne?: InputMaybe<Scalars['ID']['input']>;
  nei?: InputMaybe<Scalars['ID']['input']>;
  not?: InputMaybe<IdFilterInput>;
  notContains?: InputMaybe<Scalars['ID']['input']>;
  notContainsi?: InputMaybe<Scalars['ID']['input']>;
  notIn?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  notNull?: InputMaybe<Scalars['Boolean']['input']>;
  null?: InputMaybe<Scalars['Boolean']['input']>;
  or?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  startsWith?: InputMaybe<Scalars['ID']['input']>;
};

export type IntFilterInput = {
  and?: InputMaybe<Array<InputMaybe<Scalars['Int']['input']>>>;
  between?: InputMaybe<Array<InputMaybe<Scalars['Int']['input']>>>;
  contains?: InputMaybe<Scalars['Int']['input']>;
  containsi?: InputMaybe<Scalars['Int']['input']>;
  endsWith?: InputMaybe<Scalars['Int']['input']>;
  eq?: InputMaybe<Scalars['Int']['input']>;
  eqi?: InputMaybe<Scalars['Int']['input']>;
  gt?: InputMaybe<Scalars['Int']['input']>;
  gte?: InputMaybe<Scalars['Int']['input']>;
  in?: InputMaybe<Array<InputMaybe<Scalars['Int']['input']>>>;
  lt?: InputMaybe<Scalars['Int']['input']>;
  lte?: InputMaybe<Scalars['Int']['input']>;
  ne?: InputMaybe<Scalars['Int']['input']>;
  nei?: InputMaybe<Scalars['Int']['input']>;
  not?: InputMaybe<IntFilterInput>;
  notContains?: InputMaybe<Scalars['Int']['input']>;
  notContainsi?: InputMaybe<Scalars['Int']['input']>;
  notIn?: InputMaybe<Array<InputMaybe<Scalars['Int']['input']>>>;
  notNull?: InputMaybe<Scalars['Boolean']['input']>;
  null?: InputMaybe<Scalars['Boolean']['input']>;
  or?: InputMaybe<Array<InputMaybe<Scalars['Int']['input']>>>;
  startsWith?: InputMaybe<Scalars['Int']['input']>;
};

export type JsonFilterInput = {
  and?: InputMaybe<Array<InputMaybe<Scalars['JSON']['input']>>>;
  between?: InputMaybe<Array<InputMaybe<Scalars['JSON']['input']>>>;
  contains?: InputMaybe<Scalars['JSON']['input']>;
  containsi?: InputMaybe<Scalars['JSON']['input']>;
  endsWith?: InputMaybe<Scalars['JSON']['input']>;
  eq?: InputMaybe<Scalars['JSON']['input']>;
  eqi?: InputMaybe<Scalars['JSON']['input']>;
  gt?: InputMaybe<Scalars['JSON']['input']>;
  gte?: InputMaybe<Scalars['JSON']['input']>;
  in?: InputMaybe<Array<InputMaybe<Scalars['JSON']['input']>>>;
  lt?: InputMaybe<Scalars['JSON']['input']>;
  lte?: InputMaybe<Scalars['JSON']['input']>;
  ne?: InputMaybe<Scalars['JSON']['input']>;
  nei?: InputMaybe<Scalars['JSON']['input']>;
  not?: InputMaybe<JsonFilterInput>;
  notContains?: InputMaybe<Scalars['JSON']['input']>;
  notContainsi?: InputMaybe<Scalars['JSON']['input']>;
  notIn?: InputMaybe<Array<InputMaybe<Scalars['JSON']['input']>>>;
  notNull?: InputMaybe<Scalars['Boolean']['input']>;
  null?: InputMaybe<Scalars['Boolean']['input']>;
  or?: InputMaybe<Array<InputMaybe<Scalars['JSON']['input']>>>;
  startsWith?: InputMaybe<Scalars['JSON']['input']>;
};

export type LanduseShape = {
  __typename?: 'LanduseShape';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  landuse_zone?: Maybe<LanduseZone>;
  polygon_index?: Maybe<Scalars['Int']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  ring_index?: Maybe<Scalars['Int']['output']>;
  shape_pt_lat: Scalars['Float']['output'];
  shape_pt_lon: Scalars['Float']['output'];
  shape_pt_sequence: Scalars['Int']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type LanduseShapeEntityResponseCollection = {
  __typename?: 'LanduseShapeEntityResponseCollection';
  nodes: Array<LanduseShape>;
  pageInfo: Pagination;
};

export type LanduseShapeFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<LanduseShapeFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  landuse_zone?: InputMaybe<LanduseZoneFiltersInput>;
  not?: InputMaybe<LanduseShapeFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<LanduseShapeFiltersInput>>>;
  polygon_index?: InputMaybe<IntFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  ring_index?: InputMaybe<IntFilterInput>;
  shape_pt_lat?: InputMaybe<FloatFilterInput>;
  shape_pt_lon?: InputMaybe<FloatFilterInput>;
  shape_pt_sequence?: InputMaybe<IntFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type LanduseShapeInput = {
  landuse_zone?: InputMaybe<Scalars['ID']['input']>;
  polygon_index?: InputMaybe<Scalars['Int']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  ring_index?: InputMaybe<Scalars['Int']['input']>;
  shape_pt_lat?: InputMaybe<Scalars['Float']['input']>;
  shape_pt_lon?: InputMaybe<Scalars['Float']['input']>;
  shape_pt_sequence?: InputMaybe<Scalars['Int']['input']>;
};

export type LanduseShapeRelationResponseCollection = {
  __typename?: 'LanduseShapeRelationResponseCollection';
  nodes: Array<LanduseShape>;
};

export type LanduseZone = {
  __typename?: 'LanduseZone';
  area_sq_km?: Maybe<Scalars['Float']['output']>;
  center_latitude?: Maybe<Scalars['Float']['output']>;
  center_longitude?: Maybe<Scalars['Float']['output']>;
  country?: Maybe<Country>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  geometry_geojson: Scalars['JSON']['output'];
  is_active: Scalars['Boolean']['output'];
  landuse_shapes: Array<Maybe<LanduseShape>>;
  landuse_shapes_connection?: Maybe<LanduseShapeRelationResponseCollection>;
  name?: Maybe<Scalars['String']['output']>;
  off_peak_multiplier?: Maybe<Scalars['Float']['output']>;
  osm_id?: Maybe<Scalars['String']['output']>;
  peak_hour_multiplier?: Maybe<Scalars['Float']['output']>;
  population_density?: Maybe<Scalars['Float']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  region?: Maybe<Region>;
  spawn_weight?: Maybe<Scalars['Float']['output']>;
  tags?: Maybe<Scalars['JSON']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  zone_type: Enum_Landusezone_Zone_Type;
};


export type LanduseZoneLanduse_ShapesArgs = {
  filters?: InputMaybe<LanduseShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type LanduseZoneLanduse_Shapes_ConnectionArgs = {
  filters?: InputMaybe<LanduseShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type LanduseZoneEntityResponseCollection = {
  __typename?: 'LanduseZoneEntityResponseCollection';
  nodes: Array<LanduseZone>;
  pageInfo: Pagination;
};

export type LanduseZoneFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<LanduseZoneFiltersInput>>>;
  area_sq_km?: InputMaybe<FloatFilterInput>;
  center_latitude?: InputMaybe<FloatFilterInput>;
  center_longitude?: InputMaybe<FloatFilterInput>;
  country?: InputMaybe<CountryFiltersInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  geometry_geojson?: InputMaybe<JsonFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  landuse_shapes?: InputMaybe<LanduseShapeFiltersInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<LanduseZoneFiltersInput>;
  off_peak_multiplier?: InputMaybe<FloatFilterInput>;
  or?: InputMaybe<Array<InputMaybe<LanduseZoneFiltersInput>>>;
  osm_id?: InputMaybe<StringFilterInput>;
  peak_hour_multiplier?: InputMaybe<FloatFilterInput>;
  population_density?: InputMaybe<FloatFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  region?: InputMaybe<RegionFiltersInput>;
  spawn_weight?: InputMaybe<FloatFilterInput>;
  tags?: InputMaybe<JsonFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  zone_type?: InputMaybe<StringFilterInput>;
};

export type LanduseZoneInput = {
  area_sq_km?: InputMaybe<Scalars['Float']['input']>;
  center_latitude?: InputMaybe<Scalars['Float']['input']>;
  center_longitude?: InputMaybe<Scalars['Float']['input']>;
  country?: InputMaybe<Scalars['ID']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  geometry_geojson?: InputMaybe<Scalars['JSON']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  landuse_shapes?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  name?: InputMaybe<Scalars['String']['input']>;
  off_peak_multiplier?: InputMaybe<Scalars['Float']['input']>;
  osm_id?: InputMaybe<Scalars['String']['input']>;
  peak_hour_multiplier?: InputMaybe<Scalars['Float']['input']>;
  population_density?: InputMaybe<Scalars['Float']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  region?: InputMaybe<Scalars['ID']['input']>;
  spawn_weight?: InputMaybe<Scalars['Float']['input']>;
  tags?: InputMaybe<Scalars['JSON']['input']>;
  zone_type?: InputMaybe<Enum_Landusezone_Zone_Type>;
};

export type LanduseZoneRelationResponseCollection = {
  __typename?: 'LanduseZoneRelationResponseCollection';
  nodes: Array<LanduseZone>;
};

export type LongFilterInput = {
  and?: InputMaybe<Array<InputMaybe<Scalars['Long']['input']>>>;
  between?: InputMaybe<Array<InputMaybe<Scalars['Long']['input']>>>;
  contains?: InputMaybe<Scalars['Long']['input']>;
  containsi?: InputMaybe<Scalars['Long']['input']>;
  endsWith?: InputMaybe<Scalars['Long']['input']>;
  eq?: InputMaybe<Scalars['Long']['input']>;
  eqi?: InputMaybe<Scalars['Long']['input']>;
  gt?: InputMaybe<Scalars['Long']['input']>;
  gte?: InputMaybe<Scalars['Long']['input']>;
  in?: InputMaybe<Array<InputMaybe<Scalars['Long']['input']>>>;
  lt?: InputMaybe<Scalars['Long']['input']>;
  lte?: InputMaybe<Scalars['Long']['input']>;
  ne?: InputMaybe<Scalars['Long']['input']>;
  nei?: InputMaybe<Scalars['Long']['input']>;
  not?: InputMaybe<LongFilterInput>;
  notContains?: InputMaybe<Scalars['Long']['input']>;
  notContainsi?: InputMaybe<Scalars['Long']['input']>;
  notIn?: InputMaybe<Array<InputMaybe<Scalars['Long']['input']>>>;
  notNull?: InputMaybe<Scalars['Boolean']['input']>;
  null?: InputMaybe<Scalars['Boolean']['input']>;
  or?: InputMaybe<Array<InputMaybe<Scalars['Long']['input']>>>;
  startsWith?: InputMaybe<Scalars['Long']['input']>;
};

export type Mutation = {
  __typename?: 'Mutation';
  /** Change user password. Confirm with the current password. */
  changePassword?: Maybe<UsersPermissionsLoginPayload>;
  createActivePassenger?: Maybe<ActivePassenger>;
  createAdminLevel?: Maybe<AdminLevel>;
  createAgency?: Maybe<Agency>;
  createBlock?: Maybe<Block>;
  createBuilding?: Maybe<Building>;
  createCalendarDate?: Maybe<CalendarDate>;
  createCountry?: Maybe<Country>;
  createDepot?: Maybe<Depot>;
  createDriver?: Maybe<Driver>;
  createFareAttribute?: Maybe<FareAttribute>;
  createFareRule?: Maybe<FareRule>;
  createFeedInfo?: Maybe<FeedInfo>;
  createFrequency?: Maybe<Frequency>;
  createGeofence?: Maybe<Geofence>;
  createGeofenceGeometry?: Maybe<GeofenceGeometry>;
  createGeometryPoint?: Maybe<GeometryPoint>;
  createGpsDevice?: Maybe<GpsDevice>;
  createHighway?: Maybe<Highway>;
  createHighwayShape?: Maybe<HighwayShape>;
  createLanduseShape?: Maybe<LanduseShape>;
  createLanduseZone?: Maybe<LanduseZone>;
  createOperationalConfiguration?: Maybe<OperationalConfiguration>;
  createPlace?: Maybe<Place>;
  createPoi?: Maybe<Poi>;
  createPoiShape?: Maybe<PoiShape>;
  createRegion?: Maybe<Region>;
  createRegionShape?: Maybe<RegionShape>;
  createReviewWorkflowsWorkflow?: Maybe<ReviewWorkflowsWorkflow>;
  createReviewWorkflowsWorkflowStage?: Maybe<ReviewWorkflowsWorkflowStage>;
  createRoute?: Maybe<Route>;
  createRouteDepot?: Maybe<RouteDepot>;
  createRouteShape?: Maybe<RouteShape>;
  createService?: Maybe<Service>;
  createShape?: Maybe<Shape>;
  createSpawnConfig?: Maybe<SpawnConfig>;
  createStop?: Maybe<Stop>;
  createStopTime?: Maybe<StopTime>;
  createTransfer?: Maybe<Transfer>;
  createTrip?: Maybe<Trip>;
  /** Create a new role */
  createUsersPermissionsRole?: Maybe<UsersPermissionsCreateRolePayload>;
  /** Create a new user */
  createUsersPermissionsUser: UsersPermissionsUserEntityResponse;
  createVehicle?: Maybe<Vehicle>;
  createVehicleEvent?: Maybe<VehicleEvent>;
  createVehicleStatus?: Maybe<VehicleStatus>;
  deleteActivePassenger?: Maybe<DeleteMutationResponse>;
  deleteAdminLevel?: Maybe<DeleteMutationResponse>;
  deleteAgency?: Maybe<DeleteMutationResponse>;
  deleteBlock?: Maybe<DeleteMutationResponse>;
  deleteBuilding?: Maybe<DeleteMutationResponse>;
  deleteCalendarDate?: Maybe<DeleteMutationResponse>;
  deleteCountry?: Maybe<DeleteMutationResponse>;
  deleteDepot?: Maybe<DeleteMutationResponse>;
  deleteDriver?: Maybe<DeleteMutationResponse>;
  deleteFareAttribute?: Maybe<DeleteMutationResponse>;
  deleteFareRule?: Maybe<DeleteMutationResponse>;
  deleteFeedInfo?: Maybe<DeleteMutationResponse>;
  deleteFrequency?: Maybe<DeleteMutationResponse>;
  deleteGeofence?: Maybe<DeleteMutationResponse>;
  deleteGeofenceGeometry?: Maybe<DeleteMutationResponse>;
  deleteGeometryPoint?: Maybe<DeleteMutationResponse>;
  deleteGpsDevice?: Maybe<DeleteMutationResponse>;
  deleteHighway?: Maybe<DeleteMutationResponse>;
  deleteHighwayShape?: Maybe<DeleteMutationResponse>;
  deleteLanduseShape?: Maybe<DeleteMutationResponse>;
  deleteLanduseZone?: Maybe<DeleteMutationResponse>;
  deleteOperationalConfiguration?: Maybe<DeleteMutationResponse>;
  deletePlace?: Maybe<DeleteMutationResponse>;
  deletePoi?: Maybe<DeleteMutationResponse>;
  deletePoiShape?: Maybe<DeleteMutationResponse>;
  deleteRegion?: Maybe<DeleteMutationResponse>;
  deleteRegionShape?: Maybe<DeleteMutationResponse>;
  deleteReviewWorkflowsWorkflow?: Maybe<DeleteMutationResponse>;
  deleteReviewWorkflowsWorkflowStage?: Maybe<DeleteMutationResponse>;
  deleteRoute?: Maybe<DeleteMutationResponse>;
  deleteRouteDepot?: Maybe<DeleteMutationResponse>;
  deleteRouteShape?: Maybe<DeleteMutationResponse>;
  deleteService?: Maybe<DeleteMutationResponse>;
  deleteShape?: Maybe<DeleteMutationResponse>;
  deleteSpawnConfig?: Maybe<DeleteMutationResponse>;
  deleteStop?: Maybe<DeleteMutationResponse>;
  deleteStopTime?: Maybe<DeleteMutationResponse>;
  deleteTransfer?: Maybe<DeleteMutationResponse>;
  deleteTrip?: Maybe<DeleteMutationResponse>;
  deleteUploadFile?: Maybe<UploadFile>;
  /** Delete an existing role */
  deleteUsersPermissionsRole?: Maybe<UsersPermissionsDeleteRolePayload>;
  /** Delete an existing user */
  deleteUsersPermissionsUser: UsersPermissionsUserEntityResponse;
  deleteVehicle?: Maybe<DeleteMutationResponse>;
  deleteVehicleEvent?: Maybe<DeleteMutationResponse>;
  deleteVehicleStatus?: Maybe<DeleteMutationResponse>;
  /** Confirm an email users email address */
  emailConfirmation?: Maybe<UsersPermissionsLoginPayload>;
  /** Request a reset password token */
  forgotPassword?: Maybe<UsersPermissionsPasswordPayload>;
  login: UsersPermissionsLoginPayload;
  /** Register a user */
  register: UsersPermissionsLoginPayload;
  /** Reset user password. Confirm with a code (resetToken from forgotPassword) */
  resetPassword?: Maybe<UsersPermissionsLoginPayload>;
  updateActivePassenger?: Maybe<ActivePassenger>;
  updateAdminLevel?: Maybe<AdminLevel>;
  updateAgency?: Maybe<Agency>;
  updateBlock?: Maybe<Block>;
  updateBuilding?: Maybe<Building>;
  updateCalendarDate?: Maybe<CalendarDate>;
  updateCountry?: Maybe<Country>;
  updateDepot?: Maybe<Depot>;
  updateDriver?: Maybe<Driver>;
  updateFareAttribute?: Maybe<FareAttribute>;
  updateFareRule?: Maybe<FareRule>;
  updateFeedInfo?: Maybe<FeedInfo>;
  updateFrequency?: Maybe<Frequency>;
  updateGeofence?: Maybe<Geofence>;
  updateGeofenceGeometry?: Maybe<GeofenceGeometry>;
  updateGeometryPoint?: Maybe<GeometryPoint>;
  updateGpsDevice?: Maybe<GpsDevice>;
  updateHighway?: Maybe<Highway>;
  updateHighwayShape?: Maybe<HighwayShape>;
  updateLanduseShape?: Maybe<LanduseShape>;
  updateLanduseZone?: Maybe<LanduseZone>;
  updateOperationalConfiguration?: Maybe<OperationalConfiguration>;
  updatePlace?: Maybe<Place>;
  updatePoi?: Maybe<Poi>;
  updatePoiShape?: Maybe<PoiShape>;
  updateRegion?: Maybe<Region>;
  updateRegionShape?: Maybe<RegionShape>;
  updateReviewWorkflowsWorkflow?: Maybe<ReviewWorkflowsWorkflow>;
  updateReviewWorkflowsWorkflowStage?: Maybe<ReviewWorkflowsWorkflowStage>;
  updateRoute?: Maybe<Route>;
  updateRouteDepot?: Maybe<RouteDepot>;
  updateRouteShape?: Maybe<RouteShape>;
  updateService?: Maybe<Service>;
  updateShape?: Maybe<Shape>;
  updateSpawnConfig?: Maybe<SpawnConfig>;
  updateStop?: Maybe<Stop>;
  updateStopTime?: Maybe<StopTime>;
  updateTransfer?: Maybe<Transfer>;
  updateTrip?: Maybe<Trip>;
  updateUploadFile: UploadFile;
  /** Update an existing role */
  updateUsersPermissionsRole?: Maybe<UsersPermissionsUpdateRolePayload>;
  /** Update an existing user */
  updateUsersPermissionsUser: UsersPermissionsUserEntityResponse;
  updateVehicle?: Maybe<Vehicle>;
  updateVehicleEvent?: Maybe<VehicleEvent>;
  updateVehicleStatus?: Maybe<VehicleStatus>;
};


export type MutationChangePasswordArgs = {
  currentPassword: Scalars['String']['input'];
  password: Scalars['String']['input'];
  passwordConfirmation: Scalars['String']['input'];
};


export type MutationCreateActivePassengerArgs = {
  data: ActivePassengerInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateAdminLevelArgs = {
  data: AdminLevelInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateAgencyArgs = {
  data: AgencyInput;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateBlockArgs = {
  data: BlockInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateBuildingArgs = {
  data: BuildingInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateCalendarDateArgs = {
  data: CalendarDateInput;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateCountryArgs = {
  data: CountryInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateDepotArgs = {
  data: DepotInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateDriverArgs = {
  data: DriverInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateFareAttributeArgs = {
  data: FareAttributeInput;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateFareRuleArgs = {
  data: FareRuleInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateFeedInfoArgs = {
  data: FeedInfoInput;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateFrequencyArgs = {
  data: FrequencyInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateGeofenceArgs = {
  data: GeofenceInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateGeofenceGeometryArgs = {
  data: GeofenceGeometryInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateGeometryPointArgs = {
  data: GeometryPointInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateGpsDeviceArgs = {
  data: GpsDeviceInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateHighwayArgs = {
  data: HighwayInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateHighwayShapeArgs = {
  data: HighwayShapeInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateLanduseShapeArgs = {
  data: LanduseShapeInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateLanduseZoneArgs = {
  data: LanduseZoneInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateOperationalConfigurationArgs = {
  data: OperationalConfigurationInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreatePlaceArgs = {
  data: PlaceInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreatePoiArgs = {
  data: PoiInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreatePoiShapeArgs = {
  data: PoiShapeInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateRegionArgs = {
  data: RegionInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateRegionShapeArgs = {
  data: RegionShapeInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateReviewWorkflowsWorkflowArgs = {
  data: ReviewWorkflowsWorkflowInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateReviewWorkflowsWorkflowStageArgs = {
  data: ReviewWorkflowsWorkflowStageInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateRouteArgs = {
  data: RouteInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateRouteDepotArgs = {
  data: RouteDepotInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateRouteShapeArgs = {
  data: RouteShapeInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateServiceArgs = {
  data: ServiceInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateShapeArgs = {
  data: ShapeInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateSpawnConfigArgs = {
  data: SpawnConfigInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateStopArgs = {
  data: StopInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateStopTimeArgs = {
  data: StopTimeInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateTransferArgs = {
  data: TransferInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateTripArgs = {
  data: TripInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateUsersPermissionsRoleArgs = {
  data: UsersPermissionsRoleInput;
};


export type MutationCreateUsersPermissionsUserArgs = {
  data: UsersPermissionsUserInput;
};


export type MutationCreateVehicleArgs = {
  data: VehicleInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateVehicleEventArgs = {
  data: VehicleEventInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationCreateVehicleStatusArgs = {
  data: VehicleStatusInput;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationDeleteActivePassengerArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteAdminLevelArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteAgencyArgs = {
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
};


export type MutationDeleteBlockArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteBuildingArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteCalendarDateArgs = {
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
};


export type MutationDeleteCountryArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteDepotArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteDriverArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteFareAttributeArgs = {
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
};


export type MutationDeleteFareRuleArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteFeedInfoArgs = {
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
};


export type MutationDeleteFrequencyArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteGeofenceArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteGeofenceGeometryArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteGeometryPointArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteGpsDeviceArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteHighwayArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteHighwayShapeArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteLanduseShapeArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteLanduseZoneArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteOperationalConfigurationArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeletePlaceArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeletePoiArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeletePoiShapeArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteRegionArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteRegionShapeArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteReviewWorkflowsWorkflowArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteReviewWorkflowsWorkflowStageArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteRouteArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteRouteDepotArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteRouteShapeArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteServiceArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteShapeArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteSpawnConfigArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteStopArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteStopTimeArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteTransferArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteTripArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteUploadFileArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteUsersPermissionsRoleArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteUsersPermissionsUserArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteVehicleArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteVehicleEventArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationDeleteVehicleStatusArgs = {
  documentId: Scalars['ID']['input'];
};


export type MutationEmailConfirmationArgs = {
  confirmation: Scalars['String']['input'];
};


export type MutationForgotPasswordArgs = {
  email: Scalars['String']['input'];
};


export type MutationLoginArgs = {
  input: UsersPermissionsLoginInput;
};


export type MutationRegisterArgs = {
  input: UsersPermissionsRegisterInput;
};


export type MutationResetPasswordArgs = {
  code: Scalars['String']['input'];
  password: Scalars['String']['input'];
  passwordConfirmation: Scalars['String']['input'];
};


export type MutationUpdateActivePassengerArgs = {
  data: ActivePassengerInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateAdminLevelArgs = {
  data: AdminLevelInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateAgencyArgs = {
  data: AgencyInput;
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateBlockArgs = {
  data: BlockInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateBuildingArgs = {
  data: BuildingInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateCalendarDateArgs = {
  data: CalendarDateInput;
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateCountryArgs = {
  data: CountryInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateDepotArgs = {
  data: DepotInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateDriverArgs = {
  data: DriverInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateFareAttributeArgs = {
  data: FareAttributeInput;
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateFareRuleArgs = {
  data: FareRuleInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateFeedInfoArgs = {
  data: FeedInfoInput;
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateFrequencyArgs = {
  data: FrequencyInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateGeofenceArgs = {
  data: GeofenceInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateGeofenceGeometryArgs = {
  data: GeofenceGeometryInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateGeometryPointArgs = {
  data: GeometryPointInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateGpsDeviceArgs = {
  data: GpsDeviceInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateHighwayArgs = {
  data: HighwayInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateHighwayShapeArgs = {
  data: HighwayShapeInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateLanduseShapeArgs = {
  data: LanduseShapeInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateLanduseZoneArgs = {
  data: LanduseZoneInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateOperationalConfigurationArgs = {
  data: OperationalConfigurationInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdatePlaceArgs = {
  data: PlaceInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdatePoiArgs = {
  data: PoiInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdatePoiShapeArgs = {
  data: PoiShapeInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateRegionArgs = {
  data: RegionInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateRegionShapeArgs = {
  data: RegionShapeInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateReviewWorkflowsWorkflowArgs = {
  data: ReviewWorkflowsWorkflowInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateReviewWorkflowsWorkflowStageArgs = {
  data: ReviewWorkflowsWorkflowStageInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateRouteArgs = {
  data: RouteInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateRouteDepotArgs = {
  data: RouteDepotInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateRouteShapeArgs = {
  data: RouteShapeInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateServiceArgs = {
  data: ServiceInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateShapeArgs = {
  data: ShapeInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateSpawnConfigArgs = {
  data: SpawnConfigInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateStopArgs = {
  data: StopInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateStopTimeArgs = {
  data: StopTimeInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateTransferArgs = {
  data: TransferInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateTripArgs = {
  data: TripInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateUploadFileArgs = {
  id: Scalars['ID']['input'];
  info?: InputMaybe<FileInfoInput>;
};


export type MutationUpdateUsersPermissionsRoleArgs = {
  data: UsersPermissionsRoleInput;
  id: Scalars['ID']['input'];
};


export type MutationUpdateUsersPermissionsUserArgs = {
  data: UsersPermissionsUserInput;
  id: Scalars['ID']['input'];
};


export type MutationUpdateVehicleArgs = {
  data: VehicleInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateVehicleEventArgs = {
  data: VehicleEventInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type MutationUpdateVehicleStatusArgs = {
  data: VehicleStatusInput;
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};

export type OperationalConfiguration = {
  __typename?: 'OperationalConfiguration';
  constraints?: Maybe<Scalars['JSON']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  default_value: Scalars['String']['output'];
  description?: Maybe<Scalars['String']['output']>;
  display_name?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  parameter: Scalars['String']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  requires_restart?: Maybe<Scalars['Boolean']['output']>;
  section: Scalars['String']['output'];
  ui_group?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  value: Scalars['String']['output'];
  value_type: Enum_Operationalconfiguration_Value_Type;
};

export type OperationalConfigurationEntityResponseCollection = {
  __typename?: 'OperationalConfigurationEntityResponseCollection';
  nodes: Array<OperationalConfiguration>;
  pageInfo: Pagination;
};

export type OperationalConfigurationFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<OperationalConfigurationFiltersInput>>>;
  constraints?: InputMaybe<JsonFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  default_value?: InputMaybe<StringFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  display_name?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  not?: InputMaybe<OperationalConfigurationFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<OperationalConfigurationFiltersInput>>>;
  parameter?: InputMaybe<StringFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  requires_restart?: InputMaybe<BooleanFilterInput>;
  section?: InputMaybe<StringFilterInput>;
  ui_group?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  value?: InputMaybe<StringFilterInput>;
  value_type?: InputMaybe<StringFilterInput>;
};

export type OperationalConfigurationInput = {
  constraints?: InputMaybe<Scalars['JSON']['input']>;
  default_value?: InputMaybe<Scalars['String']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  display_name?: InputMaybe<Scalars['String']['input']>;
  parameter?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  requires_restart?: InputMaybe<Scalars['Boolean']['input']>;
  section?: InputMaybe<Scalars['String']['input']>;
  ui_group?: InputMaybe<Scalars['String']['input']>;
  value?: InputMaybe<Scalars['String']['input']>;
  value_type?: InputMaybe<Enum_Operationalconfiguration_Value_Type>;
};

export type Pagination = {
  __typename?: 'Pagination';
  page: Scalars['Int']['output'];
  pageCount: Scalars['Int']['output'];
  pageSize: Scalars['Int']['output'];
  total: Scalars['Int']['output'];
};

export type PaginationArg = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  page?: InputMaybe<Scalars['Int']['input']>;
  pageSize?: InputMaybe<Scalars['Int']['input']>;
  start?: InputMaybe<Scalars['Int']['input']>;
};

export type Place = {
  __typename?: 'Place';
  area_sq_km?: Maybe<Scalars['Float']['output']>;
  center_latitude?: Maybe<Scalars['Float']['output']>;
  center_longitude?: Maybe<Scalars['Float']['output']>;
  country?: Maybe<Country>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  geometry_geojson?: Maybe<Scalars['JSON']['output']>;
  is_active: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  off_peak_multiplier?: Maybe<Scalars['Float']['output']>;
  osm_id?: Maybe<Scalars['String']['output']>;
  osm_place_rank?: Maybe<Scalars['Int']['output']>;
  peak_hour_multiplier?: Maybe<Scalars['Float']['output']>;
  place_type: Enum_Place_Place_Type;
  population?: Maybe<Scalars['Int']['output']>;
  population_density?: Maybe<Scalars['Float']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  region?: Maybe<Region>;
  spawn_weight?: Maybe<Scalars['Float']['output']>;
  tags?: Maybe<Scalars['JSON']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type PlaceEntityResponseCollection = {
  __typename?: 'PlaceEntityResponseCollection';
  nodes: Array<Place>;
  pageInfo: Pagination;
};

export type PlaceFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<PlaceFiltersInput>>>;
  area_sq_km?: InputMaybe<FloatFilterInput>;
  center_latitude?: InputMaybe<FloatFilterInput>;
  center_longitude?: InputMaybe<FloatFilterInput>;
  country?: InputMaybe<CountryFiltersInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  geometry_geojson?: InputMaybe<JsonFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<PlaceFiltersInput>;
  off_peak_multiplier?: InputMaybe<FloatFilterInput>;
  or?: InputMaybe<Array<InputMaybe<PlaceFiltersInput>>>;
  osm_id?: InputMaybe<StringFilterInput>;
  osm_place_rank?: InputMaybe<IntFilterInput>;
  peak_hour_multiplier?: InputMaybe<FloatFilterInput>;
  place_type?: InputMaybe<StringFilterInput>;
  population?: InputMaybe<IntFilterInput>;
  population_density?: InputMaybe<FloatFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  region?: InputMaybe<RegionFiltersInput>;
  spawn_weight?: InputMaybe<FloatFilterInput>;
  tags?: InputMaybe<JsonFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type PlaceInput = {
  area_sq_km?: InputMaybe<Scalars['Float']['input']>;
  center_latitude?: InputMaybe<Scalars['Float']['input']>;
  center_longitude?: InputMaybe<Scalars['Float']['input']>;
  country?: InputMaybe<Scalars['ID']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  geometry_geojson?: InputMaybe<Scalars['JSON']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  off_peak_multiplier?: InputMaybe<Scalars['Float']['input']>;
  osm_id?: InputMaybe<Scalars['String']['input']>;
  osm_place_rank?: InputMaybe<Scalars['Int']['input']>;
  peak_hour_multiplier?: InputMaybe<Scalars['Float']['input']>;
  place_type?: InputMaybe<Enum_Place_Place_Type>;
  population?: InputMaybe<Scalars['Int']['input']>;
  population_density?: InputMaybe<Scalars['Float']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  region?: InputMaybe<Scalars['ID']['input']>;
  spawn_weight?: InputMaybe<Scalars['Float']['input']>;
  tags?: InputMaybe<Scalars['JSON']['input']>;
};

export type PlaceRelationResponseCollection = {
  __typename?: 'PlaceRelationResponseCollection';
  nodes: Array<Place>;
};

export type Poi = {
  __typename?: 'Poi';
  amenity?: Maybe<Scalars['String']['output']>;
  capacity_estimate?: Maybe<Scalars['Int']['output']>;
  country?: Maybe<Country>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  is_active: Scalars['Boolean']['output'];
  latitude: Scalars['Float']['output'];
  longitude: Scalars['Float']['output'];
  name: Scalars['String']['output'];
  off_peak_multiplier?: Maybe<Scalars['Float']['output']>;
  opening_hours?: Maybe<Scalars['String']['output']>;
  osm_id?: Maybe<Scalars['String']['output']>;
  peak_hour_multiplier?: Maybe<Scalars['Float']['output']>;
  poi_shapes: Array<Maybe<PoiShape>>;
  poi_shapes_connection?: Maybe<PoiShapeRelationResponseCollection>;
  poi_type: Enum_Poi_Poi_Type;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  region?: Maybe<Region>;
  spawn_weight?: Maybe<Scalars['Float']['output']>;
  tags?: Maybe<Scalars['JSON']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};


export type PoiPoi_ShapesArgs = {
  filters?: InputMaybe<PoiShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type PoiPoi_Shapes_ConnectionArgs = {
  filters?: InputMaybe<PoiShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type PoiEntityResponseCollection = {
  __typename?: 'PoiEntityResponseCollection';
  nodes: Array<Poi>;
  pageInfo: Pagination;
};

export type PoiFiltersInput = {
  amenity?: InputMaybe<StringFilterInput>;
  and?: InputMaybe<Array<InputMaybe<PoiFiltersInput>>>;
  capacity_estimate?: InputMaybe<IntFilterInput>;
  country?: InputMaybe<CountryFiltersInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  latitude?: InputMaybe<FloatFilterInput>;
  longitude?: InputMaybe<FloatFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<PoiFiltersInput>;
  off_peak_multiplier?: InputMaybe<FloatFilterInput>;
  opening_hours?: InputMaybe<StringFilterInput>;
  or?: InputMaybe<Array<InputMaybe<PoiFiltersInput>>>;
  osm_id?: InputMaybe<StringFilterInput>;
  peak_hour_multiplier?: InputMaybe<FloatFilterInput>;
  poi_shapes?: InputMaybe<PoiShapeFiltersInput>;
  poi_type?: InputMaybe<StringFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  region?: InputMaybe<RegionFiltersInput>;
  spawn_weight?: InputMaybe<FloatFilterInput>;
  tags?: InputMaybe<JsonFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type PoiInput = {
  amenity?: InputMaybe<Scalars['String']['input']>;
  capacity_estimate?: InputMaybe<Scalars['Int']['input']>;
  country?: InputMaybe<Scalars['ID']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  latitude?: InputMaybe<Scalars['Float']['input']>;
  longitude?: InputMaybe<Scalars['Float']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  off_peak_multiplier?: InputMaybe<Scalars['Float']['input']>;
  opening_hours?: InputMaybe<Scalars['String']['input']>;
  osm_id?: InputMaybe<Scalars['String']['input']>;
  peak_hour_multiplier?: InputMaybe<Scalars['Float']['input']>;
  poi_shapes?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  poi_type?: InputMaybe<Enum_Poi_Poi_Type>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  region?: InputMaybe<Scalars['ID']['input']>;
  spawn_weight?: InputMaybe<Scalars['Float']['input']>;
  tags?: InputMaybe<Scalars['JSON']['input']>;
};

export type PoiRelationResponseCollection = {
  __typename?: 'PoiRelationResponseCollection';
  nodes: Array<Poi>;
};

export type PoiShape = {
  __typename?: 'PoiShape';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  poi?: Maybe<Poi>;
  polygon_index?: Maybe<Scalars['Int']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  ring_index?: Maybe<Scalars['Int']['output']>;
  shape_pt_lat: Scalars['Float']['output'];
  shape_pt_lon: Scalars['Float']['output'];
  shape_pt_sequence: Scalars['Int']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type PoiShapeEntityResponseCollection = {
  __typename?: 'PoiShapeEntityResponseCollection';
  nodes: Array<PoiShape>;
  pageInfo: Pagination;
};

export type PoiShapeFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<PoiShapeFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  not?: InputMaybe<PoiShapeFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<PoiShapeFiltersInput>>>;
  poi?: InputMaybe<PoiFiltersInput>;
  polygon_index?: InputMaybe<IntFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  ring_index?: InputMaybe<IntFilterInput>;
  shape_pt_lat?: InputMaybe<FloatFilterInput>;
  shape_pt_lon?: InputMaybe<FloatFilterInput>;
  shape_pt_sequence?: InputMaybe<IntFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type PoiShapeInput = {
  poi?: InputMaybe<Scalars['ID']['input']>;
  polygon_index?: InputMaybe<Scalars['Int']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  ring_index?: InputMaybe<Scalars['Int']['input']>;
  shape_pt_lat?: InputMaybe<Scalars['Float']['input']>;
  shape_pt_lon?: InputMaybe<Scalars['Float']['input']>;
  shape_pt_sequence?: InputMaybe<Scalars['Int']['input']>;
};

export type PoiShapeRelationResponseCollection = {
  __typename?: 'PoiShapeRelationResponseCollection';
  nodes: Array<PoiShape>;
};

export enum PublicationStatus {
  Draft = 'DRAFT',
  Published = 'PUBLISHED'
}

export type Query = {
  __typename?: 'Query';
  activePassenger?: Maybe<ActivePassenger>;
  activePassengers: Array<Maybe<ActivePassenger>>;
  activePassengers_connection?: Maybe<ActivePassengerEntityResponseCollection>;
  adminLevel?: Maybe<AdminLevel>;
  adminLevels: Array<Maybe<AdminLevel>>;
  adminLevels_connection?: Maybe<AdminLevelEntityResponseCollection>;
  agencies: Array<Maybe<Agency>>;
  agencies_connection?: Maybe<AgencyEntityResponseCollection>;
  agency?: Maybe<Agency>;
  block?: Maybe<Block>;
  blocks: Array<Maybe<Block>>;
  blocks_connection?: Maybe<BlockEntityResponseCollection>;
  building?: Maybe<Building>;
  buildings: Array<Maybe<Building>>;
  buildings_connection?: Maybe<BuildingEntityResponseCollection>;
  calendarDate?: Maybe<CalendarDate>;
  calendarDates: Array<Maybe<CalendarDate>>;
  calendarDates_connection?: Maybe<CalendarDateEntityResponseCollection>;
  countries: Array<Maybe<Country>>;
  countries_connection?: Maybe<CountryEntityResponseCollection>;
  country?: Maybe<Country>;
  depot?: Maybe<Depot>;
  depots: Array<Maybe<Depot>>;
  depots_connection?: Maybe<DepotEntityResponseCollection>;
  driver?: Maybe<Driver>;
  drivers: Array<Maybe<Driver>>;
  drivers_connection?: Maybe<DriverEntityResponseCollection>;
  fareAttribute?: Maybe<FareAttribute>;
  fareAttributes: Array<Maybe<FareAttribute>>;
  fareAttributes_connection?: Maybe<FareAttributeEntityResponseCollection>;
  fareRule?: Maybe<FareRule>;
  fareRules: Array<Maybe<FareRule>>;
  fareRules_connection?: Maybe<FareRuleEntityResponseCollection>;
  feedInfo?: Maybe<FeedInfo>;
  feedInfos: Array<Maybe<FeedInfo>>;
  feedInfos_connection?: Maybe<FeedInfoEntityResponseCollection>;
  frequencies: Array<Maybe<Frequency>>;
  frequencies_connection?: Maybe<FrequencyEntityResponseCollection>;
  frequency?: Maybe<Frequency>;
  geofence?: Maybe<Geofence>;
  geofenceGeometries: Array<Maybe<GeofenceGeometry>>;
  geofenceGeometries_connection?: Maybe<GeofenceGeometryEntityResponseCollection>;
  geofenceGeometry?: Maybe<GeofenceGeometry>;
  geofences: Array<Maybe<Geofence>>;
  geofences_connection?: Maybe<GeofenceEntityResponseCollection>;
  geometryPoint?: Maybe<GeometryPoint>;
  geometryPoints: Array<Maybe<GeometryPoint>>;
  geometryPoints_connection?: Maybe<GeometryPointEntityResponseCollection>;
  gpsDevice?: Maybe<GpsDevice>;
  gpsDevices: Array<Maybe<GpsDevice>>;
  gpsDevices_connection?: Maybe<GpsDeviceEntityResponseCollection>;
  highway?: Maybe<Highway>;
  highwayShape?: Maybe<HighwayShape>;
  highwayShapes: Array<Maybe<HighwayShape>>;
  highwayShapes_connection?: Maybe<HighwayShapeEntityResponseCollection>;
  highways: Array<Maybe<Highway>>;
  highways_connection?: Maybe<HighwayEntityResponseCollection>;
  i18NLocale?: Maybe<I18NLocale>;
  i18NLocales: Array<Maybe<I18NLocale>>;
  i18NLocales_connection?: Maybe<I18NLocaleEntityResponseCollection>;
  landuseShape?: Maybe<LanduseShape>;
  landuseShapes: Array<Maybe<LanduseShape>>;
  landuseShapes_connection?: Maybe<LanduseShapeEntityResponseCollection>;
  landuseZone?: Maybe<LanduseZone>;
  landuseZones: Array<Maybe<LanduseZone>>;
  landuseZones_connection?: Maybe<LanduseZoneEntityResponseCollection>;
  me?: Maybe<UsersPermissionsMe>;
  operationalConfiguration?: Maybe<OperationalConfiguration>;
  operationalConfigurations: Array<Maybe<OperationalConfiguration>>;
  operationalConfigurations_connection?: Maybe<OperationalConfigurationEntityResponseCollection>;
  place?: Maybe<Place>;
  places: Array<Maybe<Place>>;
  places_connection?: Maybe<PlaceEntityResponseCollection>;
  poi?: Maybe<Poi>;
  poiShape?: Maybe<PoiShape>;
  poiShapes: Array<Maybe<PoiShape>>;
  poiShapes_connection?: Maybe<PoiShapeEntityResponseCollection>;
  pois: Array<Maybe<Poi>>;
  pois_connection?: Maybe<PoiEntityResponseCollection>;
  region?: Maybe<Region>;
  regionShape?: Maybe<RegionShape>;
  regionShapes: Array<Maybe<RegionShape>>;
  regionShapes_connection?: Maybe<RegionShapeEntityResponseCollection>;
  regions: Array<Maybe<Region>>;
  regions_connection?: Maybe<RegionEntityResponseCollection>;
  reviewWorkflowsWorkflow?: Maybe<ReviewWorkflowsWorkflow>;
  reviewWorkflowsWorkflowStage?: Maybe<ReviewWorkflowsWorkflowStage>;
  reviewWorkflowsWorkflowStages: Array<Maybe<ReviewWorkflowsWorkflowStage>>;
  reviewWorkflowsWorkflowStages_connection?: Maybe<ReviewWorkflowsWorkflowStageEntityResponseCollection>;
  reviewWorkflowsWorkflows: Array<Maybe<ReviewWorkflowsWorkflow>>;
  reviewWorkflowsWorkflows_connection?: Maybe<ReviewWorkflowsWorkflowEntityResponseCollection>;
  route?: Maybe<Route>;
  routeDepot?: Maybe<RouteDepot>;
  routeDepots: Array<Maybe<RouteDepot>>;
  routeDepots_connection?: Maybe<RouteDepotEntityResponseCollection>;
  routeShape?: Maybe<RouteShape>;
  routeShapes: Array<Maybe<RouteShape>>;
  routeShapes_connection?: Maybe<RouteShapeEntityResponseCollection>;
  routes: Array<Maybe<Route>>;
  routes_connection?: Maybe<RouteEntityResponseCollection>;
  service?: Maybe<Service>;
  services: Array<Maybe<Service>>;
  services_connection?: Maybe<ServiceEntityResponseCollection>;
  shape?: Maybe<Shape>;
  shapes: Array<Maybe<Shape>>;
  shapes_connection?: Maybe<ShapeEntityResponseCollection>;
  spawnConfig?: Maybe<SpawnConfig>;
  spawnConfigs: Array<Maybe<SpawnConfig>>;
  spawnConfigs_connection?: Maybe<SpawnConfigEntityResponseCollection>;
  stop?: Maybe<Stop>;
  stopTime?: Maybe<StopTime>;
  stopTimes: Array<Maybe<StopTime>>;
  stopTimes_connection?: Maybe<StopTimeEntityResponseCollection>;
  stops: Array<Maybe<Stop>>;
  stops_connection?: Maybe<StopEntityResponseCollection>;
  transfer?: Maybe<Transfer>;
  transfers: Array<Maybe<Transfer>>;
  transfers_connection?: Maybe<TransferEntityResponseCollection>;
  trip?: Maybe<Trip>;
  trips: Array<Maybe<Trip>>;
  trips_connection?: Maybe<TripEntityResponseCollection>;
  uploadFile?: Maybe<UploadFile>;
  uploadFiles: Array<Maybe<UploadFile>>;
  uploadFiles_connection?: Maybe<UploadFileEntityResponseCollection>;
  usersPermissionsRole?: Maybe<UsersPermissionsRole>;
  usersPermissionsRoles: Array<Maybe<UsersPermissionsRole>>;
  usersPermissionsRoles_connection?: Maybe<UsersPermissionsRoleEntityResponseCollection>;
  usersPermissionsUser?: Maybe<UsersPermissionsUser>;
  usersPermissionsUsers: Array<Maybe<UsersPermissionsUser>>;
  usersPermissionsUsers_connection?: Maybe<UsersPermissionsUserEntityResponseCollection>;
  vehicle?: Maybe<Vehicle>;
  vehicleEvent?: Maybe<VehicleEvent>;
  vehicleEvents: Array<Maybe<VehicleEvent>>;
  vehicleEvents_connection?: Maybe<VehicleEventEntityResponseCollection>;
  vehicleStatus?: Maybe<VehicleStatus>;
  vehicleStatuses: Array<Maybe<VehicleStatus>>;
  vehicleStatuses_connection?: Maybe<VehicleStatusEntityResponseCollection>;
  vehicles: Array<Maybe<Vehicle>>;
  vehicles_connection?: Maybe<VehicleEntityResponseCollection>;
};


export type QueryActivePassengerArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryActivePassengersArgs = {
  filters?: InputMaybe<ActivePassengerFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryActivePassengers_ConnectionArgs = {
  filters?: InputMaybe<ActivePassengerFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryAdminLevelArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryAdminLevelsArgs = {
  filters?: InputMaybe<AdminLevelFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryAdminLevels_ConnectionArgs = {
  filters?: InputMaybe<AdminLevelFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryAgenciesArgs = {
  filters?: InputMaybe<AgencyFiltersInput>;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryAgencies_ConnectionArgs = {
  filters?: InputMaybe<AgencyFiltersInput>;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryAgencyArgs = {
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryBlockArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryBlocksArgs = {
  filters?: InputMaybe<BlockFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryBlocks_ConnectionArgs = {
  filters?: InputMaybe<BlockFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryBuildingArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryBuildingsArgs = {
  filters?: InputMaybe<BuildingFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryBuildings_ConnectionArgs = {
  filters?: InputMaybe<BuildingFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryCalendarDateArgs = {
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryCalendarDatesArgs = {
  filters?: InputMaybe<CalendarDateFiltersInput>;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryCalendarDates_ConnectionArgs = {
  filters?: InputMaybe<CalendarDateFiltersInput>;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryCountriesArgs = {
  filters?: InputMaybe<CountryFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryCountries_ConnectionArgs = {
  filters?: InputMaybe<CountryFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryCountryArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryDepotArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryDepotsArgs = {
  filters?: InputMaybe<DepotFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryDepots_ConnectionArgs = {
  filters?: InputMaybe<DepotFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryDriverArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryDriversArgs = {
  filters?: InputMaybe<DriverFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryDrivers_ConnectionArgs = {
  filters?: InputMaybe<DriverFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFareAttributeArgs = {
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFareAttributesArgs = {
  filters?: InputMaybe<FareAttributeFiltersInput>;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFareAttributes_ConnectionArgs = {
  filters?: InputMaybe<FareAttributeFiltersInput>;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFareRuleArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFareRulesArgs = {
  filters?: InputMaybe<FareRuleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFareRules_ConnectionArgs = {
  filters?: InputMaybe<FareRuleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFeedInfoArgs = {
  documentId: Scalars['ID']['input'];
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFeedInfosArgs = {
  filters?: InputMaybe<FeedInfoFiltersInput>;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFeedInfos_ConnectionArgs = {
  filters?: InputMaybe<FeedInfoFiltersInput>;
  locale?: InputMaybe<Scalars['I18NLocaleCode']['input']>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFrequenciesArgs = {
  filters?: InputMaybe<FrequencyFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFrequencies_ConnectionArgs = {
  filters?: InputMaybe<FrequencyFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryFrequencyArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGeofenceArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGeofenceGeometriesArgs = {
  filters?: InputMaybe<GeofenceGeometryFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGeofenceGeometries_ConnectionArgs = {
  filters?: InputMaybe<GeofenceGeometryFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGeofenceGeometryArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGeofencesArgs = {
  filters?: InputMaybe<GeofenceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGeofences_ConnectionArgs = {
  filters?: InputMaybe<GeofenceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGeometryPointArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGeometryPointsArgs = {
  filters?: InputMaybe<GeometryPointFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGeometryPoints_ConnectionArgs = {
  filters?: InputMaybe<GeometryPointFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGpsDeviceArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGpsDevicesArgs = {
  filters?: InputMaybe<GpsDeviceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryGpsDevices_ConnectionArgs = {
  filters?: InputMaybe<GpsDeviceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryHighwayArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryHighwayShapeArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryHighwayShapesArgs = {
  filters?: InputMaybe<HighwayShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryHighwayShapes_ConnectionArgs = {
  filters?: InputMaybe<HighwayShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryHighwaysArgs = {
  filters?: InputMaybe<HighwayFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryHighways_ConnectionArgs = {
  filters?: InputMaybe<HighwayFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryI18NLocaleArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryI18NLocalesArgs = {
  filters?: InputMaybe<I18NLocaleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryI18NLocales_ConnectionArgs = {
  filters?: InputMaybe<I18NLocaleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryLanduseShapeArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryLanduseShapesArgs = {
  filters?: InputMaybe<LanduseShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryLanduseShapes_ConnectionArgs = {
  filters?: InputMaybe<LanduseShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryLanduseZoneArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryLanduseZonesArgs = {
  filters?: InputMaybe<LanduseZoneFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryLanduseZones_ConnectionArgs = {
  filters?: InputMaybe<LanduseZoneFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryOperationalConfigurationArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryOperationalConfigurationsArgs = {
  filters?: InputMaybe<OperationalConfigurationFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryOperationalConfigurations_ConnectionArgs = {
  filters?: InputMaybe<OperationalConfigurationFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryPlaceArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryPlacesArgs = {
  filters?: InputMaybe<PlaceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryPlaces_ConnectionArgs = {
  filters?: InputMaybe<PlaceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryPoiArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryPoiShapeArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryPoiShapesArgs = {
  filters?: InputMaybe<PoiShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryPoiShapes_ConnectionArgs = {
  filters?: InputMaybe<PoiShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryPoisArgs = {
  filters?: InputMaybe<PoiFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryPois_ConnectionArgs = {
  filters?: InputMaybe<PoiFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRegionArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRegionShapeArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRegionShapesArgs = {
  filters?: InputMaybe<RegionShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRegionShapes_ConnectionArgs = {
  filters?: InputMaybe<RegionShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRegionsArgs = {
  filters?: InputMaybe<RegionFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRegions_ConnectionArgs = {
  filters?: InputMaybe<RegionFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryReviewWorkflowsWorkflowArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryReviewWorkflowsWorkflowStageArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryReviewWorkflowsWorkflowStagesArgs = {
  filters?: InputMaybe<ReviewWorkflowsWorkflowStageFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryReviewWorkflowsWorkflowStages_ConnectionArgs = {
  filters?: InputMaybe<ReviewWorkflowsWorkflowStageFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryReviewWorkflowsWorkflowsArgs = {
  filters?: InputMaybe<ReviewWorkflowsWorkflowFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryReviewWorkflowsWorkflows_ConnectionArgs = {
  filters?: InputMaybe<ReviewWorkflowsWorkflowFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRouteArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRouteDepotArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRouteDepotsArgs = {
  filters?: InputMaybe<RouteDepotFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRouteDepots_ConnectionArgs = {
  filters?: InputMaybe<RouteDepotFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRouteShapeArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRouteShapesArgs = {
  filters?: InputMaybe<RouteShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRouteShapes_ConnectionArgs = {
  filters?: InputMaybe<RouteShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRoutesArgs = {
  filters?: InputMaybe<RouteFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryRoutes_ConnectionArgs = {
  filters?: InputMaybe<RouteFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryServiceArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryServicesArgs = {
  filters?: InputMaybe<ServiceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryServices_ConnectionArgs = {
  filters?: InputMaybe<ServiceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryShapeArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryShapesArgs = {
  filters?: InputMaybe<ShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryShapes_ConnectionArgs = {
  filters?: InputMaybe<ShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QuerySpawnConfigArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QuerySpawnConfigsArgs = {
  filters?: InputMaybe<SpawnConfigFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QuerySpawnConfigs_ConnectionArgs = {
  filters?: InputMaybe<SpawnConfigFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryStopArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryStopTimeArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryStopTimesArgs = {
  filters?: InputMaybe<StopTimeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryStopTimes_ConnectionArgs = {
  filters?: InputMaybe<StopTimeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryStopsArgs = {
  filters?: InputMaybe<StopFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryStops_ConnectionArgs = {
  filters?: InputMaybe<StopFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryTransferArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryTransfersArgs = {
  filters?: InputMaybe<TransferFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryTransfers_ConnectionArgs = {
  filters?: InputMaybe<TransferFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryTripArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryTripsArgs = {
  filters?: InputMaybe<TripFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryTrips_ConnectionArgs = {
  filters?: InputMaybe<TripFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryUploadFileArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryUploadFilesArgs = {
  filters?: InputMaybe<UploadFileFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryUploadFiles_ConnectionArgs = {
  filters?: InputMaybe<UploadFileFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryUsersPermissionsRoleArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryUsersPermissionsRolesArgs = {
  filters?: InputMaybe<UsersPermissionsRoleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryUsersPermissionsRoles_ConnectionArgs = {
  filters?: InputMaybe<UsersPermissionsRoleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryUsersPermissionsUserArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryUsersPermissionsUsersArgs = {
  filters?: InputMaybe<UsersPermissionsUserFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryUsersPermissionsUsers_ConnectionArgs = {
  filters?: InputMaybe<UsersPermissionsUserFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryVehicleArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryVehicleEventArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryVehicleEventsArgs = {
  filters?: InputMaybe<VehicleEventFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryVehicleEvents_ConnectionArgs = {
  filters?: InputMaybe<VehicleEventFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryVehicleStatusArgs = {
  documentId: Scalars['ID']['input'];
  status?: InputMaybe<PublicationStatus>;
};


export type QueryVehicleStatusesArgs = {
  filters?: InputMaybe<VehicleStatusFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryVehicleStatuses_ConnectionArgs = {
  filters?: InputMaybe<VehicleStatusFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryVehiclesArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};


export type QueryVehicles_ConnectionArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  status?: InputMaybe<PublicationStatus>;
};

export type Region = {
  __typename?: 'Region';
  admin_level?: Maybe<AdminLevel>;
  area_sq_km?: Maybe<Scalars['Float']['output']>;
  center_latitude?: Maybe<Scalars['Float']['output']>;
  center_longitude?: Maybe<Scalars['Float']['output']>;
  country?: Maybe<Country>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  full_id?: Maybe<Scalars['String']['output']>;
  geometry_geojson?: Maybe<Scalars['JSON']['output']>;
  highways: Array<Maybe<Highway>>;
  highways_connection?: Maybe<HighwayRelationResponseCollection>;
  is_active: Scalars['Boolean']['output'];
  landuse_zones: Array<Maybe<LanduseZone>>;
  landuse_zones_connection?: Maybe<LanduseZoneRelationResponseCollection>;
  name: Scalars['String']['output'];
  osm_id?: Maybe<Scalars['String']['output']>;
  places: Array<Maybe<Place>>;
  places_connection?: Maybe<PlaceRelationResponseCollection>;
  pois: Array<Maybe<Poi>>;
  pois_connection?: Maybe<PoiRelationResponseCollection>;
  population?: Maybe<Scalars['Int']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  region_shapes: Array<Maybe<RegionShape>>;
  region_shapes_connection?: Maybe<RegionShapeRelationResponseCollection>;
  tags?: Maybe<Scalars['JSON']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};


export type RegionHighwaysArgs = {
  filters?: InputMaybe<HighwayFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RegionHighways_ConnectionArgs = {
  filters?: InputMaybe<HighwayFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RegionLanduse_ZonesArgs = {
  filters?: InputMaybe<LanduseZoneFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RegionLanduse_Zones_ConnectionArgs = {
  filters?: InputMaybe<LanduseZoneFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RegionPlacesArgs = {
  filters?: InputMaybe<PlaceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RegionPlaces_ConnectionArgs = {
  filters?: InputMaybe<PlaceFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RegionPoisArgs = {
  filters?: InputMaybe<PoiFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RegionPois_ConnectionArgs = {
  filters?: InputMaybe<PoiFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RegionRegion_ShapesArgs = {
  filters?: InputMaybe<RegionShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RegionRegion_Shapes_ConnectionArgs = {
  filters?: InputMaybe<RegionShapeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type RegionEntityResponseCollection = {
  __typename?: 'RegionEntityResponseCollection';
  nodes: Array<Region>;
  pageInfo: Pagination;
};

export type RegionFiltersInput = {
  admin_level?: InputMaybe<AdminLevelFiltersInput>;
  and?: InputMaybe<Array<InputMaybe<RegionFiltersInput>>>;
  area_sq_km?: InputMaybe<FloatFilterInput>;
  center_latitude?: InputMaybe<FloatFilterInput>;
  center_longitude?: InputMaybe<FloatFilterInput>;
  country?: InputMaybe<CountryFiltersInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  full_id?: InputMaybe<StringFilterInput>;
  geometry_geojson?: InputMaybe<JsonFilterInput>;
  highways?: InputMaybe<HighwayFiltersInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  landuse_zones?: InputMaybe<LanduseZoneFiltersInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<RegionFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<RegionFiltersInput>>>;
  osm_id?: InputMaybe<StringFilterInput>;
  places?: InputMaybe<PlaceFiltersInput>;
  pois?: InputMaybe<PoiFiltersInput>;
  population?: InputMaybe<IntFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  region_shapes?: InputMaybe<RegionShapeFiltersInput>;
  tags?: InputMaybe<JsonFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type RegionInput = {
  admin_level?: InputMaybe<Scalars['ID']['input']>;
  area_sq_km?: InputMaybe<Scalars['Float']['input']>;
  center_latitude?: InputMaybe<Scalars['Float']['input']>;
  center_longitude?: InputMaybe<Scalars['Float']['input']>;
  country?: InputMaybe<Scalars['ID']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  full_id?: InputMaybe<Scalars['String']['input']>;
  geometry_geojson?: InputMaybe<Scalars['JSON']['input']>;
  highways?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  landuse_zones?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  name?: InputMaybe<Scalars['String']['input']>;
  osm_id?: InputMaybe<Scalars['String']['input']>;
  places?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  pois?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  population?: InputMaybe<Scalars['Int']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  region_shapes?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  tags?: InputMaybe<Scalars['JSON']['input']>;
};

export type RegionRelationResponseCollection = {
  __typename?: 'RegionRelationResponseCollection';
  nodes: Array<Region>;
};

export type RegionShape = {
  __typename?: 'RegionShape';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  polygon_index?: Maybe<Scalars['Int']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  region?: Maybe<Region>;
  ring_index?: Maybe<Scalars['Int']['output']>;
  shape_pt_lat: Scalars['Float']['output'];
  shape_pt_lon: Scalars['Float']['output'];
  shape_pt_sequence: Scalars['Int']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type RegionShapeEntityResponseCollection = {
  __typename?: 'RegionShapeEntityResponseCollection';
  nodes: Array<RegionShape>;
  pageInfo: Pagination;
};

export type RegionShapeFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<RegionShapeFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  not?: InputMaybe<RegionShapeFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<RegionShapeFiltersInput>>>;
  polygon_index?: InputMaybe<IntFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  region?: InputMaybe<RegionFiltersInput>;
  ring_index?: InputMaybe<IntFilterInput>;
  shape_pt_lat?: InputMaybe<FloatFilterInput>;
  shape_pt_lon?: InputMaybe<FloatFilterInput>;
  shape_pt_sequence?: InputMaybe<IntFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type RegionShapeInput = {
  polygon_index?: InputMaybe<Scalars['Int']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  region?: InputMaybe<Scalars['ID']['input']>;
  ring_index?: InputMaybe<Scalars['Int']['input']>;
  shape_pt_lat?: InputMaybe<Scalars['Float']['input']>;
  shape_pt_lon?: InputMaybe<Scalars['Float']['input']>;
  shape_pt_sequence?: InputMaybe<Scalars['Int']['input']>;
};

export type RegionShapeRelationResponseCollection = {
  __typename?: 'RegionShapeRelationResponseCollection';
  nodes: Array<RegionShape>;
};

export type ReviewWorkflowsWorkflow = {
  __typename?: 'ReviewWorkflowsWorkflow';
  contentTypes: Scalars['JSON']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  stageRequiredToPublish?: Maybe<ReviewWorkflowsWorkflowStage>;
  stages: Array<Maybe<ReviewWorkflowsWorkflowStage>>;
  stages_connection?: Maybe<ReviewWorkflowsWorkflowStageRelationResponseCollection>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};


export type ReviewWorkflowsWorkflowStagesArgs = {
  filters?: InputMaybe<ReviewWorkflowsWorkflowStageFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type ReviewWorkflowsWorkflowStages_ConnectionArgs = {
  filters?: InputMaybe<ReviewWorkflowsWorkflowStageFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type ReviewWorkflowsWorkflowEntityResponseCollection = {
  __typename?: 'ReviewWorkflowsWorkflowEntityResponseCollection';
  nodes: Array<ReviewWorkflowsWorkflow>;
  pageInfo: Pagination;
};

export type ReviewWorkflowsWorkflowFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<ReviewWorkflowsWorkflowFiltersInput>>>;
  contentTypes?: InputMaybe<JsonFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<ReviewWorkflowsWorkflowFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<ReviewWorkflowsWorkflowFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  stageRequiredToPublish?: InputMaybe<ReviewWorkflowsWorkflowStageFiltersInput>;
  stages?: InputMaybe<ReviewWorkflowsWorkflowStageFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type ReviewWorkflowsWorkflowInput = {
  contentTypes?: InputMaybe<Scalars['JSON']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  stageRequiredToPublish?: InputMaybe<Scalars['ID']['input']>;
  stages?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
};

export type ReviewWorkflowsWorkflowStage = {
  __typename?: 'ReviewWorkflowsWorkflowStage';
  color?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  name?: Maybe<Scalars['String']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  workflow?: Maybe<ReviewWorkflowsWorkflow>;
};

export type ReviewWorkflowsWorkflowStageEntityResponseCollection = {
  __typename?: 'ReviewWorkflowsWorkflowStageEntityResponseCollection';
  nodes: Array<ReviewWorkflowsWorkflowStage>;
  pageInfo: Pagination;
};

export type ReviewWorkflowsWorkflowStageFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<ReviewWorkflowsWorkflowStageFiltersInput>>>;
  color?: InputMaybe<StringFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<ReviewWorkflowsWorkflowStageFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<ReviewWorkflowsWorkflowStageFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  workflow?: InputMaybe<ReviewWorkflowsWorkflowFiltersInput>;
};

export type ReviewWorkflowsWorkflowStageInput = {
  color?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  workflow?: InputMaybe<Scalars['ID']['input']>;
};

export type ReviewWorkflowsWorkflowStageRelationResponseCollection = {
  __typename?: 'ReviewWorkflowsWorkflowStageRelationResponseCollection';
  nodes: Array<ReviewWorkflowsWorkflowStage>;
};

export type Route = {
  __typename?: 'Route';
  activity_level?: Maybe<Scalars['Float']['output']>;
  agencies: Array<Maybe<Agency>>;
  agencies_connection?: Maybe<AgencyRelationResponseCollection>;
  associated_depots: Array<Maybe<RouteDepot>>;
  associated_depots_connection?: Maybe<RouteDepotRelationResponseCollection>;
  blocks: Array<Maybe<Block>>;
  blocks_connection?: Maybe<BlockRelationResponseCollection>;
  color?: Maybe<Scalars['String']['output']>;
  country?: Maybe<Country>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  geojson_data?: Maybe<Scalars['JSON']['output']>;
  is_active: Scalars['Boolean']['output'];
  long_name?: Maybe<Scalars['String']['output']>;
  parishes?: Maybe<Scalars['String']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  route_type?: Maybe<Scalars['Int']['output']>;
  short_name: Scalars['String']['output'];
  spawn_config?: Maybe<SpawnConfig>;
  trips: Array<Maybe<Trip>>;
  trips_connection?: Maybe<TripRelationResponseCollection>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  valid_from?: Maybe<Scalars['Date']['output']>;
  valid_to?: Maybe<Scalars['Date']['output']>;
  vehicles: Array<Maybe<Vehicle>>;
  vehicles_connection?: Maybe<VehicleRelationResponseCollection>;
  view_map_url?: Maybe<Scalars['String']['output']>;
};


export type RouteAgenciesArgs = {
  filters?: InputMaybe<AgencyFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RouteAgencies_ConnectionArgs = {
  filters?: InputMaybe<AgencyFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RouteAssociated_DepotsArgs = {
  filters?: InputMaybe<RouteDepotFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RouteAssociated_Depots_ConnectionArgs = {
  filters?: InputMaybe<RouteDepotFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RouteBlocksArgs = {
  filters?: InputMaybe<BlockFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RouteBlocks_ConnectionArgs = {
  filters?: InputMaybe<BlockFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RouteTripsArgs = {
  filters?: InputMaybe<TripFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RouteTrips_ConnectionArgs = {
  filters?: InputMaybe<TripFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RouteVehiclesArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type RouteVehicles_ConnectionArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type RouteDepot = {
  __typename?: 'RouteDepot';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  depot?: Maybe<Depot>;
  depot_name?: Maybe<Scalars['String']['output']>;
  display_name?: Maybe<Scalars['String']['output']>;
  distance_from_route_m: Scalars['Float']['output'];
  documentId: Scalars['ID']['output'];
  is_end_terminus: Scalars['Boolean']['output'];
  is_start_terminus: Scalars['Boolean']['output'];
  precomputed_at?: Maybe<Scalars['DateTime']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  route?: Maybe<Route>;
  route_short_name?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type RouteDepotEntityResponseCollection = {
  __typename?: 'RouteDepotEntityResponseCollection';
  nodes: Array<RouteDepot>;
  pageInfo: Pagination;
};

export type RouteDepotFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<RouteDepotFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  depot?: InputMaybe<DepotFiltersInput>;
  depot_name?: InputMaybe<StringFilterInput>;
  display_name?: InputMaybe<StringFilterInput>;
  distance_from_route_m?: InputMaybe<FloatFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  is_end_terminus?: InputMaybe<BooleanFilterInput>;
  is_start_terminus?: InputMaybe<BooleanFilterInput>;
  not?: InputMaybe<RouteDepotFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<RouteDepotFiltersInput>>>;
  precomputed_at?: InputMaybe<DateTimeFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  route?: InputMaybe<RouteFiltersInput>;
  route_short_name?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type RouteDepotInput = {
  depot?: InputMaybe<Scalars['ID']['input']>;
  depot_name?: InputMaybe<Scalars['String']['input']>;
  display_name?: InputMaybe<Scalars['String']['input']>;
  distance_from_route_m?: InputMaybe<Scalars['Float']['input']>;
  is_end_terminus?: InputMaybe<Scalars['Boolean']['input']>;
  is_start_terminus?: InputMaybe<Scalars['Boolean']['input']>;
  precomputed_at?: InputMaybe<Scalars['DateTime']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  route?: InputMaybe<Scalars['ID']['input']>;
  route_short_name?: InputMaybe<Scalars['String']['input']>;
};

export type RouteDepotRelationResponseCollection = {
  __typename?: 'RouteDepotRelationResponseCollection';
  nodes: Array<RouteDepot>;
};

export type RouteEntityResponseCollection = {
  __typename?: 'RouteEntityResponseCollection';
  nodes: Array<Route>;
  pageInfo: Pagination;
};

export type RouteFiltersInput = {
  activity_level?: InputMaybe<FloatFilterInput>;
  agencies?: InputMaybe<AgencyFiltersInput>;
  and?: InputMaybe<Array<InputMaybe<RouteFiltersInput>>>;
  associated_depots?: InputMaybe<RouteDepotFiltersInput>;
  blocks?: InputMaybe<BlockFiltersInput>;
  color?: InputMaybe<StringFilterInput>;
  country?: InputMaybe<CountryFiltersInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  geojson_data?: InputMaybe<JsonFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  long_name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<RouteFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<RouteFiltersInput>>>;
  parishes?: InputMaybe<StringFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  route_type?: InputMaybe<IntFilterInput>;
  short_name?: InputMaybe<StringFilterInput>;
  spawn_config?: InputMaybe<SpawnConfigFiltersInput>;
  trips?: InputMaybe<TripFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  valid_from?: InputMaybe<DateFilterInput>;
  valid_to?: InputMaybe<DateFilterInput>;
  vehicles?: InputMaybe<VehicleFiltersInput>;
  view_map_url?: InputMaybe<StringFilterInput>;
};

export type RouteInput = {
  activity_level?: InputMaybe<Scalars['Float']['input']>;
  agencies?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  associated_depots?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  blocks?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  color?: InputMaybe<Scalars['String']['input']>;
  country?: InputMaybe<Scalars['ID']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  geojson_data?: InputMaybe<Scalars['JSON']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  long_name?: InputMaybe<Scalars['String']['input']>;
  parishes?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  route_type?: InputMaybe<Scalars['Int']['input']>;
  short_name?: InputMaybe<Scalars['String']['input']>;
  spawn_config?: InputMaybe<Scalars['ID']['input']>;
  trips?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  valid_from?: InputMaybe<Scalars['Date']['input']>;
  valid_to?: InputMaybe<Scalars['Date']['input']>;
  vehicles?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  view_map_url?: InputMaybe<Scalars['String']['input']>;
};

export type RouteRelationResponseCollection = {
  __typename?: 'RouteRelationResponseCollection';
  nodes: Array<Route>;
};

export type RouteShape = {
  __typename?: 'RouteShape';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  is_default?: Maybe<Scalars['Boolean']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  route_id: Scalars['String']['output'];
  route_shape_id: Scalars['String']['output'];
  shape_id: Scalars['String']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  variant_code?: Maybe<Scalars['String']['output']>;
};

export type RouteShapeEntityResponseCollection = {
  __typename?: 'RouteShapeEntityResponseCollection';
  nodes: Array<RouteShape>;
  pageInfo: Pagination;
};

export type RouteShapeFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<RouteShapeFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  is_default?: InputMaybe<BooleanFilterInput>;
  not?: InputMaybe<RouteShapeFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<RouteShapeFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  route_id?: InputMaybe<StringFilterInput>;
  route_shape_id?: InputMaybe<StringFilterInput>;
  shape_id?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  variant_code?: InputMaybe<StringFilterInput>;
};

export type RouteShapeInput = {
  is_default?: InputMaybe<Scalars['Boolean']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  route_id?: InputMaybe<Scalars['String']['input']>;
  route_shape_id?: InputMaybe<Scalars['String']['input']>;
  shape_id?: InputMaybe<Scalars['String']['input']>;
  variant_code?: InputMaybe<Scalars['String']['input']>;
};

export type Service = {
  __typename?: 'Service';
  calendar_dates: Array<Maybe<CalendarDate>>;
  calendar_dates_connection?: Maybe<CalendarDateRelationResponseCollection>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  end_date: Scalars['Date']['output'];
  friday: Scalars['Boolean']['output'];
  is_active: Scalars['Boolean']['output'];
  monday: Scalars['Boolean']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  saturday: Scalars['Boolean']['output'];
  service_id: Scalars['String']['output'];
  service_name?: Maybe<Scalars['String']['output']>;
  start_date: Scalars['Date']['output'];
  sunday: Scalars['Boolean']['output'];
  thursday: Scalars['Boolean']['output'];
  trips: Array<Maybe<Trip>>;
  trips_connection?: Maybe<TripRelationResponseCollection>;
  tuesday: Scalars['Boolean']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  wednesday: Scalars['Boolean']['output'];
};


export type ServiceCalendar_DatesArgs = {
  filters?: InputMaybe<CalendarDateFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type ServiceCalendar_Dates_ConnectionArgs = {
  filters?: InputMaybe<CalendarDateFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type ServiceTripsArgs = {
  filters?: InputMaybe<TripFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type ServiceTrips_ConnectionArgs = {
  filters?: InputMaybe<TripFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type ServiceEntityResponseCollection = {
  __typename?: 'ServiceEntityResponseCollection';
  nodes: Array<Service>;
  pageInfo: Pagination;
};

export type ServiceFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<ServiceFiltersInput>>>;
  calendar_dates?: InputMaybe<CalendarDateFiltersInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  end_date?: InputMaybe<DateFilterInput>;
  friday?: InputMaybe<BooleanFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  monday?: InputMaybe<BooleanFilterInput>;
  not?: InputMaybe<ServiceFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<ServiceFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  saturday?: InputMaybe<BooleanFilterInput>;
  service_id?: InputMaybe<StringFilterInput>;
  service_name?: InputMaybe<StringFilterInput>;
  start_date?: InputMaybe<DateFilterInput>;
  sunday?: InputMaybe<BooleanFilterInput>;
  thursday?: InputMaybe<BooleanFilterInput>;
  trips?: InputMaybe<TripFiltersInput>;
  tuesday?: InputMaybe<BooleanFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  wednesday?: InputMaybe<BooleanFilterInput>;
};

export type ServiceInput = {
  calendar_dates?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  end_date?: InputMaybe<Scalars['Date']['input']>;
  friday?: InputMaybe<Scalars['Boolean']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  monday?: InputMaybe<Scalars['Boolean']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  saturday?: InputMaybe<Scalars['Boolean']['input']>;
  service_id?: InputMaybe<Scalars['String']['input']>;
  service_name?: InputMaybe<Scalars['String']['input']>;
  start_date?: InputMaybe<Scalars['Date']['input']>;
  sunday?: InputMaybe<Scalars['Boolean']['input']>;
  thursday?: InputMaybe<Scalars['Boolean']['input']>;
  trips?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  tuesday?: InputMaybe<Scalars['Boolean']['input']>;
  wednesday?: InputMaybe<Scalars['Boolean']['input']>;
};

export type Shape = {
  __typename?: 'Shape';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  is_active: Scalars['Boolean']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  shape_dist_traveled?: Maybe<Scalars['Float']['output']>;
  shape_id: Scalars['String']['output'];
  shape_pt_lat: Scalars['Float']['output'];
  shape_pt_lon: Scalars['Float']['output'];
  shape_pt_sequence: Scalars['Int']['output'];
  trips: Array<Maybe<Trip>>;
  trips_connection?: Maybe<TripRelationResponseCollection>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};


export type ShapeTripsArgs = {
  filters?: InputMaybe<TripFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type ShapeTrips_ConnectionArgs = {
  filters?: InputMaybe<TripFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type ShapeEntityResponseCollection = {
  __typename?: 'ShapeEntityResponseCollection';
  nodes: Array<Shape>;
  pageInfo: Pagination;
};

export type ShapeFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<ShapeFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  not?: InputMaybe<ShapeFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<ShapeFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  shape_dist_traveled?: InputMaybe<FloatFilterInput>;
  shape_id?: InputMaybe<StringFilterInput>;
  shape_pt_lat?: InputMaybe<FloatFilterInput>;
  shape_pt_lon?: InputMaybe<FloatFilterInput>;
  shape_pt_sequence?: InputMaybe<IntFilterInput>;
  trips?: InputMaybe<TripFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type ShapeInput = {
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  shape_dist_traveled?: InputMaybe<Scalars['Float']['input']>;
  shape_id?: InputMaybe<Scalars['String']['input']>;
  shape_pt_lat?: InputMaybe<Scalars['Float']['input']>;
  shape_pt_lon?: InputMaybe<Scalars['Float']['input']>;
  shape_pt_sequence?: InputMaybe<Scalars['Int']['input']>;
  trips?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
};

export type SpawnConfig = {
  __typename?: 'SpawnConfig';
  config: Scalars['JSON']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  is_active: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  route?: Maybe<Route>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type SpawnConfigEntityResponseCollection = {
  __typename?: 'SpawnConfigEntityResponseCollection';
  nodes: Array<SpawnConfig>;
  pageInfo: Pagination;
};

export type SpawnConfigFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<SpawnConfigFiltersInput>>>;
  config?: InputMaybe<JsonFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<SpawnConfigFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<SpawnConfigFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  route?: InputMaybe<RouteFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type SpawnConfigInput = {
  config?: InputMaybe<Scalars['JSON']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  route?: InputMaybe<Scalars['ID']['input']>;
};

export type Stop = {
  __typename?: 'Stop';
  code?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  is_active: Scalars['Boolean']['output'];
  latitude?: Maybe<Scalars['Float']['output']>;
  location?: Maybe<Scalars['JSON']['output']>;
  location_type?: Maybe<Enum_Stop_Location_Type>;
  longitude?: Maybe<Scalars['Float']['output']>;
  name: Scalars['String']['output'];
  parent_station?: Maybe<Scalars['String']['output']>;
  platform_code?: Maybe<Scalars['String']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  stop_id: Scalars['String']['output'];
  stop_times: Array<Maybe<StopTime>>;
  stop_times_connection?: Maybe<StopTimeRelationResponseCollection>;
  stop_url?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  wheelchair_boarding?: Maybe<Enum_Stop_Wheelchair_Boarding>;
  zone_id?: Maybe<Scalars['String']['output']>;
};


export type StopStop_TimesArgs = {
  filters?: InputMaybe<StopTimeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type StopStop_Times_ConnectionArgs = {
  filters?: InputMaybe<StopTimeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type StopEntityResponseCollection = {
  __typename?: 'StopEntityResponseCollection';
  nodes: Array<Stop>;
  pageInfo: Pagination;
};

export type StopFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<StopFiltersInput>>>;
  code?: InputMaybe<StringFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  latitude?: InputMaybe<FloatFilterInput>;
  location?: InputMaybe<JsonFilterInput>;
  location_type?: InputMaybe<StringFilterInput>;
  longitude?: InputMaybe<FloatFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<StopFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<StopFiltersInput>>>;
  parent_station?: InputMaybe<StringFilterInput>;
  platform_code?: InputMaybe<StringFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  stop_id?: InputMaybe<StringFilterInput>;
  stop_times?: InputMaybe<StopTimeFiltersInput>;
  stop_url?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  wheelchair_boarding?: InputMaybe<StringFilterInput>;
  zone_id?: InputMaybe<StringFilterInput>;
};

export type StopInput = {
  code?: InputMaybe<Scalars['String']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  latitude?: InputMaybe<Scalars['Float']['input']>;
  location?: InputMaybe<Scalars['JSON']['input']>;
  location_type?: InputMaybe<Enum_Stop_Location_Type>;
  longitude?: InputMaybe<Scalars['Float']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  parent_station?: InputMaybe<Scalars['String']['input']>;
  platform_code?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  stop_id?: InputMaybe<Scalars['String']['input']>;
  stop_times?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  stop_url?: InputMaybe<Scalars['String']['input']>;
  wheelchair_boarding?: InputMaybe<Enum_Stop_Wheelchair_Boarding>;
  zone_id?: InputMaybe<Scalars['String']['input']>;
};

export type StopTime = {
  __typename?: 'StopTime';
  arrival_time?: Maybe<Scalars['Time']['output']>;
  continuous_drop_off?: Maybe<Scalars['Int']['output']>;
  continuous_pickup?: Maybe<Scalars['Int']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  departure_time?: Maybe<Scalars['Time']['output']>;
  documentId: Scalars['ID']['output'];
  drop_off_type?: Maybe<Scalars['Int']['output']>;
  is_active?: Maybe<Scalars['Boolean']['output']>;
  pickup_type?: Maybe<Scalars['Int']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  shape_dist_traveled?: Maybe<Scalars['Float']['output']>;
  stop?: Maybe<Stop>;
  stop_headsign?: Maybe<Scalars['String']['output']>;
  stop_sequence: Scalars['Int']['output'];
  timepoint?: Maybe<Scalars['Int']['output']>;
  trip?: Maybe<Trip>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type StopTimeEntityResponseCollection = {
  __typename?: 'StopTimeEntityResponseCollection';
  nodes: Array<StopTime>;
  pageInfo: Pagination;
};

export type StopTimeFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<StopTimeFiltersInput>>>;
  arrival_time?: InputMaybe<TimeFilterInput>;
  continuous_drop_off?: InputMaybe<IntFilterInput>;
  continuous_pickup?: InputMaybe<IntFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  departure_time?: InputMaybe<TimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  drop_off_type?: InputMaybe<IntFilterInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  not?: InputMaybe<StopTimeFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<StopTimeFiltersInput>>>;
  pickup_type?: InputMaybe<IntFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  shape_dist_traveled?: InputMaybe<FloatFilterInput>;
  stop?: InputMaybe<StopFiltersInput>;
  stop_headsign?: InputMaybe<StringFilterInput>;
  stop_sequence?: InputMaybe<IntFilterInput>;
  timepoint?: InputMaybe<IntFilterInput>;
  trip?: InputMaybe<TripFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type StopTimeInput = {
  arrival_time?: InputMaybe<Scalars['Time']['input']>;
  continuous_drop_off?: InputMaybe<Scalars['Int']['input']>;
  continuous_pickup?: InputMaybe<Scalars['Int']['input']>;
  departure_time?: InputMaybe<Scalars['Time']['input']>;
  drop_off_type?: InputMaybe<Scalars['Int']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  pickup_type?: InputMaybe<Scalars['Int']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  shape_dist_traveled?: InputMaybe<Scalars['Float']['input']>;
  stop?: InputMaybe<Scalars['ID']['input']>;
  stop_headsign?: InputMaybe<Scalars['String']['input']>;
  stop_sequence?: InputMaybe<Scalars['Int']['input']>;
  timepoint?: InputMaybe<Scalars['Int']['input']>;
  trip?: InputMaybe<Scalars['ID']['input']>;
};

export type StopTimeRelationResponseCollection = {
  __typename?: 'StopTimeRelationResponseCollection';
  nodes: Array<StopTime>;
};

export type StringFilterInput = {
  and?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  between?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  contains?: InputMaybe<Scalars['String']['input']>;
  containsi?: InputMaybe<Scalars['String']['input']>;
  endsWith?: InputMaybe<Scalars['String']['input']>;
  eq?: InputMaybe<Scalars['String']['input']>;
  eqi?: InputMaybe<Scalars['String']['input']>;
  gt?: InputMaybe<Scalars['String']['input']>;
  gte?: InputMaybe<Scalars['String']['input']>;
  in?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  lt?: InputMaybe<Scalars['String']['input']>;
  lte?: InputMaybe<Scalars['String']['input']>;
  ne?: InputMaybe<Scalars['String']['input']>;
  nei?: InputMaybe<Scalars['String']['input']>;
  not?: InputMaybe<StringFilterInput>;
  notContains?: InputMaybe<Scalars['String']['input']>;
  notContainsi?: InputMaybe<Scalars['String']['input']>;
  notIn?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  notNull?: InputMaybe<Scalars['Boolean']['input']>;
  null?: InputMaybe<Scalars['Boolean']['input']>;
  or?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  startsWith?: InputMaybe<Scalars['String']['input']>;
};

export type TimeFilterInput = {
  and?: InputMaybe<Array<InputMaybe<Scalars['Time']['input']>>>;
  between?: InputMaybe<Array<InputMaybe<Scalars['Time']['input']>>>;
  contains?: InputMaybe<Scalars['Time']['input']>;
  containsi?: InputMaybe<Scalars['Time']['input']>;
  endsWith?: InputMaybe<Scalars['Time']['input']>;
  eq?: InputMaybe<Scalars['Time']['input']>;
  eqi?: InputMaybe<Scalars['Time']['input']>;
  gt?: InputMaybe<Scalars['Time']['input']>;
  gte?: InputMaybe<Scalars['Time']['input']>;
  in?: InputMaybe<Array<InputMaybe<Scalars['Time']['input']>>>;
  lt?: InputMaybe<Scalars['Time']['input']>;
  lte?: InputMaybe<Scalars['Time']['input']>;
  ne?: InputMaybe<Scalars['Time']['input']>;
  nei?: InputMaybe<Scalars['Time']['input']>;
  not?: InputMaybe<TimeFilterInput>;
  notContains?: InputMaybe<Scalars['Time']['input']>;
  notContainsi?: InputMaybe<Scalars['Time']['input']>;
  notIn?: InputMaybe<Array<InputMaybe<Scalars['Time']['input']>>>;
  notNull?: InputMaybe<Scalars['Boolean']['input']>;
  null?: InputMaybe<Scalars['Boolean']['input']>;
  or?: InputMaybe<Array<InputMaybe<Scalars['Time']['input']>>>;
  startsWith?: InputMaybe<Scalars['Time']['input']>;
};

export type Transfer = {
  __typename?: 'Transfer';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  from_stop?: Maybe<Stop>;
  is_active?: Maybe<Scalars['Boolean']['output']>;
  min_transfer_time?: Maybe<Scalars['Int']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  to_stop?: Maybe<Stop>;
  transfer_type: Scalars['Int']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type TransferEntityResponseCollection = {
  __typename?: 'TransferEntityResponseCollection';
  nodes: Array<Transfer>;
  pageInfo: Pagination;
};

export type TransferFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<TransferFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  from_stop?: InputMaybe<StopFiltersInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  min_transfer_time?: InputMaybe<IntFilterInput>;
  not?: InputMaybe<TransferFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<TransferFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  to_stop?: InputMaybe<StopFiltersInput>;
  transfer_type?: InputMaybe<IntFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type TransferInput = {
  from_stop?: InputMaybe<Scalars['ID']['input']>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  min_transfer_time?: InputMaybe<Scalars['Int']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  to_stop?: InputMaybe<Scalars['ID']['input']>;
  transfer_type?: InputMaybe<Scalars['Int']['input']>;
};

export type Trip = {
  __typename?: 'Trip';
  bikes_allowed?: Maybe<Enum_Trip_Bikes_Allowed>;
  block_id?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  direction_id?: Maybe<Enum_Trip_Direction_Id>;
  documentId: Scalars['ID']['output'];
  frequencies: Array<Maybe<Frequency>>;
  frequencies_connection?: Maybe<FrequencyRelationResponseCollection>;
  is_active: Scalars['Boolean']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  route?: Maybe<Route>;
  service?: Maybe<Service>;
  shape?: Maybe<Shape>;
  stop_times: Array<Maybe<StopTime>>;
  stop_times_connection?: Maybe<StopTimeRelationResponseCollection>;
  trip_headsign?: Maybe<Scalars['String']['output']>;
  trip_id: Scalars['String']['output'];
  trip_short_name?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  wheelchair_accessible?: Maybe<Enum_Trip_Wheelchair_Accessible>;
};


export type TripFrequenciesArgs = {
  filters?: InputMaybe<FrequencyFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type TripFrequencies_ConnectionArgs = {
  filters?: InputMaybe<FrequencyFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type TripStop_TimesArgs = {
  filters?: InputMaybe<StopTimeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type TripStop_Times_ConnectionArgs = {
  filters?: InputMaybe<StopTimeFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type TripEntityResponseCollection = {
  __typename?: 'TripEntityResponseCollection';
  nodes: Array<Trip>;
  pageInfo: Pagination;
};

export type TripFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<TripFiltersInput>>>;
  bikes_allowed?: InputMaybe<StringFilterInput>;
  block_id?: InputMaybe<StringFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  direction_id?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  frequencies?: InputMaybe<FrequencyFiltersInput>;
  is_active?: InputMaybe<BooleanFilterInput>;
  not?: InputMaybe<TripFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<TripFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  route?: InputMaybe<RouteFiltersInput>;
  service?: InputMaybe<ServiceFiltersInput>;
  shape?: InputMaybe<ShapeFiltersInput>;
  stop_times?: InputMaybe<StopTimeFiltersInput>;
  trip_headsign?: InputMaybe<StringFilterInput>;
  trip_id?: InputMaybe<StringFilterInput>;
  trip_short_name?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  wheelchair_accessible?: InputMaybe<StringFilterInput>;
};

export type TripInput = {
  bikes_allowed?: InputMaybe<Enum_Trip_Bikes_Allowed>;
  block_id?: InputMaybe<Scalars['String']['input']>;
  direction_id?: InputMaybe<Enum_Trip_Direction_Id>;
  frequencies?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  is_active?: InputMaybe<Scalars['Boolean']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  route?: InputMaybe<Scalars['ID']['input']>;
  service?: InputMaybe<Scalars['ID']['input']>;
  shape?: InputMaybe<Scalars['ID']['input']>;
  stop_times?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  trip_headsign?: InputMaybe<Scalars['String']['input']>;
  trip_id?: InputMaybe<Scalars['String']['input']>;
  trip_short_name?: InputMaybe<Scalars['String']['input']>;
  wheelchair_accessible?: InputMaybe<Enum_Trip_Wheelchair_Accessible>;
};

export type TripRelationResponseCollection = {
  __typename?: 'TripRelationResponseCollection';
  nodes: Array<Trip>;
};

export type UploadFile = {
  __typename?: 'UploadFile';
  alternativeText?: Maybe<Scalars['String']['output']>;
  caption?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  ext?: Maybe<Scalars['String']['output']>;
  formats?: Maybe<Scalars['JSON']['output']>;
  hash: Scalars['String']['output'];
  height?: Maybe<Scalars['Int']['output']>;
  mime: Scalars['String']['output'];
  name: Scalars['String']['output'];
  previewUrl?: Maybe<Scalars['String']['output']>;
  provider: Scalars['String']['output'];
  provider_metadata?: Maybe<Scalars['JSON']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  related?: Maybe<Array<Maybe<GenericMorph>>>;
  size: Scalars['Float']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  url: Scalars['String']['output'];
  width?: Maybe<Scalars['Int']['output']>;
};

export type UploadFileEntityResponseCollection = {
  __typename?: 'UploadFileEntityResponseCollection';
  nodes: Array<UploadFile>;
  pageInfo: Pagination;
};

export type UploadFileFiltersInput = {
  alternativeText?: InputMaybe<StringFilterInput>;
  and?: InputMaybe<Array<InputMaybe<UploadFileFiltersInput>>>;
  caption?: InputMaybe<StringFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  ext?: InputMaybe<StringFilterInput>;
  formats?: InputMaybe<JsonFilterInput>;
  hash?: InputMaybe<StringFilterInput>;
  height?: InputMaybe<IntFilterInput>;
  mime?: InputMaybe<StringFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<UploadFileFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<UploadFileFiltersInput>>>;
  previewUrl?: InputMaybe<StringFilterInput>;
  provider?: InputMaybe<StringFilterInput>;
  provider_metadata?: InputMaybe<JsonFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  size?: InputMaybe<FloatFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  url?: InputMaybe<StringFilterInput>;
  width?: InputMaybe<IntFilterInput>;
};

export type UsersPermissionsCreateRolePayload = {
  __typename?: 'UsersPermissionsCreateRolePayload';
  ok: Scalars['Boolean']['output'];
};

export type UsersPermissionsDeleteRolePayload = {
  __typename?: 'UsersPermissionsDeleteRolePayload';
  ok: Scalars['Boolean']['output'];
};

export type UsersPermissionsLoginInput = {
  identifier: Scalars['String']['input'];
  password: Scalars['String']['input'];
  provider?: Scalars['String']['input'];
};

export type UsersPermissionsLoginPayload = {
  __typename?: 'UsersPermissionsLoginPayload';
  jwt?: Maybe<Scalars['String']['output']>;
  user: UsersPermissionsMe;
};

export type UsersPermissionsMe = {
  __typename?: 'UsersPermissionsMe';
  blocked?: Maybe<Scalars['Boolean']['output']>;
  confirmed?: Maybe<Scalars['Boolean']['output']>;
  documentId: Scalars['ID']['output'];
  email?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  role?: Maybe<UsersPermissionsMeRole>;
  username: Scalars['String']['output'];
};

export type UsersPermissionsMeRole = {
  __typename?: 'UsersPermissionsMeRole';
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  type?: Maybe<Scalars['String']['output']>;
};

export type UsersPermissionsPasswordPayload = {
  __typename?: 'UsersPermissionsPasswordPayload';
  ok: Scalars['Boolean']['output'];
};

export type UsersPermissionsPermission = {
  __typename?: 'UsersPermissionsPermission';
  action: Scalars['String']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  role?: Maybe<UsersPermissionsRole>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type UsersPermissionsPermissionFiltersInput = {
  action?: InputMaybe<StringFilterInput>;
  and?: InputMaybe<Array<InputMaybe<UsersPermissionsPermissionFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  not?: InputMaybe<UsersPermissionsPermissionFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<UsersPermissionsPermissionFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  role?: InputMaybe<UsersPermissionsRoleFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
};

export type UsersPermissionsPermissionRelationResponseCollection = {
  __typename?: 'UsersPermissionsPermissionRelationResponseCollection';
  nodes: Array<UsersPermissionsPermission>;
};

export type UsersPermissionsRegisterInput = {
  email: Scalars['String']['input'];
  password: Scalars['String']['input'];
  username: Scalars['String']['input'];
};

export type UsersPermissionsRole = {
  __typename?: 'UsersPermissionsRole';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  documentId: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  permissions: Array<Maybe<UsersPermissionsPermission>>;
  permissions_connection?: Maybe<UsersPermissionsPermissionRelationResponseCollection>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  type?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  users: Array<Maybe<UsersPermissionsUser>>;
  users_connection?: Maybe<UsersPermissionsUserRelationResponseCollection>;
};


export type UsersPermissionsRolePermissionsArgs = {
  filters?: InputMaybe<UsersPermissionsPermissionFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type UsersPermissionsRolePermissions_ConnectionArgs = {
  filters?: InputMaybe<UsersPermissionsPermissionFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type UsersPermissionsRoleUsersArgs = {
  filters?: InputMaybe<UsersPermissionsUserFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type UsersPermissionsRoleUsers_ConnectionArgs = {
  filters?: InputMaybe<UsersPermissionsUserFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type UsersPermissionsRoleEntityResponseCollection = {
  __typename?: 'UsersPermissionsRoleEntityResponseCollection';
  nodes: Array<UsersPermissionsRole>;
  pageInfo: Pagination;
};

export type UsersPermissionsRoleFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<UsersPermissionsRoleFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  description?: InputMaybe<StringFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<UsersPermissionsRoleFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<UsersPermissionsRoleFiltersInput>>>;
  permissions?: InputMaybe<UsersPermissionsPermissionFiltersInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  type?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  users?: InputMaybe<UsersPermissionsUserFiltersInput>;
};

export type UsersPermissionsRoleInput = {
  description?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  permissions?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  type?: InputMaybe<Scalars['String']['input']>;
  users?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
};

export type UsersPermissionsUpdateRolePayload = {
  __typename?: 'UsersPermissionsUpdateRolePayload';
  ok: Scalars['Boolean']['output'];
};

export type UsersPermissionsUser = {
  __typename?: 'UsersPermissionsUser';
  blocked?: Maybe<Scalars['Boolean']['output']>;
  confirmed?: Maybe<Scalars['Boolean']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  email: Scalars['String']['output'];
  provider?: Maybe<Scalars['String']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  role?: Maybe<UsersPermissionsRole>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  username: Scalars['String']['output'];
};

export type UsersPermissionsUserEntityResponse = {
  __typename?: 'UsersPermissionsUserEntityResponse';
  data?: Maybe<UsersPermissionsUser>;
};

export type UsersPermissionsUserEntityResponseCollection = {
  __typename?: 'UsersPermissionsUserEntityResponseCollection';
  nodes: Array<UsersPermissionsUser>;
  pageInfo: Pagination;
};

export type UsersPermissionsUserFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<UsersPermissionsUserFiltersInput>>>;
  blocked?: InputMaybe<BooleanFilterInput>;
  confirmed?: InputMaybe<BooleanFilterInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  email?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<UsersPermissionsUserFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<UsersPermissionsUserFiltersInput>>>;
  provider?: InputMaybe<StringFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  role?: InputMaybe<UsersPermissionsRoleFiltersInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  username?: InputMaybe<StringFilterInput>;
};

export type UsersPermissionsUserInput = {
  blocked?: InputMaybe<Scalars['Boolean']['input']>;
  confirmed?: InputMaybe<Scalars['Boolean']['input']>;
  email?: InputMaybe<Scalars['String']['input']>;
  password?: InputMaybe<Scalars['String']['input']>;
  provider?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  role?: InputMaybe<Scalars['ID']['input']>;
  username?: InputMaybe<Scalars['String']['input']>;
};

export type UsersPermissionsUserRelationResponseCollection = {
  __typename?: 'UsersPermissionsUserRelationResponseCollection';
  nodes: Array<UsersPermissionsUser>;
};

export type Vehicle = {
  __typename?: 'Vehicle';
  acceleration_mps2: Scalars['Float']['output'];
  assigned_driver?: Maybe<Driver>;
  braking_mps2: Scalars['Float']['output'];
  capacity?: Maybe<Scalars['Int']['output']>;
  country?: Maybe<Country>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  eco_mode: Scalars['Boolean']['output'];
  gps_device?: Maybe<GpsDevice>;
  home_depot?: Maybe<Depot>;
  max_speed_kmh: Scalars['Float']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  performance_profile?: Maybe<Enum_Vehicle_Performance_Profile>;
  preferred_route?: Maybe<Route>;
  profile_id?: Maybe<Scalars['String']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  reg_code: Scalars['String']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  vehicle_id: Scalars['String']['output'];
  vehicle_status?: Maybe<VehicleStatus>;
};

export type VehicleEntityResponseCollection = {
  __typename?: 'VehicleEntityResponseCollection';
  nodes: Array<Vehicle>;
  pageInfo: Pagination;
};

export type VehicleEvent = {
  __typename?: 'VehicleEvent';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  event_data?: Maybe<Scalars['JSON']['output']>;
  event_type: Enum_Vehicleevent_Event_Type;
  heading?: Maybe<Scalars['Float']['output']>;
  latitude?: Maybe<Scalars['Float']['output']>;
  longitude?: Maybe<Scalars['Float']['output']>;
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  speed?: Maybe<Scalars['Float']['output']>;
  timestamp: Scalars['DateTime']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  vehicle_id: Scalars['String']['output'];
};

export type VehicleEventEntityResponseCollection = {
  __typename?: 'VehicleEventEntityResponseCollection';
  nodes: Array<VehicleEvent>;
  pageInfo: Pagination;
};

export type VehicleEventFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<VehicleEventFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  event_data?: InputMaybe<JsonFilterInput>;
  event_type?: InputMaybe<StringFilterInput>;
  heading?: InputMaybe<FloatFilterInput>;
  latitude?: InputMaybe<FloatFilterInput>;
  longitude?: InputMaybe<FloatFilterInput>;
  not?: InputMaybe<VehicleEventFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<VehicleEventFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  speed?: InputMaybe<FloatFilterInput>;
  timestamp?: InputMaybe<DateTimeFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  vehicle_id?: InputMaybe<StringFilterInput>;
};

export type VehicleEventInput = {
  event_data?: InputMaybe<Scalars['JSON']['input']>;
  event_type?: InputMaybe<Enum_Vehicleevent_Event_Type>;
  heading?: InputMaybe<Scalars['Float']['input']>;
  latitude?: InputMaybe<Scalars['Float']['input']>;
  longitude?: InputMaybe<Scalars['Float']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  speed?: InputMaybe<Scalars['Float']['input']>;
  timestamp?: InputMaybe<Scalars['DateTime']['input']>;
  vehicle_id?: InputMaybe<Scalars['String']['input']>;
};

export type VehicleFiltersInput = {
  acceleration_mps2?: InputMaybe<FloatFilterInput>;
  and?: InputMaybe<Array<InputMaybe<VehicleFiltersInput>>>;
  assigned_driver?: InputMaybe<DriverFiltersInput>;
  braking_mps2?: InputMaybe<FloatFilterInput>;
  capacity?: InputMaybe<IntFilterInput>;
  country?: InputMaybe<CountryFiltersInput>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  eco_mode?: InputMaybe<BooleanFilterInput>;
  gps_device?: InputMaybe<GpsDeviceFiltersInput>;
  home_depot?: InputMaybe<DepotFiltersInput>;
  max_speed_kmh?: InputMaybe<FloatFilterInput>;
  not?: InputMaybe<VehicleFiltersInput>;
  notes?: InputMaybe<StringFilterInput>;
  or?: InputMaybe<Array<InputMaybe<VehicleFiltersInput>>>;
  performance_profile?: InputMaybe<StringFilterInput>;
  preferred_route?: InputMaybe<RouteFiltersInput>;
  profile_id?: InputMaybe<StringFilterInput>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  reg_code?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  vehicle_id?: InputMaybe<StringFilterInput>;
  vehicle_status?: InputMaybe<VehicleStatusFiltersInput>;
};

export type VehicleInput = {
  acceleration_mps2?: InputMaybe<Scalars['Float']['input']>;
  assigned_driver?: InputMaybe<Scalars['ID']['input']>;
  braking_mps2?: InputMaybe<Scalars['Float']['input']>;
  capacity?: InputMaybe<Scalars['Int']['input']>;
  country?: InputMaybe<Scalars['ID']['input']>;
  eco_mode?: InputMaybe<Scalars['Boolean']['input']>;
  gps_device?: InputMaybe<Scalars['ID']['input']>;
  home_depot?: InputMaybe<Scalars['ID']['input']>;
  max_speed_kmh?: InputMaybe<Scalars['Float']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
  performance_profile?: InputMaybe<Enum_Vehicle_Performance_Profile>;
  preferred_route?: InputMaybe<Scalars['ID']['input']>;
  profile_id?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  reg_code?: InputMaybe<Scalars['String']['input']>;
  vehicle_id?: InputMaybe<Scalars['String']['input']>;
  vehicle_status?: InputMaybe<Scalars['ID']['input']>;
};

export type VehicleRelationResponseCollection = {
  __typename?: 'VehicleRelationResponseCollection';
  nodes: Array<Vehicle>;
};

export type VehicleStatus = {
  __typename?: 'VehicleStatus';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  documentId: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  status_id: Scalars['String']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  vehicles: Array<Maybe<Vehicle>>;
  vehicles_connection?: Maybe<VehicleRelationResponseCollection>;
};


export type VehicleStatusVehiclesArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


export type VehicleStatusVehicles_ConnectionArgs = {
  filters?: InputMaybe<VehicleFiltersInput>;
  pagination?: InputMaybe<PaginationArg>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};

export type VehicleStatusEntityResponseCollection = {
  __typename?: 'VehicleStatusEntityResponseCollection';
  nodes: Array<VehicleStatus>;
  pageInfo: Pagination;
};

export type VehicleStatusFiltersInput = {
  and?: InputMaybe<Array<InputMaybe<VehicleStatusFiltersInput>>>;
  createdAt?: InputMaybe<DateTimeFilterInput>;
  documentId?: InputMaybe<IdFilterInput>;
  name?: InputMaybe<StringFilterInput>;
  not?: InputMaybe<VehicleStatusFiltersInput>;
  or?: InputMaybe<Array<InputMaybe<VehicleStatusFiltersInput>>>;
  publishedAt?: InputMaybe<DateTimeFilterInput>;
  status_id?: InputMaybe<StringFilterInput>;
  updatedAt?: InputMaybe<DateTimeFilterInput>;
  vehicles?: InputMaybe<VehicleFiltersInput>;
};

export type VehicleStatusInput = {
  name?: InputMaybe<Scalars['String']['input']>;
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  status_id?: InputMaybe<Scalars['String']['input']>;
  vehicles?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
};

export type CreateRouteMutationVariables = Exact<{
  data: RouteInput;
}>;


export type CreateRouteMutation = { __typename?: 'Mutation', createRoute?: { __typename?: 'Route', documentId: string, short_name: string, long_name?: string | null, description?: string | null, color?: string | null, route_type?: number | null } | null };

export type UpdateRouteMutationVariables = Exact<{
  documentId: Scalars['ID']['input'];
  data: RouteInput;
}>;


export type UpdateRouteMutation = { __typename?: 'Mutation', updateRoute?: { __typename?: 'Route', documentId: string, short_name: string, long_name?: string | null, description?: string | null, color?: string | null, route_type?: number | null } | null };

export type DeleteRouteMutationVariables = Exact<{
  documentId: Scalars['ID']['input'];
}>;


export type DeleteRouteMutation = { __typename?: 'Mutation', deleteRoute?: { __typename?: 'DeleteMutationResponse', documentId: string } | null };

export type RouteBasicFragment = { __typename?: 'Route', documentId: string, short_name: string, long_name?: string | null, description?: string | null, color?: string | null, route_type?: number | null };

export type GetRoutesQueryVariables = Exact<{
  limit?: InputMaybe<Scalars['Int']['input']>;
  start?: InputMaybe<Scalars['Int']['input']>;
  sort?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>> | InputMaybe<Scalars['String']['input']>>;
}>;


export type GetRoutesQuery = { __typename?: 'Query', routes: Array<{ __typename?: 'Route', documentId: string, short_name: string, long_name?: string | null, description?: string | null, color?: string | null, route_type?: number | null } | null> };

export type GetRouteQueryVariables = Exact<{
  documentId: Scalars['ID']['input'];
}>;


export type GetRouteQuery = { __typename?: 'Query', route?: { __typename?: 'Route', createdAt?: any | null, updatedAt?: any | null, documentId: string, short_name: string, long_name?: string | null, description?: string | null, color?: string | null, route_type?: number | null } | null };

export type GetRouteByCodeQueryVariables = Exact<{
  shortName: Scalars['String']['input'];
}>;


export type GetRouteByCodeQuery = { __typename?: 'Query', routes: Array<{ __typename?: 'Route', documentId: string, short_name: string, long_name?: string | null, description?: string | null, color?: string | null, route_type?: number | null } | null> };

export type SearchRoutesQueryVariables = Exact<{
  search: Scalars['String']['input'];
  limit?: InputMaybe<Scalars['Int']['input']>;
}>;


export type SearchRoutesQuery = { __typename?: 'Query', routes: Array<{ __typename?: 'Route', documentId: string, short_name: string, long_name?: string | null, description?: string | null, color?: string | null, route_type?: number | null } | null> };

export const RouteBasicFragmentDoc = gql`
    fragment RouteBasic on Route {
  documentId
  short_name
  long_name
  description
  color
  route_type
}
    `;
export const CreateRouteDocument = gql`
    mutation CreateRoute($data: RouteInput!) {
  createRoute(data: $data) {
    ...RouteBasic
  }
}
    ${RouteBasicFragmentDoc}`;

export function useCreateRouteMutation() {
  return Urql.useMutation<CreateRouteMutation, CreateRouteMutationVariables>(CreateRouteDocument);
};
export const UpdateRouteDocument = gql`
    mutation UpdateRoute($documentId: ID!, $data: RouteInput!) {
  updateRoute(documentId: $documentId, data: $data) {
    ...RouteBasic
  }
}
    ${RouteBasicFragmentDoc}`;

export function useUpdateRouteMutation() {
  return Urql.useMutation<UpdateRouteMutation, UpdateRouteMutationVariables>(UpdateRouteDocument);
};
export const DeleteRouteDocument = gql`
    mutation DeleteRoute($documentId: ID!) {
  deleteRoute(documentId: $documentId) {
    documentId
  }
}
    `;

export function useDeleteRouteMutation() {
  return Urql.useMutation<DeleteRouteMutation, DeleteRouteMutationVariables>(DeleteRouteDocument);
};
export const GetRoutesDocument = gql`
    query GetRoutes($limit: Int, $start: Int, $sort: [String]) {
  routes(pagination: {limit: $limit, start: $start}, sort: $sort) {
    ...RouteBasic
  }
}
    ${RouteBasicFragmentDoc}`;

export function useGetRoutesQuery(options?: Omit<Urql.UseQueryArgs<GetRoutesQueryVariables>, 'query'>) {
  return Urql.useQuery<GetRoutesQuery, GetRoutesQueryVariables>({ query: GetRoutesDocument, ...options });
};
export const GetRouteDocument = gql`
    query GetRoute($documentId: ID!) {
  route(documentId: $documentId) {
    ...RouteBasic
    createdAt
    updatedAt
  }
}
    ${RouteBasicFragmentDoc}`;

export function useGetRouteQuery(options: Omit<Urql.UseQueryArgs<GetRouteQueryVariables>, 'query'>) {
  return Urql.useQuery<GetRouteQuery, GetRouteQueryVariables>({ query: GetRouteDocument, ...options });
};
export const GetRouteByCodeDocument = gql`
    query GetRouteByCode($shortName: String!) {
  routes(filters: {short_name: {eq: $shortName}}) {
    ...RouteBasic
  }
}
    ${RouteBasicFragmentDoc}`;

export function useGetRouteByCodeQuery(options: Omit<Urql.UseQueryArgs<GetRouteByCodeQueryVariables>, 'query'>) {
  return Urql.useQuery<GetRouteByCodeQuery, GetRouteByCodeQueryVariables>({ query: GetRouteByCodeDocument, ...options });
};
export const SearchRoutesDocument = gql`
    query SearchRoutes($search: String!, $limit: Int = 10) {
  routes(
    filters: {or: [{short_name: {containsi: $search}}, {long_name: {containsi: $search}}]}
    pagination: {limit: $limit}
  ) {
    ...RouteBasic
  }
}
    ${RouteBasicFragmentDoc}`;

export function useSearchRoutesQuery(options: Omit<Urql.UseQueryArgs<SearchRoutesQueryVariables>, 'query'>) {
  return Urql.useQuery<SearchRoutesQuery, SearchRoutesQueryVariables>({ query: SearchRoutesDocument, ...options });
};