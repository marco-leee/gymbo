"use client";

import { Gender } from "@/models";
import { Box, Button, LoadingOverlay, Stack, TextInput, Title, Text, Select, Textarea } from "@mantine/core";
import { DatePicker, DatePickerInput } from "@mantine/dates";

import { Container } from "@mantine/core";
import { Form, useForm } from "@mantine/form";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function NewAssessmentPage() {
  const [visible, setVisible] = useState(false);
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  const form = useForm({
    mode: 'uncontrolled',
    initialValues: {
      name: '',
      description: '',
      date: new Date(),
    },
    validate: {}
  });

  const handleSubmit = async (values: typeof form.values) => {
    console.log(values);
    // setVisible(true);

    // const response = await fetch('/api/v1/assessments', {
    //   method: 'POST',
    //   body: JSON.stringify(values),
    // });

    // const data = await response.json();

    // if (response.ok) {
    //   router.push(`/app/assessments/${data.data.id}`);
    // } else {
    //   setError(data.error);
    // }

    // setVisible(false);
  };

  return (
    <Container fluid>
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Title order={2}>New Assessment</Title>
        <Box pos="relative">
          <LoadingOverlay visible={visible} zIndex={1000} overlayProps={{ blur: 2 }} />
          <Stack gap="md">
            <TextInput label="Name" {...form.getInputProps('name')} required />
            <Textarea label="Description" {...form.getInputProps('description')} />
            <DatePickerInput label="Date" {...form.getInputProps('date')} required />
            {error && <Text c="red">{error}</Text>}
            <Button type="submit">Create</Button>
          </Stack>
        </Box>
      </form>
    </Container>
  );
}