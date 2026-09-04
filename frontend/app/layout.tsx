import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "EVIDENTIAL — AI Digital Investigation Platform",
  description: "Secure Digital Investigation, Evidence Integrity and Multilingual Case Intelligence",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0b0f19] text-slate-100 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
