import type { Metadata, Viewport } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { ThemeProvider } from "@/components/layouts/theme-provider";
import { QueryProvider } from "@/components/layouts/query-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Career Intelligence Platform",
    template: "%s | Career Intelligence Platform",
  },
  description:
    "AI-powered career guidance through behavioral analysis, psychometric assessment, and intelligent recommendations.",
  keywords: [
    "career",
    "AI",
    "psychometric",
    "career guidance",
    "personality assessment",
  ],
  authors: [{ name: "Career Intelligence Platform" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    title: "Career Intelligence Platform",
    description:
      "AI-powered career guidance through behavioral analysis and intelligent recommendations.",
    siteName: "Career Intelligence Platform",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "white" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0f" },
  ],
  width: "device-width",
  initialScale: 1,
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html
      lang="en"
      className={`${GeistSans.variable} ${GeistMono.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-screen bg-background font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            {children}
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
