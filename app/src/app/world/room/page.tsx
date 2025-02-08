'use client';

import {
  Chat,
  ControlBar,
  GridLayout,
  LiveKitRoom,
  ParticipantTile,
  RoomAudioRenderer,
  useTracks,
} from '@livekit/components-react';

import '@livekit/components-styles';

import { useEffect, useState } from 'react';
import { Track } from 'livekit-client';

export default function Page() {
  // TODO: get user input for room and name
  const room = 'quickstart-room';
  const name = 'quickstart-user';
  const [wsUrl, setWsUrl] = useState('');
  const [token, setToken] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const resp = await fetch(`/api/token?room=${room}&username=${name}`);
        const data = await resp.json();
        setWsUrl(data.wsUrl);
        setToken(data.token);
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  if (!token && !wsUrl) {
    return <div>Getting token...</div>;
  }

  return (
    <LiveKitRoom
      video={true}
      audio={true}
      token={token}
      serverUrl={wsUrl}
      // Use the default LiveKit theme for nice styles.
      data-lk-theme="default"
      style={{ height: '100%' }}
    >
      {/* Your custom component with basic video conferencing functionality. */}
      <MyVideoConference />
      {/* The RoomAudioRenderer takes care of room-wide audio for you. */}
      <RoomAudioRenderer />
      {/* Controls for the user to start/stop audio, video, and screen
      share tracks and to leave the room. */}
      <ControlBar />
    </LiveKitRoom>
  );
}

function MyVideoConference() {
  // `useTracks` returns all camera and screen share tracks. If a user
  // joins without a published camera track, a placeholder track is returned.
  const tracks = useTracks(
    [
      { source: Track.Source.Camera, withPlaceholder: true },
      { source: Track.Source.ScreenShare, withPlaceholder: false },
    ],
    { onlySubscribed: false },
  );
  return (
    <GridLayout tracks={tracks} style={{ height: 'calc(100vh - var(--app-shell-header-height))', width: '100%' }}>
      {/* The GridLayout accepts zero or one child. The child is used
      as a template to render all passed in tracks. */}
      <ParticipantTile />
    </GridLayout>
  );
}