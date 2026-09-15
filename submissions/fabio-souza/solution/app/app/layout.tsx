import type { Metadata } from "next"
import { Barlow, Barlow_Semi_Condensed } from "next/font/google"

import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"

const barlow = Barlow({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-barlow",
})

const barlowSemi = Barlow_Semi_Condensed({
  subsets: ["latin"],
  weight: ["500", "600"],
  variable: "--font-barlow-semi",
})

export const metadata: Metadata = {
  title: "Triagem assistida",
  description:
    "Protótipo de roteamento de tickets com filas automática, assistida e humana, testado em 7.026 tickets reais.",
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="pt-BR"
      suppressHydrationWarning
      className={`${barlow.variable} ${barlowSemi.variable} antialiased`}
    >
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  )
}
