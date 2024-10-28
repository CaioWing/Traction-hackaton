import { Box, Button } from '@mui/material';
import React, { useRef, useState } from 'react';
import styled from 'styled-components';

const CenteredDiv = styled.div`
  transform: translate(-50%, 50%);
  position: absolute;
  left: 50%;
  top: 50%;
`;

function VoiceRequest() {
  const mediaStream = useRef<MediaStream>();
  const mediaRecorder = useRef<MediaRecorder>();
  const chunks = useRef<Blob[]>([]);
  const [recordedUrl, setRecordedUrl] = useState('');
  const [transcription, setTranscription] = useState('');
  const [recording, setRecording] = useState(false);
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStream.current = stream;
      mediaRecorder.current = new MediaRecorder(stream);
      mediaRecorder.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.current.push(e.data);
        }
      };
      mediaRecorder.current.onstop = () => {
        const recordedBlob = new Blob(chunks.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(recordedBlob);
        setRecordedUrl(url);
        chunks.current = [];
        const formData = new FormData();

        formData.append('file', recordedBlob);
        fetch('http://localhost:8000/audioupload', {
          method: 'POST',
          body: formData,
        }).then((res) => {
          res.json().then((data) => {
            setTranscription(data.transcription);
          });
        });
      };
      mediaRecorder.current.start();
      setRecording(true);
      setTimeout(() => {
        mediaRecorder?.current?.stop();
        setRecording(false);
      }, 8000);
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };
  return (
    <div>
      <CenteredDiv>
        <Box sx={{ '& button': { m: 1 } }} textAlign='center'>
          <Button
            color={recording ? 'success' : 'error'}
            style={{ margin: 'auto' }}
            onClick={startRecording}
            variant='contained'
            size='large'
          >
            SOLICITAR SERVIÇO
          </Button>
        </Box>
        <h1 style={{ textAlign: 'center' }}>{transcription}</h1>
      </CenteredDiv>
    </div>
  );
}

export default VoiceRequest;
