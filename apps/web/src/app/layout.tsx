import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Camerino",
  description:
    "Import garments from any online store into one wardrobe, discover your seasonal color palette, and try outfits on before you buy.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-neutral-50 text-neutral-900 antialiased">
        {children}
      </body>
    </html>
  );
}
