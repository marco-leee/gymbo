"use client";

import { createOrganisation } from "@/services";
import { Box, Button, Container, LoadingOverlay, Stack, Text, TextInput, Title } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function NewOrganisation() {
  const [visible, setVisible] = useState(false);
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  const form = useForm({
    mode: 'uncontrolled',
    initialValues: {
      name: '',
      email: '',
      address: '',
      phone: '',
      logo: '',
      website: '',
    },

    validate: {
    },
  });

  const handleSubmit = async (values: typeof form.values) => {
    setVisible(true);
    try {
      const response = await createOrganisation({
        $typeName: 'shared.entities.v1.Organisation',
        id: '',
        name: values.name,
        email: values.email,
        address: values.address,
        phone: values.phone,
        logo: values.logo,
        website: values.website,
        createdAt: {
          $typeName: 'google.protobuf.Timestamp',
          seconds: BigInt(Math.floor(Date.now() / 1000)),
          nanos: 0,
        },
        updatedAt: {
          $typeName: 'google.protobuf.Timestamp',
          seconds: BigInt(Math.floor(Date.now() / 1000)),
          nanos: 0,
        },
        deletedAt: undefined,
      });

    if (response.organisation?.id) {
      router.push(`/app/organisations/${response.organisation.id}`);
    }
  } catch (err) {
    setError(err instanceof Error ? err.message : 'An error occurred');
  } finally {
    setVisible(false);
  }
};

return (
  <Container fluid>
    <form onSubmit={form.onSubmit(handleSubmit)}>
      <Title order={2}>New Organisation</Title>
      <Box pos="relative">
        <LoadingOverlay visible={visible} zIndex={1000} overlayProps={{ blur: 2 }} />
        <Stack gap="md">
          <TextInput label="Name" {...form.getInputProps('name')} required />
          <TextInput label="Email" {...form.getInputProps('email')} required />
          <TextInput label="Address" {...form.getInputProps('address')} required />
          <TextInput label="Phone" {...form.getInputProps('phone')} required />
          {/* <TextInput label="Logo" {...form.getInputProps('logo')} required />
            <TextInput label="Website" {...form.getInputProps('website')} required /> */}
          {error && <Text c="red">{error}</Text>}
          <Button type="submit">Create</Button>
        </Stack>
      </Box>
    </form>
  </Container>
);
}