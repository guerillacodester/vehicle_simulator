/**
 * IMPORT DATA PAGE - Data Import and Migration (App Router)
 */

import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Import Data',
  description: 'Import and migrate fleet management data'
}

export default function ImportPage() {
  return (
    <main className="main-content">
      <div className="page-header">
        <h1 className="text-3xl font-bold text-gray-900">Data Import</h1>
        <p className="text-gray-600">Import and migrate fleet management data</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-medium text-gray-900">Import Options</h2>
            <div className="flex space-x-2">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                Upload File
              </button>
              <button className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                Import History
              </button>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            <div className="border border-gray-200 rounded-lg p-6 hover:border-blue-300 cursor-pointer">
              <div className="text-center">
                <div className="text-blue-500 mb-4">
                  <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Vehicle Data</h3>
                <p className="text-sm text-gray-500">Import vehicle information from CSV, Excel, or JSON files</p>
              </div>
            </div>
            
            <div className="border border-gray-200 rounded-lg p-6 hover:border-blue-300 cursor-pointer">
              <div className="text-center">
                <div className="text-green-500 mb-4">
                  <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Driver Data</h3>
                <p className="text-sm text-gray-500">Import driver records and license information</p>
              </div>
            </div>
            
            <div className="border border-gray-200 rounded-lg p-6 hover:border-blue-300 cursor-pointer">
              <div className="text-center">
                <div className="text-purple-500 mb-4">
                  <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m-6 3l6-3" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Route Data</h3>
                <p className="text-sm text-gray-500">Import route information and stop data</p>
              </div>
            </div>
          </div>
          
          <div className="text-center py-8">
            <div className="text-gray-500 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Import Tools Coming Soon</h3>
            <p className="text-gray-500 mb-4">Drag-and-drop file upload and batch import functionality will be available soon</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Supported Formats</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• CSV Files</li>
                  <li>• Excel Spreadsheets</li>
                  <li>• JSON Data</li>
                  <li>• GTFS Feeds</li>
                </ul>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-medium text-green-900 mb-2">Current Data</h4>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>
                    <Link href="/vehicles" className="hover:underline">• 4 Vehicles Loaded</Link>
                  </li>
                  <li>
                    <Link href="/drivers" className="hover:underline">• 4 Drivers Loaded</Link>
                  </li>
                  <li>• Real API Connected</li>
                  <li>• Database Integrated</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
