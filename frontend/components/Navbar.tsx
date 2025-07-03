'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import clsx from 'clsx';
// Use client-side session hook
import { useSession, signOut } from "next-auth/react"; 

const navItems = [
  { name: 'Index', href: '/' },
  { name: 'Analysis', href: '/predict' },
  { name: 'Validation', href: '/validate' }, 
  { name: 'System', href: '/admin' },    
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 w-full z-50 mix-blend-difference text-primary">
      <div className="max-w-[1400px] mx-auto px-6 py-6 flex justify-between items-baseline">
        <Link href="/" className="group">
            <div className="text-[10px] font-sans tracking-[0.2em] text-muted mb-1 opacity-60">VER. 1.0</div>
            <span className="font-serif text-2xl tracking-tight text-white group-hover:text-primary transition-colors">
              LUNG / SCAN
            </span>
        </Link>
        
        <div className="flex space-x-12 items-baseline">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className="relative group"
              >
                <span className={clsx(
                  'text-xs font-sans tracking-[0.15em] uppercase transition-colors duration-300',
                  isActive ? 'text-primary' : 'text-muted hover:text-white'
                )}>
                  {item.name}
                </span>
                {isActive && (
                  <motion.div
                    layoutId="dot"
                    className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-1 h-1 bg-primary rounded-full"
                  />
                )}
              </Link>
            );
          })}
          
          {/* Sign Out Link (Visual Only - functionality requires SessionProvider) */}
           <button 
             onClick={() => signOut({ callbackUrl: '/login' })}
             className="text-xs font-sans tracking-[0.15em] uppercase text-muted hover:text-red-400 transition-colors"
           >
             Lock
           </button>
        </div>
      </div>
    </nav>
  );
}