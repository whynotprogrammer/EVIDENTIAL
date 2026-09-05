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
    <html lang="en">
      <body className="bg-black text-ink antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
