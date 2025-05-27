'use client';

import { AppShell } from "@mantine/core";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell.Main styles={{ main: { display: 'flex', justifyContent: 'center', alignItems: 'center' } }}>
      {children}
    </AppShell.Main>
  );
}