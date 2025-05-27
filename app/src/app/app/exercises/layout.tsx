'use client';

import { AppShell } from "@mantine/core";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell.Main styles={{ main: { height: '100%', display: 'flex', flexDirection: 'column' } }}>
      {children}
    </AppShell.Main>
  );
}