'use client';

import { AppShell, Burger, Group, NavLink, Text } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import React from "react";
import { IconDeviceMobile, IconDeviceDesktop, IconForms, IconTreadmill, IconTrain, IconUser, IconDashboard, IconSettings, IconBuilding } from '@tabler/icons-react';

const links = [
  {
    href: "/app/dashboard",
    label: "Dashboard",
    icon: <IconDashboard size={16} stroke={1.5} />,
  },
  {
    href: "/app/desktop",
    label: "Pose Detection Live Dashboard",
    icon: <IconDeviceDesktop size={16} stroke={1.5} />,
  },
  {
    href: "/app/mobile",
    label: "Pose Detection Mobile Stream",
    icon: <IconDeviceMobile size={16} stroke={1.5} />,
  },
  {
    href: "/app/assessments",
    label: "Assessments",
    icon: <IconForms size={16} stroke={1.5} />,
  },
  {
    href: "/app/exercises",
    label: "Exercise",
    icon: <IconTreadmill size={16} stroke={1.5} />,
  },
  {
    href: "/app/trainers",
    label: "Trainers",
    icon: <IconTrain size={16} stroke={1.5} />,
  },
  {
    href: "/app/clients",
    label: "Clients",
    icon: <IconUser size={16} stroke={1.5} />,
  },
  {
    href: "/app/organisations", 
    label: "Organisations",
    icon: <IconBuilding size={16} stroke={1.5} />,
  },
];

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
          {/* <Burger opened={desktopOpened} onClick={toggleDesktop} visibleFrom="sm" size="sm" /> */}
          <Text>Gymbo AI</Text>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <AppShell.Section grow>
          {links.map((link) => (
            <NavLink
              key={link.href}
              href={link.href}
              label={link.label}
              leftSection={link.icon}
            />
          ))}
        </AppShell.Section>
        <AppShell.Section>
          <NavLink
            href="/app/settings"
            label="Settings"
            leftSection={<IconSettings size={16} stroke={1.5} />}
          />
        </AppShell.Section>
      </AppShell.Navbar>
      {children}
    </AppShell>
  );
}