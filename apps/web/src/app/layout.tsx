import type { Metadata } from "next";
import { Splash } from "@/components/brand/Splash";
import { Logo } from "@/components/brand/Logo";
import { Playfair_Display, Inter, Source_Serif_4, JetBrains_Mono } from "next/font/google";
import "../styles/globals.css";
import "../styles/logo.css";

const playfair = Playfair_Display({
  subsets: ["latin", "cyrillic"],
  variable: "--font-playfair",
  display: "swap",
  weight: ["400", "500", "600", "700", "800", "900"],
});

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
  weight: ["300", "400", "500", "600", "700"],
});

const sourceSerif = Source_Serif_4({
  subsets: ["latin", "cyrillic"],
  variable: "--font-source-serif",
  display: "swap",
  weight: ["300", "400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin", "cyrillic"],
  variable: "--font-jetbrains-mono",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "AI Ugoda — Юридична інтелектуальна платформа",
  description: "Законодавство України — зрозуміле, актуальне та пов'язане.",
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  openGraph: { siteName: "AI Ugoda", locale: "uk_UA", type: "website" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="uk"
      suppressHydrationWarning
      className={`${playfair.variable} ${inter.variable} ${sourceSerif.variable} ${jetbrainsMono.variable}`}
    >
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className="antialiased"><Splash />{children}\n<Logo variant=\"lockup\" size={80} />
    </html>
  );
}