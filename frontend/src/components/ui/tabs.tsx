"use client"

import * as React from "react"

type TabsContextType = {
  value: string
  onValueChange: (value: string) => void
}

const TabsContext = React.createContext<TabsContextType | null>(null)

function Tabs({ 
  defaultValue = "", 
  children,
  className = ""
}: { 
  defaultValue?: string
  children: React.ReactNode
  className?: string
}) {
  const [value, setValue] = React.useState(defaultValue)
  
  return (
    <TabsContext.Provider value={{ value, onValueChange: setValue }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

function TabsList({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 ${className}`}>
      {children}
    </div>
  )
}

function TabsTrigger({ 
  value, 
  children, 
  className = "" 
}: { 
  value: string
  children: React.ReactNode
  className?: string
}) {
  const context = React.useContext(TabsContext)
  if (!context) return null
  
  const isActive = context.value === value
  
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all ${
        isActive ? 'bg-white text-gray-950 shadow-sm' : ''
      } ${className}`}
      onClick={() => context.onValueChange(value)}
    >
      {children}
    </button>
  )
}

function TabsContent({ 
  value, 
  children, 
  className = "" 
}: { 
  value: string
  children: React.ReactNode
  className?: string
}) {
  const context = React.useContext(TabsContext)
  if (!context) return null
  
  if (context.value !== value) return null
  
  return <div className={`mt-2 ${className}`}>{children}</div>
}

export { Tabs, TabsList, TabsTrigger, TabsContent }
