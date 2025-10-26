// src/components/AudioPlayer.js
import React from 'react';

export default function AudioPlayer({ blob }) {
  if (!blob) return null;
  const url = URL.createObjectURL(blob);
  return (
    <audio controls src={url} style={{width:'100%'}} onEnded={() => URL.revokeObjectURL(url)} />
  );
}
