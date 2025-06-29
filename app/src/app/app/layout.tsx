'use client';

import { AppShell, Burger, Group, NavLink, Text } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import React from "react";
import { IconDeviceMobile, IconDeviceDesktop, IconForms, IconTreadmill, IconTrain, IconUser, IconDashboard, IconSettings, IconBuilding, IconLogout, IconSwitch, IconDatabase } from '@tabler/icons-react';
import { useAuth } from "@/context/AuthProvider";
import { UserRole } from "@/types/auth";
import { canUserAccessRoute } from "@/config/auth";

const allLinks = [
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
    label: "Client Management",
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
  const { user, logout, token } = useAuth();

  // Filter links based on user role permissions
  const filteredLinks = allLinks.filter(link => {
    if (!user) return false;
    return canUserAccessRoute(token?.user_type as UserRole, link.href);
  });

  const handleLogout = () => logout();

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 300, breakpoint: 'sm', collapsed: { mobile: !mobileOpened, desktop: desktopOpened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={mobileOpened} onClick={toggleMobile} hiddenFrom="sm" size="sm" />
            <Text>Gymbo AI</Text>
          </Group>
        </Group>
      </AppShell.Header>
      
      <AppShell.Navbar p="md">
        <AppShell.Section grow>
          {filteredLinks.map((link) => (
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