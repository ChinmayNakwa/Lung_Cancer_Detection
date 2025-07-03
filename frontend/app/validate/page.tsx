'use client';

import { Suspense, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { correctPrediction } from '@/app/lib/api';
import clsx from 'clsx';

// The classes from dataset
const DIAGNOSIS_OPTIONS = [
  { id: 'adenocarcinoma', label: 'Adenocarcinoma' },
  { id: 'squamous_carcinoma', label: 'Squamous Carcinoma' },
  { id: 'benign', label: 'Benign' },
];

function ValidateContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const idParam = searchParams.get('id');
  
  const [predId, setPredId] = useState(idParam || '');
  const [selectedClass, setSelectedClass] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');

  const handleSubmit = async () => {
    if (!predId || !selectedClass) return;
    setStatus('submitting');
    try {
      await correctPrediction(parseInt(predId), selectedClass);
      setStatus('success');
      setTimeout(() => router.push('/admin'), 1500);
    } catch (e) {
      setStatus('error');
    }
  };

  return (
    <div className="max-w-2xl w-full mx-auto space-y-12">
      <header className="text-center space-y-4">
        <span className="text-xs font-sans tracking-[0.2em] text-primary uppercase">Human-in-the-loop</span>
        <h1 className="text-5xl font-serif text-white">Validation Protocol</h1>
        <p className="text-muted font-sans text-sm max-w-md mx-auto leading-relaxed">
          Expert review of ambiguous classifications. This input directly influences the next retraining cycle.
        </p>
      </header>

      <div className="bg-surface/50 border border-white/10 p-8 md:p-12 relative">
        {/* Decorative corner accents */}
        <div className="absolute top-0 left-0 w-3 h-3 border-t border-l border-primary opacity-50"/>
        <div className="absolute top-0 right-0 w-3 h-3 border-t border-r border-primary opacity-50"/>
        <div className="absolute bottom-0 left-0 w-3 h-3 border-b border-l border-primary opacity-50"/>
        <div className="absolute bottom-0 right-0 w-3 h-3 border-b border-r border-primary opacity-50"/>

        <div className="space-y-10">
          
          {/* ID Input */}
          <div className="space-y-2">
            <label className="block text-xs font-sans tracking-widest text-muted uppercase">Reference ID</label>
            <input 
              type="number" 
              value={predId} 
              onChange={(e) => setPredId(e.target.value)}
              className="w-full text-2xl bg-transparent border-b border-white/20 pb-2 text-white font-serif focus:border-primary focus:outline-none transition-colors placeholder:text-white/10"
              placeholder="000"
            />
          </div>

          {/* Class Selection */}
          <div className="space-y-4">
            <label className="block text-xs font-sans tracking-widest text-muted uppercase">Correct Diagnosis</label>
            <div className="grid grid-cols-1 gap-4">
              {DIAGNOSIS_OPTIONS.map((option) => (
                <button
                  key={option.id}
                  onClick={() => setSelectedClass(option.id)}
                  className={clsx(
                    "group relative p-6 text-left border transition-all duration-500",
                    selectedClass === option.id 
                      ? "border-primary bg-primary/10" 
                      : "border-white/10 hover:border-white/30"
                  )}
                >
                  <div className="flex items-baseline justify-between">
                    <span className={clsx(
                      "font-serif text-xl transition-colors",
                      selectedClass === option.id ? "text-primary" : "text-white group-hover:text-primary"
                    )}>
                      {option.label}
                    </span>
                    {selectedClass === option.id && (
                        <span className="text-[10px] uppercase tracking-widest text-primary">Selected</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={status === 'submitting' || !selectedClass || !predId}
            className="w-full py-5 bg-white hover:bg-primary text-black transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <span className="font-sans text-xs font-bold tracking-[0.2em] uppercase group-hover:text-white transition-colors">
              {status === 'submitting' ? 'Updating Database...' : 'Confirm Classification'}
            </span>
          </button>

          {/* Success Feedback */}
          {status === 'success' && (
            <div className="text-center pt-4 border-t border-white/10 animate-fade-in">
              <p className="font-serif text-xl italic text-primary">Record updated successfully.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ValidatePage() {
  return (
    <div className="min-h-screen pt-32 px-6 pb-20">
      <Suspense fallback={<div className="text-white text-center font-serif italic">Loading interface...</div>}>
        <ValidateContent />
      </Suspense>
    </div>
  );
}