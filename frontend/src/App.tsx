import { useState, useRef, useEffect, useCallback } from 'react';
import styles from './App.module.css';
import { Header } from './components/Header';
import { RecordButton } from './components/RecordButton';
import { UploadZone } from './components/UploadZone';
import { TextInputZone } from './components/TextInputZone';
import { SettingsPanel } from './components/SettingsPanel';
import { TranscriptionResults } from './components/TranscriptionResults';
import { ErrorMessage } from './components/ErrorMessage';
import MindMapViewer from './components/MindMapViewer'; // <--- Import New Component

// --- Interfaces ---
interface TranscriptionResponse {
  success: boolean;
  text?: string;
  error?: string;
}

interface CleanResponse {
  success: boolean;
  text?: string;
}

interface SystemPromptResponse {
  default_prompt: string;
}

// New Interface for Mind Map API
interface MindMapResponse {
  status: string;
  json: any;
  mermaid: string;
  transcript: string;
}

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [rawText, setRawText] = useState<string | null>(null);
  const [cleanedText, setCleanedText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [useLLM, setUseLLM] = useState(true);
  const [isCopied, setIsCopied] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [isLoadingPrompt, setIsLoadingPrompt] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [isCleaningWithLLM, setIsCleaningWithLLM] = useState(false);
  const [isOriginalExpanded, setIsOriginalExpanded] = useState(true);

  // --- New State for Mind Map ---
  const [mindMapData, setMindMapData] = useState<MindMapResponse | null>(null);
  const [isGeneratingMap, setIsGeneratingMap] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const isKeyDownRef = useRef(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const loadSystemPrompt = async () => {
      try {
        const response = await fetch('/api/system-prompt');
        const data = (await response.json()) as SystemPromptResponse;
        setSystemPrompt(data.default_prompt);
      } catch (err) {
        console.error('Failed to load system prompt:', err);
        setError('Failed to load system prompt');
      } finally {
        setIsLoadingPrompt(false);
      }
    };

    void loadSystemPrompt();
  }, []);

  // ... (Existing Audio Logic Remains Unchanged) ...
  const uploadAudio = useCallback(
    async (audioBlob: Blob) => {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      try {
        const transcribeResponse = await fetch('/api/transcribe', {
          method: 'POST',
          body: formData,
        });

        if (!transcribeResponse.ok)
          throw new Error(
            `Transcription failed: ${transcribeResponse.statusText}`
          );

        const transcribeData =
          (await transcribeResponse.json()) as TranscriptionResponse;
        if (!transcribeData.success)
          throw new Error(transcribeData.error || 'Transcription failed');

        setRawText(transcribeData.text || '');
        setIsProcessing(false);
        setError(null);

        if (useLLM && transcribeData.text) {
          setIsCleaningWithLLM(true);
          const cleanResponse = await fetch('/api/clean', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              text: transcribeData.text,
              ...(systemPrompt && { system_prompt: systemPrompt }),
            }),
          });

          if (!cleanResponse.ok) {
            setIsCleaningWithLLM(false);
            throw new Error(`Cleaning failed: ${cleanResponse.statusText}`);
          }

          const cleanData = (await cleanResponse.json()) as CleanResponse;
          if (cleanData.success && cleanData.text)
            setCleanedText(cleanData.text);
          setIsCleaningWithLLM(false);
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Unknown error';
        setError('Processing failed: ' + errorMessage);
        setIsProcessing(false);
      }
    },
    [useLLM, systemPrompt]
  );

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e: BlobEvent) =>
        chunksRef.current.push(e.data);
      mediaRecorderRef.current.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        await uploadAudio(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setError(null);
      setRawText(null);
      setCleanedText(null);
      setIsCleaningWithLLM(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError('Microphone access denied: ' + errorMessage);
    }
  }, [uploadAudio]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  }, [isRecording]);

  const processAudioFile = (file: File) => {
    if (!file) return;
    if (!file.type.startsWith('audio/')) {
      setError('Please select an audio file');
      return;
    }
    setError(null);
    setRawText(null);
    setCleanedText(null);
    setIsProcessing(true);
    setIsCleaningWithLLM(false);
    const blob = new Blob([file], { type: file.type });
    void uploadAudio(blob);
  };

  const handleDragEnter = () => setIsDragging(true);
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (file: File) => {
    if (isProcessing || isRecording) return;
    processAudioFile(file);
  };

  const handleFileSelect = (file: File) => {
    processAudioFile(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleTextSubmit = useCallback(
    async (text: string) => {
      if (!text.trim()) return;
      try {
        setError(null);
        setRawText(null);
        setCleanedText(null);
        setIsProcessing(true);
        setIsCleaningWithLLM(false);
        setRawText(text);
        setIsProcessing(false);

        if (useLLM) {
          setIsCleaningWithLLM(true);
          const cleanResponse = await fetch('/api/clean', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              text: text,
              ...(systemPrompt && { system_prompt: systemPrompt }),
            }),
          });

          if (!cleanResponse.ok) {
            setIsCleaningWithLLM(false);
            throw new Error(`Cleaning failed: ${cleanResponse.statusText}`);
          }

          const cleanData = (await cleanResponse.json()) as CleanResponse;
          if (cleanData.success && cleanData.text)
            setCleanedText(cleanData.text);
          setIsCleaningWithLLM(false);
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Unknown error';
        setError('Processing failed: ' + errorMessage);
        setIsProcessing(false);
        setIsCleaningWithLLM(false);
      }
    },
    [useLLM, systemPrompt]
  );

  const copyToClipboard = (text: string) => {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 2000);
      })
      .catch((err: Error) => setError('Copy failed: ' + err.message));
  };

  // --- NEW: Mind Map Generation Logic ---
  const generateMindMap = async () => {
    setIsGeneratingMap(true);
    setError(null);
    try {
      const response = await fetch('/api/generate-mindmap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pdf_path: 'data/why-llm-cant-develop-software.pdf',
          start_para: 0,
          end_para: 2,
        }),
      });

      const data = (await response.json()) as MindMapResponse;
      if (data.status === 'success') {
        setMindMapData(data);
      } else {
        setError('Failed to generate mind map');
      }
    } catch (err) {
      console.error('Error:', err);
      setError('Error connecting to backend for Mind Map');
    } finally {
      setIsGeneratingMap(false);
    }
  };

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };
  // --------------------------------------

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isProcessing || e.repeat || isKeyDownRef.current) return;
      const target = e.target as HTMLElement;
      if (
        e.key.toLowerCase() === 'v' &&
        !['INPUT', 'TEXTAREA'].includes(target.tagName)
      ) {
        e.preventDefault();
        isKeyDownRef.current = true;
        if (!isRecording) void startRecording();
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === 'v') {
        isKeyDownRef.current = false;
        if (isRecording) stopRecording();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isRecording, isProcessing, startRecording, stopRecording]);

  return (
    <div className={styles.app}>
      <div className={styles.container}>
        <Header />

        <RecordButton
          isRecording={isRecording}
          isProcessing={isProcessing}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
        />

        <UploadZone
          isProcessing={isProcessing}
          isDragging={isDragging}
          onFileSelect={handleFileSelect}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          fileInputRef={fileInputRef}
        />

        <TextInputZone
          isProcessing={isProcessing}
          onTextSubmit={handleTextSubmit}
        />

        <SettingsPanel
          useLLM={useLLM}
          systemPrompt={systemPrompt}
          isLoadingPrompt={isLoadingPrompt}
          onToggleLLM={setUseLLM}
          onPromptChange={setSystemPrompt}
        />

        {error && (
          <ErrorMessage message={error} onDismiss={() => setError(null)} />
        )}

        <TranscriptionResults
          rawText={rawText}
          cleanedText={cleanedText}
          useLLM={useLLM}
          isCopied={isCopied}
          isCleaningWithLLM={isCleaningWithLLM}
          isProcessing={isProcessing}
          isOriginalExpanded={isOriginalExpanded}
          onCopy={copyToClipboard}
          onToggleOriginalExpanded={() =>
            setIsOriginalExpanded(!isOriginalExpanded)
          }
        />

        {/* --- NEW MIND MAP SECTION --- */}
        <div
          style={{
            marginTop: '2rem',
            padding: '1.5rem',
            backgroundColor: '#fff',
            borderRadius: '12px',
            border: '1px solid #e5e7eb',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
            }}
          >
            <h2
              style={{ fontSize: '1.25rem', fontWeight: 600, color: '#111827' }}
            >
              🧠 PDF Mind Map Generator
            </h2>
            <span
              style={{
                fontSize: '0.75rem',
                backgroundColor: '#f3e8ff',
                color: '#7e22ce',
                padding: '0.25rem 0.75rem',
                borderRadius: '999px',
                fontWeight: 500,
              }}
            >
              New Feature
            </span>
          </div>

          <p
            style={{
              color: '#4b5563',
              marginBottom: '1rem',
              fontSize: '0.95rem',
            }}
          >
            Extracts the first two paragraphs from{' '}
            <code>data/why-llm-cant-develop-software.pdf</code> and visualizes
            them.
          </p>

          <button
            onClick={generateMindMap}
            disabled={isGeneratingMap}
            style={{
              width: '100%',
              padding: '0.75rem',
              backgroundColor: isGeneratingMap ? '#9ca3af' : '#7c3aed',
              color: 'white',
              borderRadius: '8px',
              fontWeight: 500,
              cursor: isGeneratingMap ? 'not-allowed' : 'pointer',
              border: 'none',
              transition: 'background-color 0.2s',
            }}
          >
            {isGeneratingMap ? 'Generating...' : 'Generate Mind Map'}
          </button>

          {mindMapData && (
            <div
              style={{ marginTop: '1.5rem', animation: 'fadeIn 0.5s ease-in' }}
            >
              <div
                style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}
              >
                <button
                  onClick={() =>
                    downloadFile(
                      JSON.stringify(mindMapData.json, null, 2),
                      'mindmap.json',
                      'application/json'
                    )
                  }
                  style={{
                    padding: '0.5rem 1rem',
                    fontSize: '0.875rem',
                    backgroundColor: '#f3f4f6',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    color: '#374151',
                  }}
                >
                  Download JSON
                </button>
                <button
                  onClick={() =>
                    downloadFile(
                      mindMapData.mermaid,
                      'mindmap.mmd',
                      'text/plain'
                    )
                  }
                  style={{
                    padding: '0.5rem 1rem',
                    fontSize: '0.875rem',
                    backgroundColor: '#f3f4f6',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    color: '#374151',
                  }}
                >
                  Download Mermaid
                </button>
              </div>

              <MindMapViewer mermaidCode={mindMapData.mermaid} />

              <div style={{ marginTop: '1rem' }}>
                <h3
                  style={{
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    color: '#374151',
                    marginBottom: '0.5rem',
                  }}
                >
                  Extracted Text
                </h3>
                <div
                  style={{
                    padding: '0.75rem',
                    backgroundColor: '#f9fafb',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                    color: '#4b5563',
                    maxHeight: '150px',
                    overflowY: 'auto',
                    border: '1px solid #e5e7eb',
                  }}
                >
                  {mindMapData.transcript}
                </div>
              </div>
            </div>
          )}
        </div>
        {/* --------------------------- */}
      </div>
    </div>
  );
}

export default App;
