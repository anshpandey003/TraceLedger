import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TraceLedger",
  description:
    "Evidence verification and investigation for technical and business claims.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}