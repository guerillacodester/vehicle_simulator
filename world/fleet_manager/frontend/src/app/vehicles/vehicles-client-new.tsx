// This file has been deprecated in favor of vehicles-client.tsx
// All mock data has been removed and replaced with real database integration

export default function DeprecatedVehiclesClient() {
  return (
    <div className="p-8 text-center">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Component Deprecated
      </h2>
      <p className="text-gray-600 dark:text-gray-400">
        This component has been replaced with the main vehicles-client.tsx 
        which uses real database data instead of mock data.
      </p>
    </div>
  )
}
