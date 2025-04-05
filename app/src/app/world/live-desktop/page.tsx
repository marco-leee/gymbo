'use client';

import { useState, useEffect, useRef } from 'react';
import { TextInput, Button, Group, Paper, Title, Container, Text, Box, Stack } from '@mantine/core';
import { useForm } from '@mantine/form';
import { io, Socket } from 'socket.io-client';

export default function Page() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [joinedRoom, setJoinedRoom] = useState('');
  const [error, setError] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
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

    socketInstance.on('pose_results', (frameData) => {
      console.log(frameData);
    });

    setSocket(socketInstance);

    // Cleanup on component unmount
    return () => {
      socketInstance.disconnect();
    };
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

  return (
    <Container size="xs" py="xl" w="100%" h="100%">
      <Paper radius="md" p="xl" withBorder>
        <Title order={2} ta="center" mt="md" mb={30}>
          Join Desktop Room
        </Title>

        {isConnected ? (
          <Text c="green" mb="md" ta="center">
            Connected to server
          </Text>
        ) : (
          <Text c="red" mb="md" ta="center">
            Disconnected from server
          </Text>
        )}
        
        {/* Connection status badges */}
        <Group justify="center" gap="xs" mb="md">
          {isConnected && (
            <Text size="sm" fw={500} c="green">●&nbsp;Connected</Text>
          )}
          {isStreaming && (
            <Text size="sm" fw={500} c="blue">●&nbsp;Streaming</Text>
          )}
        </Group>

        {error && (
          <Text c="red" mb="md" ta="center">
            {error}
          </Text>
        )}

        {joinedRoom ? (
          <>
            <Text ta="center" size="lg" mb="md">
              You joined room: <b>{joinedRoom}</b>
            </Text>
            
            {/* Video display */}
            <Box pos="relative" mx="auto" mb="xl">
              {/* Visible video element with styling */}
              <Box 
                style={{ 
                  position: 'relative',
                  width: '100%',
                  maxWidth: '100%',
                  aspectRatio: '4/3',
                  overflow: 'hidden',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                  background: '#000'
                }}
              >
                <video 
                  ref={videoRef} 
                  autoPlay 
                  playsInline 
                  muted
                  style={{ 
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover'
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
              
              {/* Hidden canvas for processing frames */}
              <canvas 
                ref={canvasRef} 
                style={{ display: 'none' }} 
              />
            </Box>
            
            <Group justify="center" mt="md">
              <Button 
                onClick={() => {
                  socket?.emit('leave_room', joinedRoom);
                  setJoinedRoom('');
                }}
                color="red"
                size="md"
                radius="md"
              >
                Leave Room
              </Button>
            </Group>
          </>
        ) : (
          <form onSubmit={handleJoinRoom}>
            <TextInput
              label="Room Name"
              placeholder="Enter room name"
              required
              {...form.getInputProps('roomName')}
            />
            
            <Group justify="center" mt="xl">
              <Button type="submit" fullWidth>
                Join Room
              </Button>
            </Group>
          </form>
        )}
      </Paper>
    </Container>
  );
}