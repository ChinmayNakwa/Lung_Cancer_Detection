'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { uploadImage, PredictionResult } from '@/app/lib/api';
import Link from 'next/link';
import Image from 'next/image';

// Helper to make snake_case look like a title
const formatLabel = (label: string) => {
  if (!label) return "Unknown";
  return label.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

// NEW: Robust helper to handle confidence scores
const formatConfidence = (value: number | string | undefined) => {
  if (value === undefined || value === null) return "0.00";

  // 1. Convert to string first to handle any edge cases
  const strVal = String(value);

  // 2. Remove '%' if it exists (e.g. "98.5%")
  const cleanStr = strVal.replace('%', '');

  // 3. Parse as float
  const num = parseFloat(cleanStr);

  if (isNaN(num)) return "0.00";

  // 4. Heuristic: If value is <= 1 (e.g. 0.98), it's a probability -> multiply by 100
  // If value is > 1 (e.g. 98.5), it's already a percentage -> keep as is
  if (num <= 1 && num >= 0) {
    return (num * 100).toFixed(2);
  }
  
  return num.toFixed(2);
};

export default function PredictPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
      setResult(null);
    }
  };

  const handlePredict = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const data = await uploadImage(file);
      setResult(data);
    } catch (err) {
      alert("Error processing image");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen pt-32 px-6 max-w-[1400px] mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        
        {/* Left Column: Title & Controls */}
        <div className="col-span-1 lg:col-span-4 space-y-8">
          <div>
            <span className="text-primary text-xs tracking-[0.2em] uppercase">Input Source</span>
            <h1 className="font-serif text-5xl mt-2 text-white">Scan Analysis</h1>
          </div>
          
          <p className="text-muted font-sans leading-relaxed">
            Upload DICOM converted PNG/JPG files. The system detects: Adenocarcinoma, Squamous Carcinoma, and Benign tissue.
          </p>

          <div className="pt-8 border-t border-white/10">
             <label className="block cursor-pointer group">
                <input type="file" className="hidden" onChange={handleFileChange} accept="image/*" />
                <div className="flex items-center justify-between py-4 border-b border-white/30 group-hover:border-primary transition-colors">
                    <span className="font-serif text-xl group-hover:text-primary transition-colors truncate max-w-[200px]">
                        {file ? file.name : "Select File"}
                    </span>
                    <span className="text-xs uppercase tracking-widest text-muted group-hover:text-white">
                        Browse
                    </span>
                </div>
             </label>

             <button 
                onClick={handlePredict}
                disabled={!file || loading}
                className="mt-8 w-full py-4 bg-primary text-black font-sans text-xs font-bold tracking-[0.15em] uppercase hover:bg-white transition-colors disabled:opacity-50"
             >
                {loading ? "Processing..." : "Run Sequence"}
             </button>
          </div>
        </div>

        {/* Right Column: Visual & Result */}
        <div className="col-span-1 lg:col-span-8 relative min-h-[500px]">
           <div className="w-full h-full border border-white/10 bg-surface/50 relative p-8 flex items-center justify-center">
                {/* Decorative Corners */}
                <div className="absolute top-0 left-0 w-4 h-4 border-t border-l border-primary"/>
                <div className="absolute top-0 right-0 w-4 h-4 border-t border-r border-primary"/>
                <div className="absolute bottom-0 left-0 w-4 h-4 border-b border-l border-primary"/>
                <div className="absolute bottom-0 right-0 w-4 h-4 border-b border-r border-primary"/>

                {preview ? (
                   <div className="relative w-full h-full min-h-[400px]">
                      <Image src={preview} alt="Scan" fill className="object-contain" />
                   </div>
                ) : (
                    <span className="font-serif text-2xl text-white/20 italic">Awaiting Input...</span>
                )}
           </div>

           <AnimatePresence>
            {result && (
                <motion.div 
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="absolute -bottom-12 -left-6 lg:-left-12 bg-background border border-primary p-8 shadow-2xl max-w-sm w-full"
                >
                    <div className="flex justify-between items-baseline mb-2">
                        <span className="text-xs tracking-widest text-muted uppercase">Diagnosis</span>
                        <span className="text-xs tracking-widest text-muted uppercase">ID: {result.id}</span>
                    </div>
                    
                    {/* Formatted Class Name */}
                    <div className="font-serif text-4xl text-white mb-2 leading-tight">
                        {formatLabel(result.predicted_class)}
                    </div>
                    
                    {/* SAFE CONFIDENCE DISPLAY */}
                    <div className="flex items-end gap-2">
                        <span className="font-sans text-primary text-xl font-bold">
                            {formatConfidence(result.confidence)}%
                        </span>
                        <span className="text-xs text-muted mb-1">Confidence Score</span>
                    </div>
                    
                    <div className="mt-6 pt-6 border-t border-dashed border-white/20">
                        <Link href={`/validate?id=${result.id}`} className="text-xs text-white underline decoration-primary decoration-1 underline-offset-4 hover:text-primary">
                            Incorrect? Flag for review
                        </Link>
                    </div>
                </motion.div>
            )}
           </AnimatePresence>
        </div>

      </div>
    </div>
  );
}