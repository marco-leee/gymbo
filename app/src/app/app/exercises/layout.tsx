'use client';

import { AppShell } from "@mantine/core";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell.Main>
      {children}
    </AppShell.Main>
  );
}