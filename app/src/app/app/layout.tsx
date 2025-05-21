'use client';

import { AppShell, Burger, Group, NavLink } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import React from "react";
import { IconDeviceMobile, IconDeviceDesktop } from '@tabler/icons-react';

export default function Layout({ children }: { children: React.ReactNode }) {
  const [mobileOpened, { toggle: toggleMobile }] = useDisclosure();
  const [desktopOpened, { toggle: toggleDesktop }] = useDisclosure();

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 300, breakpoint: 'sm', collapsed: { mobile: !mobileOpened, desktop: desktopOpened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger opened={mobileOpened} onClick={toggleMobile} hiddenFrom="sm" size="sm" />
          <Burger opened={desktopOpened} onClick={toggleDesktop} visibleFrom="sm" size="sm" />
          Gymbo AI
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <NavLink
          href="/app/desktop"
          label="Pose Detection Live Dashboard"
          leftSection={<IconDeviceDesktop size={16} stroke={1.5} />}
        />
        <NavLink
          href="/app/mobile"
          label="Pose Detection Mobile Stream"
          leftSection={<IconDeviceMobile size={16} stroke={1.5} />}
        />
      </AppShell.Navbar>
      <AppShell.Main styles={{ main: { display: 'flex', justifyContent: 'center', alignItems: 'center' } }}>
        {children}
      </AppShell.Main>
    </AppShell>
  );
}