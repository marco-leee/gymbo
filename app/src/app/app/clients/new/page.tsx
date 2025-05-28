"use client";

import { Box, Button, LoadingOverlay, Stack, TextInput, Title, Text } from "@mantine/core";

import { Container } from "@mantine/core";
import { Form, useForm } from "@mantine/form";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function NewClientPage() {
  const [visible, setVisible] = useState(false);
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  const form = useForm({
    mode: 'uncontrolled',
    initialValues: {
      email: '',
      first_name: '',
      last_name: '',
    },

    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
      first_name: (value) => (value.length > 0 ? null : 'First name is required'),
      last_name: (value) => (value.length > 0 ? null : 'Last name is required'),
    },
  });

  const handleSubmit = async (values: typeof form.values) => {
    setVisible(true);

    const response = await fetch('/api/v1/clients', {
      method: 'POST',
      body: JSON.stringify(values),
    });

    const data = await response.json();

    if (response.ok) {
      router.push(`/app/clients/${data.data.id}`);
    } else {
      setError(data.error);
    }

    setVisible(false);
  };

  return (
    <Container fluid>
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Title order={2}>New Client</Title>
        <Box pos="relative">
          <LoadingOverlay visible={visible} zIndex={1000} overlayProps={{ blur: 2 }} />
          <Stack gap="md">
            <TextInput label="Email" {...form.getInputProps('email')} />
            <TextInput label="First Name" {...form.getInputProps('first_name')} />
            <TextInput label="Last Name" {...form.getInputProps('last_name')} />
            {error && <Text c="red">{error}</Text>}
            <Button type="submit">Create</Button>
          </Stack>
        </Box>
      </form>
    </Container>
  );
}