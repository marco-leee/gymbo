'use client';

import { Geist, Geist_Mono } from "next/font/google";
import '@mantine/core/styles.css';
import '@mantine/charts/styles.css';
import '@mantine/dates/styles.css';
import { createTheme, MantineProvider } from "@mantine/core";
import { ConfigProvider } from "@/hooks/useConfig";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SessionProvider } from "@/context/SessionProvider";
import { TransportProvider } from '@connectrpc/connect-query';
import { transport } from "@/services/shared";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const customTheme = createTheme({
  fontFamily: 'Inter, sans-serif',
  primaryColor: 'blue',
  primaryShade: 6,
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const queryClient = new QueryClient();
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        {/* <ColorSchemeScript /> */}
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <MantineProvider defaultColorScheme="light" theme={customTheme}>
          <SessionProvider>
            <ConfigProvider>
              <TransportProvider transport={transport}>
                <QueryClientProvider client={queryClient}>
                  {children}
                </QueryClientProvider>
              </TransportProvider>
            </ConfigProvider>
          </SessionProvider>
        </MantineProvider>
      </body>
    </html>
  );
}
