'use client';

import { useState, useEffect, useRef } from 'react';
import { TextInput, Button, Group, Paper, Title, Container, Text, Box, Stack, Loader, Center, Flex, Grid, Select, Image as MantineImage, Card, Badge, List, CardSection, AspectRatio } from '@mantine/core';
import { useForm } from '@mantine/form';
import { io, Socket } from 'socket.io-client';
import { LineChart } from '@mantine/charts';
import RoomLoading from '@/app/components/room/RoomLoading';

export default function Page() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [joinedRoom, setJoinedRoom] = useState('');
  const [error, setError] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [chartData, setChartData] = useState<Array<{ time: string } & Record<string, number>>>([]);
  const [availableFields, setAvailableFields] = useState<string[]>([]);


  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const form = useForm({
    initialValues: {
      roomName: '',
    },
    validate: {
      roomName: (value) => (value.trim().length > 0 ? null : 'Room name is required'),
    },
  });

  useEffect(() => {
    // Initialize Socket.IO connection
    const socketInstance = io(process.env.NEXT_PUBLIC_SOCKET_SERVER_URL || 'http://localhost:10000/pose-detection', {
      transports: ['websocket'],
    });

    socketInstance.on('connect', () => {
      console.log('Connected to socket server');
      setIsConnected(true);
      setError('');
    });

    socketInstance.on('disconnect', () => {
      setIsConnected(false);
      setJoinedRoom('');
    });

    socketInstance.on('connect_error', (err) => {
      setError(`Connection error: ${err.message}`);
    });

    socketInstance.on('room_joined', ({ message, room_id, sid, type }) => {
      console.log(message, room_id, sid, type);
      setJoinedRoom(room_id);
      setError('');
    });

    socketInstance.on('pose_results', (data) => {
      setIsStreaming(true);
      const { time, annotated_image, dimensions, key_interest_points_2d } = data;

      const timeStr = new Date(time).toLocaleTimeString();
      const newDataPoint: Record<string, number | string> = { time: timeStr };

      Object.entries(key_interest_points_2d).forEach(([key, value]) => {
        console.log('Key:', key, 'Value:', value, 'Type:', typeof value);
        newDataPoint[key] = (value as { angle: number }).angle;
      });

      // Handle key interest points
      const fields = Object.keys(key_interest_points_2d).filter(key => key !== 'time');
      setAvailableFields(prev => {
        const newFields = [...new Set([...prev, ...fields])];
        return newFields;
      });

      // Update chart data
      setChartData(prev => {
        const newData = [...prev, newDataPoint as { time: string } & Record<string, number>];
        // Keep only last 20 data points to prevent performance issues
        return newData.slice(-20);
      });

      // Create a blob from the array buffer
      const blob = new Blob([annotated_image], { type: `image/${dimensions.format}` });

      const reader = new FileReader();
      reader.onload = () => {
        console.log('Image URL:', reader.result);

        const img = new Image();

        img.src = reader.result as string;

        img.onload = () => {
          console.log('Image loaded, dimensions:', img.width, 'x', img.height);

          // Get the canvas context
          const canvas = canvasRef.current;
          if (!canvas) {
            console.error('Canvas element not found');
            return;
          }

          // Set canvas dimensions to match the image
          canvas.width = dimensions.width;
          canvas.height = dimensions.height;
          console.log('Canvas dimensions set to:', canvas.width, 'x', canvas.height);

          // // Draw the image on the canvas
          const ctx = canvas.getContext('2d');
          if (!ctx) {
            console.error('Could not get canvas context');
            return;
          }

          // Clear the canvas first
          ctx.clearRect(0, 0, canvas.width, canvas.height);

          // Draw the image
          ctx.drawImage(img, 0, 0, dimensions.width, dimensions.height);
          // console.log('Image drawn to canvas');

          // // Clean up the object URL to prevent memory leaks
          URL.revokeObjectURL(reader.result as string);
        };

        img.onerror = (error) => {
          console.error('Error loading image:', error);
          URL.revokeObjectURL(reader.result as string);
        };
      };
      reader.readAsDataURL(blob);
    });
    setSocket(socketInstance);

    // Cleanup on component unmount
    return () => {
      socketInstance.disconnect();
    };
  }, []);

  // Initialize canvas with default size and color
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Set default dimensions
    canvas.width = 640;
    canvas.height = 480;

    // Draw a placeholder
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Fill with a dark gray color
    ctx.fillStyle = '#333333';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Add text
    ctx.fillStyle = 'white';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Waiting for pose detection...', canvas.width / 2, canvas.height / 2);

    console.log('Canvas initialized with default size and color');
  }, []);

  const handleJoinRoom = form.onSubmit((values) => {
    if (!socket) return;
    setError('');

    try {
      socket.emit('join_room', values.roomName, 'desktop');
    } catch (err) {
      setError(`Failed to join room: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  });

  const handleSelectChange = (value: string | null) => {
    if (!value) return;

    socket?.emit('set_exercise', value);
    setChartData([]);
    setAvailableFields([]);
  }

  const series = availableFields.map((field, index) => ({
    name: field,
    color: `blue.${(index + 1) * 2}`,
  }));

  if (!isConnected || !joinedRoom) {
    return (
      <form onSubmit={handleJoinRoom}>
        <Card shadow="sm" padding="lg" radius="md" withBorder >
          <Card.Section>
            <MantineImage
              src="https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=900&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8d29ya291dHxlbnwwfHwwfHx8MA%3D%3D"
              height={320}
              alt="Norway"
            />
          </Card.Section>

          <Stack>
            <Group justify="space-between" mt="md" mb="xs">
              <Text fw={500}>Pose Detection Live Dashboard</Text>
              <Badge color={isConnected ? "green" : "red"}>{isConnected ? "Connected" : "Disconnected"}</Badge>
            </Group>

            {!isConnected && !joinedRoom && (
              <RoomLoading error={error} isConnected={isConnected} isStreaming={isStreaming} />
            )}

            {isConnected && !joinedRoom && (
              <>
                <List type="ordered" size="sm" c="dimmed">
                  <List.Item>
                    <Text>Setup your mobile</Text>
                  </List.Item>
                  <List.Item>
                    <Text>Visit the mobile page and create a Room</Text>
                  </List.Item>
                  <List.Item>
                    <Text>Visit this page on your desktop</Text>
                  </List.Item>
                  <List.Item>
                    <Text>Enter the Room ID and click Join Room</Text>
                  </List.Item>
                  <List.Item>
                    <Text>Start the workout and see the results!</Text>
                  </List.Item>
                </List>
                <TextInput
                  label="Room Name"
                  placeholder="Enter room name"
                  required
                  {...form.getInputProps('roomName')}
                />
                <Button color="blue" fullWidth mt="md" radius="md">
                  Join Room
                </Button>
              </>
            )}
          </Stack>
        </Card>
      </form>
    )
  }

  return (
    <Container w="100%" h="100%" maw="100%" mah="100%" p={0}>
      <Stack justify="space-between" gap="md">
        <Stack gap="xs">
          <Group justify="center" gap="xs">
            <Text ta="center" size="lg">
              Room ID: <b>{joinedRoom}</b>
            </Text>
            {isConnected && (
              <Badge color="green">Connected</Badge>
            )}
            {isStreaming && (
              <Badge color="blue">Streaming</Badge>
            )}
          </Group>

          {error && (
            <Text c="red" ta="center">
              {error}
            </Text>
          )}

          <Select
            label="Select an exercise type"
            data={["SQUAT", "PUSH_UP"]}
            onChange={handleSelectChange}
          />

          <LineChart
            h={300}
            w="100%"
            data={chartData}
            dataKey="time"
            withLegend
            legendProps={{ verticalAlign: 'bottom', height: 50 }}
            series={series}
          />
        </Stack>


        <AspectRatio ratio={9 / 16} maw={"50%"} mah={"50%"}>
          <Box pos="relative" mx="auto" style={{ flex: 1 }}>
            {/* Canvas element with styling */}
            <Box
              style={{
                position: 'relative',
                width: '100%',
                height: '100%',
                maxWidth: '100%',
                aspectRatio: '4/3',
                overflow: 'hidden',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                background: '#000'
              }}
            >
              <canvas
                ref={canvasRef}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  display: 'block'
                }}
              />

              {isStreaming && (
                <Box
                  style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    background: 'rgba(0,0,0,0.5)',
                    color: 'white',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px'
                  }}
                >
                  LIVE
                </Box>
              )}
            </Box>
          </Box>
        </AspectRatio>


        <Button
          onClick={() => {
            socket?.emit('leave_room', joinedRoom);
            setJoinedRoom('');
          }}
          color="red"
          size="md"
          radius="md"
          w="100%"
        >
          Leave Room
        </Button>
      </Stack>
    </Container>
  );
}