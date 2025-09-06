import React, { useState, useEffect, Fragment } from 'react';
import './VoiceInputButton.css';

const VoiceInputButton = ({ onTranscript, onInterimTranscript, isListening, onStartListening, onStopListening }) => {
  const [recognition, setRecognition] = useState(null);
  const [isSupported, setIsSupported] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Tarayıcı uyumluluğunu kontrol et
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      const recognitionInstance = new SpeechRecognition();
      
      // Türkçe dil ayarı
      recognitionInstance.lang = 'tr-TR';
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = true; // Geçici sonuçları al
      recognitionInstance.maxAlternatives = 1;

      // Event listeners
      recognitionInstance.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        // Geçici sonuçları gönder
        if (interimTranscript) {
          onInterimTranscript(interimTranscript);
        }

        // Final sonuçları gönder
        if (finalTranscript) {
          onTranscript(finalTranscript);
        }
      };

      recognitionInstance.onerror = (event) => {
        console.error('Konuşma tanıma hatası:', event.error);
        setError(`Hata: ${event.error}`);
        onStopListening();
      };

      recognitionInstance.onend = () => {
        onStopListening();
      };

      recognitionInstance.onstart = () => {
        setError(null);
      };

      setRecognition(recognitionInstance);
      setIsSupported(true);
    } else {
      setIsSupported(false);
      setError('Tarayıcınız konuşma tanıma API\'sini desteklemiyor.');
    }
  }, [onTranscript, onStartListening, onStopListening]);

  const handleClick = () => {
    if (!isSupported) {
      alert('Tarayıcınız konuşma tanıma özelliğini desteklemiyor. Lütfen Chrome, Edge veya Safari kullanın.');
      return;
    }

    if (isListening) {
      recognition.stop();
      onStopListening();
    } else {
      try {
        recognition.start();
        onStartListening();
      } catch (err) {
        console.error('Mikrofon başlatma hatası:', err);
        setError('Mikrofon başlatılamadı. Lütfen mikrofon izni verin.');
      }
    }
  };

  if (!isSupported) {
    return null; // Desteklenmeyen tarayıcılarda butonu gösterme
  }

  return (
    <button
      className={`voice-input-button ${isListening ? 'listening' : ''}`}
      onClick={handleClick}
      title={isListening ? 'Konuşmayı durdur' : 'Sesli giriş başlat'}
      disabled={!isSupported}
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        {isListening ? (
          // Kayıt durdurma ikonu (kare)
          <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/>
        ) : (
          // Mikrofon ikonu
          <Fragment>
            <path 
              d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" 
              fill="currentColor"
            />
            <path 
              d="M19 10v2a7 7 0 0 1-14 0v-2" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
            <line 
              x1="12" 
              y1="19" 
              x2="12" 
              y2="23" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
            <line 
              x1="8" 
              y1="23" 
              x2="16" 
              y2="23" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
          </Fragment>
        )}
      </svg>
      
      {error && (
        <div className="voice-error">
          {error}
        </div>
      )}
    </button>
  );
};

export default VoiceInputButton;
