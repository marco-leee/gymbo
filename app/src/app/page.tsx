"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader, Center, Text, Stack } from '@mantine/core';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const timer = setTimeout(() => {
      router.push("/app/desktop");
    }, 3000);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <Center h="100vh">
      <Stack align="center" gap="md">
        <Loader size="md" />
        <Text>Welcome to Gymbo AI</Text>
        <Text>Redirecting to app in 3 seconds...</Text>
      </Stack>
    </Center>
  );
}
