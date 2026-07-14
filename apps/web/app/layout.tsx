import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Camerino",
  description: "Il tuo camerino digitale universale: guardaroba, armocromia e virtual try-on.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="it">
      <body className="min-h-screen bg-neutral-50 text-neutral-900 antialiased">{children}</body>
    </html>
  );
}
