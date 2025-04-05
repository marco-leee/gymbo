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
  const [videoReady, setVideoReady] = useState(false);
  
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
      stopStreaming();
    });

    socketInstance.on('connect_error', (err) => {
      setError(`Connection error: ${err.message}`);
    });

    socketInstance.on('room_joined', ({ message, room_id, sid }) => {
      setJoinedRoom(room_id);
      setError('');

      socketInstance.emit('start_stream', room_id);
    });

    socketInstance.on('stream_ready', () => {
      console.log('Stream ready');
    
      // Start webcam stream
      startWebcamStream(socketInstance);
    });

    setSocket(socketInstance);

    // Cleanup on component unmount
    return () => {
      socketInstance.disconnect();
      stopStreaming();
    };
  }, []);

  const startWebcamStream = async (socketInstance: Socket) => {
    try {
      // Request camera access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment', // Use back camera for better streaming
          width: { ideal: 640 },
          height: { ideal: 480 }
        } 
      });
      
      // Save stream reference
      streamRef.current = stream;
      
      // Connect stream to video element
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      
      // Initialize canvas
      const canvas = canvasRef.current;
      const video = videoRef.current;
      
      if (!canvas || !video) {
        throw new Error("Video or canvas element not found");
      }
      
      // Set canvas dimensions
      canvas.width = 640;
      canvas.height = 480;
      
      // Start sending frames
      setIsStreaming(true);
      setVideoReady(true);
      
      // Frame interval is now managed by useEffect
      
    } catch (err) {
      setError(`Camera access error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      console.error('Error accessing camera:', err);
    }
  };
  
  // Use useEffect to manage the frame interval
  useEffect(() => {
    // Only start the interval if we're streaming and the video is ready
    if (isStreaming && videoReady && socket && joinedRoom && videoRef.current && canvasRef.current) {
      // Clear any existing interval first
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
      }
      
      // Set up new interval
      frameIntervalRef.current = setInterval(() => {
        sendVideoFrame(canvasRef.current!, videoRef.current!, socket);
      }, 100);
      
      // Clean up function
      return () => {
        if (frameIntervalRef.current) {
          clearInterval(frameIntervalRef.current);
          frameIntervalRef.current = null;
        }
      };
    }
    
    // If we're not streaming anymore, clear the interval
    return () => {
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
        frameIntervalRef.current = null;
      }
    };
  }, [isStreaming, videoReady, socket, joinedRoom]); // Dependencies that should trigger interval restart
  
  const sendVideoFrame = (
    canvas: HTMLCanvasElement, 
    video: HTMLVideoElement, 
    socketInstance: Socket
  ) => {
    try {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      // Draw the current video frame to canvas
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Convert canvas to blob instead of data URL
      canvas.toBlob(
        (blob) => {
          if (!blob) return;
          
          // Create a new FileReader to convert blob to ArrayBuffer
          const reader = new FileReader();
          
          reader.onload = function() {
            if (!reader.result) return;
            
            // Send binary frame data to server
            socketInstance.emit('video_frame', {
              room_id: joinedRoom,
              frame: reader.result,
              // Add dimensions to help server with reshaping
              dimensions: {
                width: canvas.width,
                height: canvas.height,
                format: 'jpeg'
              }
            });
          };
          
          // Read the blob as ArrayBuffer
          reader.readAsArrayBuffer(blob);
        },
        'image/jpeg',
        0.6  // Reduced quality to 60% for faster transmission
      );
      
    } catch (err) {
      console.error('Error sending video frame:', err);
    }
  };
  
  const stopStreaming = () => {
    // The interval clearing is now handled by the useEffect
    // Just need to stop the stream tracks and update state
    
    // Stop all tracks in the stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    setIsStreaming(false);
    setVideoReady(false);
  };

  const handleJoinRoom = form.onSubmit((values) => {
    if (!socket) return;
    setError('');
    
    try {
      socket.emit('join_room', values.roomName, 'mobile');
    } catch (err) {
      setError(`Failed to join room: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  });

  return (
    <Container size="xs" py="xl" w="100%" h="100%">
      <Paper radius="md" p="xl" withBorder>
        <Title order={2} ta="center" mt="md" mb={30}>
          Join Mobile Room
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
                  stopStreaming();
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