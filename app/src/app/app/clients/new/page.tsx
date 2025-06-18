"use client";

import { createClient } from "@/gen/web/gateways/admin/v1/admin_gateway-AdminGatewayService_connectquery";
import { Client_Gender, Client_GenderSchema } from "@/gen/web/shared/entities/v1/client_pb";
import { AdminGatewayClientService } from "@/services/Client";
import { formatLabel } from "@/utils/string";
import { Box, Button, LoadingOverlay, Stack, TextInput, Title, Text, Select, Notification } from "@mantine/core";

import { Container } from "@mantine/core";
import { Form, useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
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
      full_name: '',
      first_name: '',
      last_name: '',
      gender: '',
      height: '',
      weight: '',
    },

    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
      full_name: (value) => (value.length > 0 ? null : 'Full name is required'),
    },
  });

  const handleSubmit = async (values: typeof form.values) => {
    setVisible(true);

    try {
      const response = await AdminGatewayClientService.createClient({
        $typeName: 'shared.entities.v1.Client',
        id: '',
        email: values.email,
        fullName: values.full_name,
        firstName: values.first_name,
        lastName: values.last_name,
        gender: values.gender,
        height: values.height ? {
          $typeName: 'shared.entities.v1.Client.Height',
          value: Number(values.height),
          unit: "cm",
        } : undefined,
        weight: values.weight ? {
          $typeName: 'shared.entities.v1.Client.Weight',
          value: Number(values.weight),
          unit: "kg",
        } : undefined,
      });

      notifications.show({
        title: 'Client created',
        message: `Client ${response.client?.email} created`,
        color: 'green',
      });

      if (response.client?.id) {
        router.push(`/app/clients/${response.client.id}`);
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setVisible(false);
    }

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
            <TextInput label="Email" {...form.getInputProps('email')} required />
            <TextInput label="Full Name" {...form.getInputProps('full_name')} required />
            <TextInput label="First Name" {...form.getInputProps('first_name')} />
            <TextInput label="Last Name" {...form.getInputProps('last_name')} />
            <Select label="Gender" {...form.getInputProps('gender')} data={Client_GenderSchema.values.map(value => ({ label: formatLabel(value.localName), value: value.localName }))} required />
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