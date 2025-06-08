"use client";

import { useSession } from "@/context/SessionProvider";
import { Button, Container, Paper, PasswordInput, Stack, TextInput, Title } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Login() {
  const router = useRouter();
  const { session, signIn } = useSession();
  const form = useForm({
    initialValues: {
      email: "",
      password: "",
    },
    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : "Invalid email"),
      password: (value) => (value.length < 6 ? "Password must be at least 6 characters" : null),
    },
  });

  useEffect(() => {
    if (session) {
      router.push("/app/dashboard");
    }
  }, [session, router]);

  const handleSubmit = async (values: typeof form.values) => {
    try {
      await signIn(values.email, values.password);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <Container size="xs" h="100vh" style={{ display: "flex", alignItems: "center" }}>
      <Paper radius="md" p="xl" withBorder style={{ width: "100%" }}>
        <Title order={2} mb="md" ta="center">
          Gymbo AI Login
        </Title>

        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack>
            <TextInput
              required
              label="Email"
              placeholder="your@email.com"
              {...form.getInputProps("email")}
            />

            <PasswordInput
              required
              label="Password"
              placeholder="Your password"
              {...form.getInputProps("password")}
            />

            <Button type="submit" fullWidth mt="xl">
              Sign in
            </Button>
          </Stack>
        </form>
      </Paper>
    </Container>
  );
}