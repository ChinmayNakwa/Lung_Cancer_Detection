'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react'; // Client side sign in for simplicity
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const res = await signIn('credentials', {
      username,
      password,
      redirect: false,
    });

    if (res?.error) {
      setError('Invalid credentials. Access denied.');
      setLoading(false);
    } else {
      router.push('/admin'); // Redirect to admin on success
      router.refresh();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 relative overflow-hidden">
      {/* Background Texture already in globals.css, but we can add a spotlight */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/5 blur-[120px] rounded-full -z-10" />

      <div className="w-full max-w-md">
        <div className="text-center mb-12">
           <span className="text-xs font-sans tracking-[0.3em] text-muted uppercase">Authorized Personnel Only</span>
           <h1 className="font-serif text-5xl text-white mt-4">System Access</h1>
        </div>

        <form onSubmit={handleSubmit} className="bg-surface/50 border border-white/10 p-12 relative">
            {/* Decorative corners */}
            <div className="absolute top-0 left-0 w-3 h-3 border-t border-l border-primary"/>
            <div className="absolute top-0 right-0 w-3 h-3 border-t border-r border-primary"/>
            <div className="absolute bottom-0 left-0 w-3 h-3 border-b border-l border-primary"/>
            <div className="absolute bottom-0 right-0 w-3 h-3 border-b border-r border-primary"/>

            <div className="space-y-8">
                <div>
                    <label className="block text-xs font-sans tracking-widest text-muted uppercase mb-2">Identify</label>
                    <input 
                        type="text" 
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="w-full editorial-input pb-2 text-xl"
                        placeholder="Username"
                        required
                    />
                </div>
                
                <div>
                    <label className="block text-xs font-sans tracking-widest text-muted uppercase mb-2">Keycode</label>
                    <input 
                        type="password" 
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full editorial-input pb-2 text-xl"
                        placeholder="••••••••"
                        required
                    />
                </div>

                {error && (
                    <div className="text-red-400 text-xs font-sans tracking-widest uppercase text-center">
                        {error}
                    </div>
                )}

                <button 
                    type="submit" 
                    disabled={loading}
                    className="w-full py-4 bg-white text-black font-bold font-sans text-xs tracking-[0.2em] uppercase hover:bg-primary transition-colors mt-4"
                >
                    {loading ? "Verifying..." : "Enter Secure Area"}
                </button>
            </div>
        </form>
        
        <div className="text-center mt-8">
            <p className="font-serif italic text-white/20">LungScan AI Diagnostic Division</p>
        </div>
      </div>
    </div>
  );
}