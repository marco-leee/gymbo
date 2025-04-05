'use client';

import { AppShell, Burger, Group, NavLink, Skeleton } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import Link from "next/link";
import React from "react";
import { IconDeviceMobile, IconDeviceDesktop } from '@tabler/icons-react';

export default function Layout({ children }: { children: React.ReactNode }) {
  const [mobileOpened, { toggle: toggleMobile }] = useDisclosure();
  const [desktopOpened, { toggle: toggleDesktop }] = useDisclosure();

  return (
    <AppShell
      header={{ height: 60 }}
      footer={{ height: 60 }}
      navbar={{ width: 300, breakpoint: 'sm', collapsed: { mobile: !mobileOpened, desktop: desktopOpened } }}
      aside={{ width: 300, breakpoint: 'md', collapsed: { desktop: false, mobile: true } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger opened={mobileOpened} onClick={toggleMobile} hiddenFrom="sm" size="sm" />
          <Burger opened={desktopOpened} onClick={toggleDesktop} visibleFrom="sm" size="sm" />
          Header
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <NavLink
          href="/world/live-desktop"
          label="Desktop Only"
          leftSection={<IconDeviceDesktop size={16} stroke={1.5} />}
        />
        <NavLink
          href="/world/live-mobile"
          label="Mobile Only"
          leftSection={<IconDeviceMobile size={16} stroke={1.5} />}
        />
      </AppShell.Navbar>
      <AppShell.Main>
        {children}
      </AppShell.Main>
      {/* <AppShell.Aside p="md">Aside</AppShell.Aside>
      <AppShell.Footer p="md">Footer</AppShell.Footer> */}
    </AppShell>
  );
}