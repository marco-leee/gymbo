"use client";

import { Button, Container, Paper, Stack, Title, Card, Flex, Center } from "@mantine/core";
import { IconBrandGoogle } from '@tabler/icons-react';
import Image from "next/image";
import { useAuth } from "@/context/AuthProvider";

export default function Login() {
  const { login } = useAuth();

  return (
    <Flex
      h="100vh"
      w="100vw"
      gap="0"
      justify="flex-start"
      align="flex-start"
      direction="row"
      wrap="wrap"
    >
      <Paper h="100%" w="50%" p={0} style={{ position: 'relative' }}>
        <Image 
          src="/gymbo.jpg" 
          alt="Gymbo AI" 
          fill
          style={{ objectFit: 'cover', objectPosition: 'center' }}
        />
      </Paper>
      <Paper h="100%" w="50%">
        <Container h="100%" w="100%">
          <Center h="100%" w="100%">
            <Card>
              <Title order={2} mb="lg" ta="center">
                Login
              </Title>
              <Stack>
                <Button leftSection={<IconBrandGoogle />} onClick={async () => await login('admin')}>
                  Continue with Google
                </Button>
              </Stack>
            </Card>
          </Center>
        </Container>
      </Paper>
    </Flex >
  );
}