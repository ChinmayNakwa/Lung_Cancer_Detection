import type { Metadata } from "next";
import { Playfair_Display, Inter } from "next/font/google"; // Import fonts
import "./globals.css";
import { SessionProvider } from "next-auth/react";
import Navbar from "@/components/Navbar";

// Elegant Serif for Headings
const playfair = Playfair_Display({ 
  subsets: ["latin"],
  variable: "--font-playfair"
});

// Clean Sans for UI elements (inputs, small text)
const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-inter"
});

export const metadata: Metadata = {
  title: "LungScan AI",
  description: "Advanced Lung Cancer Detection System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${playfair.variable} ${inter.variable} antialiased`}>
        <SessionProvider>
            <Navbar />
            {children}
        </SessionProvider>
      </body>
    </html>
  );
}