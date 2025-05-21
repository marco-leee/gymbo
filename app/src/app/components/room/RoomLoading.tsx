import { Stack, Text, Loader } from "@mantine/core";
import { IconChecks } from "@tabler/icons-react";

export type RoomLoadingProps = {
  error: string;
  isConnected: boolean;
}

export default function RoomLoading({ error, isConnected }: RoomLoadingProps) {
  return (
    <Stack align='center' gap="md">
      {isConnected && (
        <IconChecks color="green" size={100} />
      )}

      {!isConnected && (
        <Loader color="blue" />
      )}

      {error && (
        <>
          <Text c="blue" ta="center">
            Retrying to connect, no action needed. Please wait...
          </Text>
        </>
      )}

      {!isConnected && !error && (
        <Text c="blue" ta="center">
          Connecting to server
        </Text>
      )}

      {isConnected && !error && (
        <Text c="green" ta="center">
          Connected to server
        </Text>
      )}
    </Stack>
  )
}