"use client";

import { Gender } from "@/models";
import { Box, Button, LoadingOverlay, Stack, TextInput, Title, Text, Select } from "@mantine/core";

import { Container } from "@mantine/core";
import { Form, useForm } from "@mantine/form";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function NewExercisePage() {
  const [visible, setVisible] = useState(false);
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  const form = useForm({
    mode: 'uncontrolled',
    initialValues: {
      name: '',
      type: '',
      camera_view: '',
      client: '',
    },

    validate: {
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
        <Title order={2}>New Exercise</Title>
        <Box pos="relative">
          <LoadingOverlay visible={visible} zIndex={1000} overlayProps={{ blur: 2 }} />
          <Stack gap="md">
            <TextInput label="Name" {...form.getInputProps('email')} required />
            <TextInput label="Type" {...form.getInputProps('ty')} required />
            <TextInput label="Camera View" {...form.getInputProps('last_name')} required />
            <Select label="Client" {...form.getInputProps('gender')} data={Gender.options} required />
            <TextInput label="Height" {...form.getInputProps('height')} type="number" min={0} />
            <TextInput label="Weight" {...form.getInputProps('weight')} type="number" min={0} />
            {error && <Text c="red">{error}</Text>}
            <Button type="submit">Create</Button>
          </Stack>
        </Box>
      </form>
    </Container>
  );
}