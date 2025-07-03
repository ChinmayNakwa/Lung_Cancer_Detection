'use client';

import { useEffect, useState } from 'react';
import { getStats, getModels, triggerRetrain, Stats, ModelInfo } from '@/app/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, Loader2, CheckCircle2, AlertCircle, XCircle } from 'lucide-react';
import clsx from 'clsx';

export default function AdminPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  
  // New State for Retraining UI
  const [retrainStatus, setRetrainStatus] = useState<'idle' | 'loading' | 'success' | 'skipped' | 'error'>('idle');
  const [retrainResult, setRetrainResult] = useState<any>(null);

  useEffect(() => {
    getStats().then(setStats);
    getModels().then(data => setModels(data.models));
  }, [retrainStatus]); // Auto-refresh stats when retraining status changes

  const handleRetrain = async () => {
    setRetrainStatus('loading');
    setRetrainResult(null);
    
    try {
      // Simulate a slight delay for dramatic effect if API is too fast
      const [res] = await Promise.all([
          triggerRetrain(),
          new Promise(resolve => setTimeout(resolve, 800)) 
      ]);

      setRetrainResult(res);
      
      if (res.status === 'triggered') {
          setRetrainStatus('success');
      } else {
          setRetrainStatus('skipped');
      }
    } catch (e) {
      setRetrainStatus('error');
    }
  };

  return (
    <div className="min-h-screen pt-32 px-6 max-w-[1400px] mx-auto pb-24">
        <header className="mb-16 border-b border-white/10 pb-8 flex justify-between items-end">
            <div>
                <h1 className="font-serif text-6xl text-white mb-4">System Registry</h1>
                <p className="font-sans text-primary tracking-widest text-xs uppercase">Operations & Model Lifecycle</p>
            </div>
            {/* Status Indicator */}
            <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"/>
                <span className="text-xs font-mono text-muted uppercase">System Online</span>
            </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
            {/* Stat Card 1 */}
            <div className="border-l border-primary/50 pl-6">
                <h3 className="text-muted text-xs uppercase tracking-widest mb-2">Data Buffer</h3>
                <div className="font-serif text-5xl text-white">
                    {stats?.unused_predictions || 0}<span className="text-2xl text-muted">/{stats?.retrain_threshold || 300}</span>
                </div>
                <div className="w-full bg-white/10 h-1 mt-4">
                    <div 
                        className="bg-primary h-full transition-all duration-1000" 
                        style={{ width: `${stats?.progress_percentage || 0}%` }} 
                    />
                </div>
            </div>
            
            {/* Stat Card 2 */}
            <div className="border-l border-primary/50 pl-6">
                <h3 className="text-muted text-xs uppercase tracking-widest mb-2">Active Version</h3>
                <div className="font-serif text-5xl text-white">
                    v.{stats?.active_model_version || '0'}
                </div>
            </div>

            {/* Action Area */}
            <div className="flex flex-col justify-end">
                <button 
                    onClick={handleRetrain}
                    disabled={retrainStatus === 'loading'}
                    className="w-full py-4 border border-white/20 bg-surface hover:border-primary hover:text-primary transition-all text-white text-xs font-bold uppercase tracking-widest flex items-center justify-center gap-3"
                >
                    {retrainStatus === 'loading' ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin" /> 
                            Initializing Protocol...
                        </>
                    ) : (
                        "Trigger Retraining Protocol"
                    )}
                </button>
            </div>
        </div>

        {/* DYNAMIC SYSTEM CONSOLE DISPLAY */}
        <AnimatePresence>
            {retrainStatus !== 'idle' && (
                <motion.div 
                    initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                    animate={{ opacity: 1, height: 'auto', marginBottom: 60 }}
                    exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                    className="overflow-hidden"
                >
                    <div className={clsx(
                        "p-8 border-l-4 font-mono text-sm relative bg-surface/50",
                        retrainStatus === 'success' ? "border-green-500" : 
                        retrainStatus === 'skipped' ? "border-yellow-500" : "border-red-500"
                    )}>
                        <div className="flex items-start gap-4">
                            <div className="mt-1">
                                {retrainStatus === 'success' && <CheckCircle2 className="text-green-500 w-5 h-5"/>}
                                {retrainStatus === 'skipped' && <AlertCircle className="text-yellow-500 w-5 h-5"/>}
                                {retrainStatus === 'error' && <XCircle className="text-red-500 w-5 h-5"/>}
                            </div>
                            
                            <div className="space-y-2 w-full">
                                <div className="flex justify-between border-b border-white/10 pb-2 mb-2">
                                    <span className="uppercase tracking-widest text-muted">Operation Log</span>
                                    <span className="text-white/30">{new Date().toLocaleTimeString()}</span>
                                </div>
                                
                                {retrainStatus === 'success' && (
                                    <>
                                        <p className="text-green-400"> TRAINING TASK DISPATCHED SUCCESSFULLY</p>
                                        <p className="text-muted">Task ID: <span className="text-white">{retrainResult?.task_id}</span></p>
                                        <p className="text-muted">Celery Worker: <span className="text-white">Active</span></p>
                                    </>
                                )}

                                {retrainStatus === 'skipped' && (
                                    <>
                                        <p className="text-yellow-500"> OPERATION ABORTED: INSUFFICIENT DATA</p>
                                        <p className="text-muted">Current Buffer: <span className="text-white">{retrainResult?.unused_count}</span></p>
                                        <p className="text-muted">Required Threshold: <span className="text-white">{retrainResult?.required}</span></p>
                                        <p className="text-white/50 italic mt-2">"System requires more validated samples before retraining can improve model accuracy."</p>
                                    </>
                                )}

                                {retrainStatus === 'error' && (
                                    <p className="text-red-500"> CRITICAL ERROR: CONNECTION FAILED</p>
                                )}
                            </div>
                            
                            {/* Close Console Button */}
                            <button 
                                onClick={() => setRetrainStatus('idle')}
                                className="text-white/30 hover:text-white"
                            >
                                <span className="sr-only">Dismiss</span>
                                ×
                            </button>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>

        <h2 className="font-serif text-3xl mb-8 text-white">Model Archives</h2>
        <div className="w-full">
            <table className="w-full text-left border-collapse">
                <thead>
                    <tr className="border-b border-white/20">
                        <th className="py-4 text-xs font-normal text-muted uppercase tracking-widest">Version</th>
                        <th className="py-4 text-xs font-normal text-muted uppercase tracking-widest">Run ID</th>
                        <th className="py-4 text-xs font-normal text-muted uppercase tracking-widest">Date</th>
                        <th className="py-4 text-xs font-normal text-muted uppercase tracking-widest">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {models.map((m) => (
                        <tr key={m.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                            <td className="py-6 font-serif text-xl text-primary">v.{m.version}</td>
                            <td className="py-6 font-mono text-xs text-muted">{m.mlflow_run_id}</td>
                            <td className="py-6 font-sans text-xs text-white/60">{new Date(m.created_at).toLocaleDateString()}</td>
                            <td className="py-6">
                                {m.is_active ? (
                                    <span className="text-[10px] tracking-widest border border-primary/30 text-primary px-3 py-1 uppercase">Active</span>
                                ) : (
                                    <span className="text-[10px] tracking-widest text-muted uppercase">Archived</span>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    </div>
  );
}