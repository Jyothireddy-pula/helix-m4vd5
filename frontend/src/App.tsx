import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { VintageExplorer } from './pages/VintageExplorer'
import { DataQuality } from './pages/DataQuality'
import { DataTable } from './pages/DataTable'
import { CutoffSelector } from './components/CutoffSelector'

function Layout({ children, cutoffHour, cutoffMinute, onCutoffChange }: {
  children: React.ReactNode
  cutoffHour: number
  cutoffMinute: number
  onCutoffChange: (h: number, m: number) => void
}) {
  const navClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 text-sm rounded font-medium transition-colors ${
      isActive
        ? 'bg-blue-700 text-white'
        : 'text-blue-100 hover:bg-blue-700/50'
    }`

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-blue-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <h1 className="text-lg font-bold tracking-tight">Wind Forecast Intelligence</h1>
              <p className="text-xs text-blue-200">UK National Wind Generation · January 2026 · All times UTC</p>
            </div>
            <div className="text-xs text-blue-200 bg-blue-800 rounded px-2 py-1">
              Elexon BMRS · FUELHH + WINDFOR
            </div>
          </div>
        </div>
        {/* Nav */}
        <nav className="bg-blue-800 border-t border-blue-700">
          <div className="max-w-7xl mx-auto px-4 py-1 flex gap-1 overflow-x-auto">
            <NavLink to="/dashboard" className={navClass}>Overview</NavLink>
            <NavLink to="/vintages" className={navClass}>Vintage Explorer</NavLink>
            <NavLink to="/table" className={navClass}>Data Table</NavLink>
            <NavLink to="/quality" className={navClass}>Data Quality</NavLink>
          </div>
        </nav>
      </header>

      {/* Cutoff bar */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-2">
          <CutoffSelector
            cutoffHour={cutoffHour}
            cutoffMinute={cutoffMinute}
            onChange={onCutoffChange}
          />
        </div>
      </div>

      {/* Main content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        {children}
      </main>

      <footer className="bg-white border-t border-gray-100 text-center text-xs text-gray-400 py-3">
        Wind Forecast Intelligence · Data: Elexon BMRS (FUELHH, WINDFOR) · Analysis period: January 2026 UTC
      </footer>
    </div>
  )
}

export default function App() {
  const [cutoffHour, setCutoffHour] = useState(16)
  const [cutoffMinute, setCutoffMinute] = useState(0)

  function handleCutoffChange(h: number, m: number) {
    setCutoffHour(h)
    setCutoffMinute(m)
  }

  return (
    <BrowserRouter>
      <Layout cutoffHour={cutoffHour} cutoffMinute={cutoffMinute} onCutoffChange={handleCutoffChange}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard cutoffHour={cutoffHour} cutoffMinute={cutoffMinute} />} />
          <Route path="/vintages" element={<VintageExplorer cutoffHour={cutoffHour} cutoffMinute={cutoffMinute} />} />
          <Route path="/table" element={<DataTable cutoffHour={cutoffHour} cutoffMinute={cutoffMinute} />} />
          <Route path="/quality" element={<DataQuality />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
