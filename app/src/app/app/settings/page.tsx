'use client';

import useConfig, { Config } from "@/hooks/useConfig";
import { Container, Flex, Select, Tabs } from "@mantine/core";
import { IconSettings } from "@tabler/icons-react";

export default function Settings() {
  const { theme, setTheme } = useConfig().getState();

  return (
    <Tabs variant="outline" orientation="vertical" defaultValue="appearance">
      <Tabs.List>
        <Tabs.Tab value="appearance" leftSection={<IconSettings size={12} />}>
          Appearance
        </Tabs.Tab>
      </Tabs.List>
      <Tabs.Panel value="appearance">
        <Container m="sm">
          <Flex justify="flex-start">
            <Select
              label="Theme"
              data={['light', 'dark', 'system']}
              defaultValue={theme}
              onChange={(value) => setTheme(value as Config['theme'])}
            />
          </Flex>

        </Container>
      </Tabs.Panel>
    </Tabs>
  )
}