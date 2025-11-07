# Vehicle Simulator - TODO & Progress Tracking

**Project**: ArkNet Vehicle Simulator  
**Branch**: branch-0.0.3.3  
**Date**: November 7, 2025  
**Status**: 🚀 Transitioning to Component-Driven Development (IN PROGRESS)  
**Current Phase**: Component Design & Testing

> **📌 Key Documentation**:
> - `CONTEXT.md` - Complete project context, architecture, all technical details
> - `TODO.md` - Task tracking, progress, next steps

**Execution Priority**:

## Component-Driven Development Tasks

- [ ] **Core Components**
  - [ ] Breadcrumb Navigation: Create breadcrumb navigation component for intuitive tier traversal.
  - [ ] Card Component: Design reusable card component for displaying summaries (e.g., depots, routes, vehicles, drivers).
  - [ ] Dashboard Layout: Build shared layout for all dashboards, including headers, sidebars, and content areas.
  - [ ] Table Component: Create dynamic table component for detailed data views.
  - [ ] Modal Component: Implement modal for detailed information or actions.
  - [ ] Map Component: Integrate map visualization for geospatial data.

- [ ] **Dashboard-Specific Components**
  - [ ] Country Overview Card: Display depot summaries for a country.
  - [ ] Depot Overview Card: Display route, vehicle, and driver summaries for a depot.
  - [ ] Route Detail Card: Display route-specific information (e.g., stops, schedules).
  - [ ] Vehicle Detail Card: Display vehicle-specific information (e.g., status, location).
  - [ ] Driver Detail Card: Display driver-specific information (e.g., assignments, availability).

- [ ] **Utility Components**
  - [ ] Search Bar: Add search functionality for filtering data.
  - [ ] Pagination Controls: Implement pagination for large datasets.
  - [ ] Loading Spinner: Indicate data loading states.
  - [ ] Error Boundary: Handle and display errors gracefully.

## Hierarchical Dashboard Structure

- [ ] Build Country Dashboard: Country-level dashboard view with depot overview cards.
- [ ] Build Depot Dashboard: Depot-level dashboard with routes, vehicles, and drivers breakdown.
- [ ] Build Detail Dashboards: Route/Vehicle/Driver detail dashboards with full state information.
- [ ] Setup Hierarchical State Management: Implement state management for drill-down context (Zustand).
- [ ] Create Reusable Tier Components: Create reusable card components for each tier level.

## TODO List

- [-] Design Hierarchical Dashboard Structure
  - Design and implement hierarchical navigation structure: Country -> Depots -> Routes/Vehicles/Drivers with drill-down capability
- [ ] Implement Breadcrumb Navigation
  - Create breadcrumb navigation component for intuitive tier traversal
- [ ] Build Country Dashboard
  - Build Country-level dashboard view with depot overview cards
- [ ] Build Depot Dashboard
  - Build Depot-level dashboard with routes, vehicles, and drivers breakdown
- [ ] Build Detail Dashboards
  - Build Route/Vehicle/Driver detail dashboards with full state information
- [ ] Setup Hierarchical State Management
  - Implement state management for drill-down context (Zustand)
- [ ] Create Reusable Tier Components
  - Create reusable card components for each tier level
- [ ] Implement TelemetryDataProvider
  - Create a provider to connect to gpscentcom_server for telemetry data.
  - Implement methods: subscribeToTelemetry, getTelemetryData, disconnectTelemetry.
  - Ensure secure connection and caching of telemetry data.
- [ ] Implement GraphQLDataProvider
  - Create a provider to interact with Strapi via GraphQL.
  - Implement methods: getVehicles, getRoutes, getDepots, updateVehicle, updateRoute.
  - Ensure secure and efficient data fetching.
- [ ] Test DataProviders
  - Write unit tests for TelemetryDataProvider.
  - Write unit tests for GraphQLDataProvider.
  - Test integration of both providers with the application.
