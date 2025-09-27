import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { NotebookLayout } from "@/components/layout/NotebookLayout";
import { SupabaseProvider } from "@/components/providers/SupabaseProvider";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Paperclip - Transform Research Papers into Videos",
  description: "AI-powered platform to extract insights from research papers and generate engaging video content",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}
      >
        <SupabaseProvider>
          <NotebookLayout>
            {children}
          </NotebookLayout>
        </SupabaseProvider>
      </body>
    </html>
  );
}
