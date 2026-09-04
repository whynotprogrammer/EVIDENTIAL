import React from "react";

export const metadata = {
  title: "EVIDENTIAL — Forensic Intelligence & Integrity Platform",
  description: "Enterprise Forensic Investigation, Correlation & Audit System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%236366f1'><circle cx='12' cy='12' r='10'/></svg>" />
      </head>
      <body style={{ margin: 0, padding: 0, backgroundColor: "#0b0f19", color: "#f8fafc", fontFamily: "system-ui, -apple-system, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
