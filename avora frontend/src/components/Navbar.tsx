import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { Button } from './ui/Button';
import AvoraLogo from './brand/AvoraLogo';
import { cn } from '../lib/utils';

const navLinks = [
  { label: 'Intelligence', href: '#intelligence' },
  { label: 'Ecosystem', href: '#ecosystem' },
  { label: 'Modes', href: '#modes' },
  { label: 'Demo', href: '#demo' },
  { label: 'Download', href: '#download' },
  { label: 'Roadmap', href: '#roadmap' },
  { label: 'Privacy', href: '#privacy' },
  { label: 'Developer', href: '#developer' },
];

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeHash, setActiveHash] = useState('');

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
      const sections = navLinks.map(link => link.href.slice(1));
      const current = sections.find(id => {
        const el = document.getElementById(id);
        if (el) {
          const rect = el.getBoundingClientRect();
          return rect.top <= 120;
        }
        return false;
      });
      setActiveHash(current || '');
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-500',
        scrolled
          ? 'bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/[0.06]'
          : 'bg-transparent'
      )}
    >
      <nav className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <motion.a
          href="#"
          className="flex items-center gap-2"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <AvoraLogo height={18} />
        </motion.a>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <motion.a
              key={link.label}
              href={link.href}
              className={cn(
                'text-sm transition-colors duration-300 relative',
                activeHash === link.href.slice(1)
                  ? 'text-white'
                  : 'text-gray-400 hover:text-white'
              )}
              whileHover={{ y: -2 }}
              whileTap={{ y: 0 }}
            >
              {link.label}
              {activeHash === link.href.slice(1) && (
                <motion.div
                  layoutId="navbar-indicator"
                  className="absolute -bottom-1 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
            </motion.a>
          ))}
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Button size="sm" onClick={() => {
              const downloadSection = document.getElementById('download');
              if (downloadSection) downloadSection.scrollIntoView({ behavior: 'smooth' });
            }}>
              Download AVORA
            </Button>
          </motion.div>
        </div>

        {/* Mobile toggle */}
        <motion.button
          className="md:hidden text-white hover-target"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Toggle menu"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          {isOpen ? <X size={20} /> : <Menu size={20} />}
        </motion.button>
      </nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="md:hidden bg-[#0a0a0f]/95 backdrop-blur-xl border-b border-white/[0.06] overflow-hidden"
          >
            <div className="px-6 py-6 flex flex-col gap-4">
              {navLinks.map((link, index) => (
                <motion.a
                  key={link.label}
                  href={link.href}
                  onClick={() => setIsOpen(false)}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ delay: index * 0.05 }}
                >
                  {link.label}
                </motion.a>
              ))}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Button size="sm" className="mt-2" onClick={() => {
                  setIsOpen(false);
                  const downloadSection = document.getElementById('download');
                  if (downloadSection) downloadSection.scrollIntoView({ behavior: 'smooth' });
                }}>
                  Download AVORA
                </Button>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}