import { createContext, useContext, useEffect, useState } from 'react'
import { metaApi } from '../api/services'

// Dropdown values come from the backend so frontend and API validation never drift apart.
const FALLBACK = {
  appliance_categories: [], usage_frequencies: [], conditions: [], risk_levels: ['Low', 'Medium', 'High', 'Critical'],
  severities: [], maintenance_types: [], schedule_statuses: [], issue_statuses: [], problem_categories: [], expense_types: [],
}
const OptionsContext = createContext(FALLBACK)

export function OptionsProvider({ children }) {
  const [opts, setOpts] = useState(FALLBACK)
  useEffect(() => { metaApi.options().then(setOpts).catch(() => {}) }, [])
  return <OptionsContext.Provider value={opts}>{children}</OptionsContext.Provider>
}

export const useOptions = () => useContext(OptionsContext)
