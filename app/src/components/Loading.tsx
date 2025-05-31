import { Center, Container, Loader } from "@mantine/core";

export default function Loading() {
  return (
    <Container fluid>
      <Center>
        <Loader />
      </Center>
    </Container>
  );
}