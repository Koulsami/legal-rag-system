import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Myk Raws Legal AI',
  description: 'Singapore Statutory Interpretation Assistant',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}
