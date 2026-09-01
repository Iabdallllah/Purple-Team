import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'Purple Platform - Autonomous Purple Teaming',
  description: 'Continuous security validation through adversarial AI agents',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} antialiased dark`}>
      <body className="min-h-screen bg-dark-50 dark:bg-dark-950">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}