'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SectionHeading } from '../ui/SectionHeading';
import { Button } from '../ui/Button';
import { versions, getLatestVersion, getDownloadUrl, type Version } from '../../lib/versions';
import { platformDetector } from '../../lib/platform-detection';
import { cn } from '../../lib/utils';
import {
  Download,
  ChevronDown,
  ChevronUp,
  Check,
  Monitor,
  Apple,
  Terminal,
  FileText,
  Shield,
  Clock,
  X,
  Package,
  Zap,
} from 'lucide-react';

type DownloadState = 'idle' | 'preparing' | 'connecting' | 'downloading' | 'ready' | 'error';

const platformIcons = {
  windows: Monitor,
  macos: Apple,
  linux: Terminal,
};

export function DownloadCenter() {
  const [activeVersion, setActiveVersion] = useState<Version>(getLatestVersion());
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [downloadState, setDownloadState] = useState<DownloadState>('idle');
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [showReleaseNotes, setShowReleaseNotes] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<'windows' | 'macos' | 'linux'>('windows');
  const [detectedPlatform, setDetectedPlatform] = useState<{
    os: 'windows' | 'macos' | 'linux' | null;
    arch: string;
    isAppleSilicon: boolean;
  } | null>(null);
  const progressRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const info = platformDetector.detectPlatform();
    let os: 'windows' | 'macos' | 'linux' | null = null;
    if (info.isWindows) os = 'windows';
    else if (info.isMacOS) os = 'macos';
    else if (info.isLinux) os = 'linux';

    const arch = info.processorArchitecture === 'arm64' ? 'ARM64' : '64-bit';

    setDetectedPlatform({
      os,
      arch,
      isAppleSilicon: info.isAppleSilicon,
    });

    if (os) {
      setSelectedPlatform(os);
    }
  }, []);

  const handleDownload = async () => {
    if (downloadState === 'downloading' || downloadState === 'preparing' || downloadState === 'connecting') return;

    // Reset any previous intervals
    if (progressRef.current) clearInterval(progressRef.current);
    setDownloadState('preparing');
    setDownloadProgress(0);

    try {
      // Get the download URL for the selected platform
      const downloadUrl = getDownloadUrl(activeVersion, selectedPlatform);
      
      if (!downloadUrl || downloadUrl === '#') {
        setDownloadState('error');
        return;
      }

      // Simulate preparation and connecting phases
      setTimeout(() => setDownloadState('connecting'), 800);
      
      setTimeout(() => {
        setDownloadState('downloading');
        
        // Create a hidden anchor element to trigger the download
        const downloadLink = document.createElement('a');
        downloadLink.href = downloadUrl;
        downloadLink.style.display = 'none';
        downloadLink.target = '_blank';
        downloadLink.rel = 'noopener noreferrer';
        document.body.appendChild(downloadLink);
        
        // Trigger the download by clicking the hidden link
        downloadLink.click();
        
        // Remove the element after triggering
        setTimeout(() => {
          document.body.removeChild(downloadLink);
        }, 100);
        
        // Simulate progress (real browser downloads don't expose progress easily)
        let progress = 0;
        progressRef.current = setInterval(() => {
          progress += Math.random() * 12 + 3;
          if (progress >= 90) {
            progress = 90;
            if (progressRef.current) clearInterval(progressRef.current);
          }
          setDownloadProgress(Math.min(progress, 90));
        }, 300);

        // Clean up after a realistic download time
        setTimeout(() => {
          if (progressRef.current) clearInterval(progressRef.current);
          setDownloadProgress(100);
          setDownloadState('ready');
        }, 3000);
      }, 1800);
      
    } catch (error) {
      console.error('Download failed:', error);
      if (progressRef.current) clearInterval(progressRef.current);
      setDownloadState('error');
    }
  };

  const resetDownload = () => {
    if (progressRef.current) clearInterval(progressRef.current);
    setDownloadState('idle');
    setDownloadProgress(0);
  };

  const platform = activeVersion.platforms.find((p) => p.platform === selectedPlatform);

  return (
    <section id="download" className="relative py-32">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 right-0 w-[600px] h-[600px] rounded-full bg-blue-500/3 blur-3xl" />
        <div className="absolute bottom-1/3 left-0 w-[400px] h-[400px] rounded-full bg-purple-500/3 blur-3xl" />
      </div>

      <div className="max-w-6xl mx-auto px-6">
        <SectionHeading
          label="Download Center"
          title="Get AVORA"
          description="Download the latest stable release and experience a new kind of personal intelligence."
        />

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mt-16"
          >
            {/* Platform Detection Banner */}
            {detectedPlatform && detectedPlatform.os && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="mb-6"
              >
                <div className="max-w-2xl mx-auto rounded-xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-md p-4 flex flex-col sm:flex-row items-start sm:items-center gap-3">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                      <Zap size={14} className="text-blue-400" />
                    </div>
                    <div>
                      <span className="text-xs text-gray-400 uppercase tracking-wider">Detected</span>
                      <p className="text-sm text-white font-medium">
                        {detectedPlatform.os === 'windows' && `Windows (${detectedPlatform.arch})`}
                        {detectedPlatform.os === 'macos' && detectedPlatform.isAppleSilicon && `macOS (Apple Silicon)`}
                        {detectedPlatform.os === 'macos' && !detectedPlatform.isAppleSilicon && `macOS (Intel)`}
                        {detectedPlatform.os === 'linux' && `Linux (${detectedPlatform.arch})`}
                      </p>
                    </div>
                  </div>
                  <div className="sm:ml-auto">
                    {detectedPlatform.os === 'macos' && detectedPlatform.isAppleSilicon ? (
                      <span className="text-sm text-yellow-400 font-medium">macOS version coming soon.</span>
                    ) : (
                      <span className="text-sm text-emerald-400 font-medium">
                        Recommended: AVORA Setup v{getLatestVersion().version}
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Platform tabs */}
            <div className="flex justify-center gap-3 mb-8">
            {(['windows', 'macos', 'linux'] as const).map((pf) => {
              const Icon = platformIcons[pf];
              const isAvailable = activeVersion.platforms.some((p) => p.platform === pf && p.size !== 'TBD');
              return (
                <motion.button
                  key={pf}
                  onClick={() => setSelectedPlatform(pf)}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm border transition-all duration-300 capitalize',
                    selectedPlatform === pf
                      ? 'bg-white/[0.08] border-white/[0.15] text-white'
                      : 'bg-white/[0.02] border-white/[0.08] text-gray-400 hover:text-gray-200',
                    !isAvailable && 'opacity-40 cursor-not-allowed'
                  )}
                  whileHover={isAvailable ? { scale: 1.05, y: -2 } : {}}
                  whileTap={isAvailable ? { scale: 0.95 } : {}}
                >
                  <Icon size={16} />
                  {pf}
                  {!isAvailable && (
                    <span className="text-[10px] text-gray-600 ml-1">Soon</span>
                  )}
                </motion.button>
              );
            })}
          </div>

          <div className="grid lg:grid-cols-5 gap-8">
            {/* Download Card */}
            <div className="lg:col-span-3">
              <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl overflow-hidden">
                <div className="p-8">
                  {/* Version badge */}
                  <div className="flex items-center gap-3 mb-6">
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">
                        {activeVersion.label}
                      </span>
                    </div>
                    {activeVersion.isLatest && (
                      <span className="text-xs text-gray-500 border border-white/[0.08] rounded-full px-3 py-1.5">
                        Latest Release
                      </span>
                    )}
                  </div>

                  <h3 className="text-2xl font-bold text-white mb-2">{activeVersion.title}</h3>
                  <div className="flex items-center gap-4 text-sm text-gray-500 mb-6">
                    <span className="flex items-center gap-1">
                      <Package size={14} />
                      Version {activeVersion.version}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock size={14} />
                      {activeVersion.releaseDate}
                    </span>
                  </div>

                  <p className="text-sm text-gray-400 leading-relaxed mb-8">
                    {activeVersion.description}
                  </p>

                  {/* System requirements */}
                  <div className="mb-8">
                    <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <Shield size={12} />
                      System Requirements
                    </h4>
                    <ul className="space-y-1.5">
                      {activeVersion.systemRequirements.map((req) => (
                        <li key={req} className="flex items-center gap-2 text-xs text-gray-500">
                          <div className="w-1 h-1 rounded-full bg-blue-500/50" />
                          {req}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Download state */}
                  <div className="space-y-4">
                    {downloadState === 'idle' && platform && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                      >
                        <Button
                          size="lg"
                          icon={<Download size={18} />}
                          onClick={handleDownload}
                          className="w-full"
                          magnetic
                        >
                          Download for {selectedPlatform === 'windows' ? 'Windows' : selectedPlatform === 'macos' ? 'macOS' : 'Linux'}
                        </Button>
                        {platform.size && (
                          <p className="text-xs text-gray-500 text-center mt-2">
                            {platform.type === 'installer' ? 'Installer' : 'Portable'} · {platform.size}
                            {platform.checksum && ` · ${platform.checksum.slice(0, 20)}...`}
                          </p>
                        )}
                        {selectedPlatform === 'windows' && (
                          <p className="text-[10px] text-yellow-400/80 text-center mt-3 leading-relaxed">
                            Note: If Windows Defender shows a SmartScreen prompt, click "More info" → "Run anyway"
                          </p>
                        )}
                      </motion.div>
                    )}

                    <AnimatePresence mode="wait">
                      {downloadState === 'preparing' && (
                        <motion.div
                          key="preparing"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          className="flex items-center gap-3 px-4 py-3 rounded-xl bg-blue-500/10 border border-blue-500/20"
                        >
                          <div className="w-4 h-4 border-2 border-blue-400/30 border-t-blue-400 rounded-full animate-spin" />
                          <span className="text-sm text-blue-300">Preparing AVORA...</span>
                        </motion.div>
                      )}

                      {downloadState === 'connecting' && (
                        <motion.div
                          key="connecting"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          className="flex items-center gap-3 px-4 py-3 rounded-xl bg-purple-500/10 border border-purple-500/20"
                        >
                          <div className="w-4 h-4 border-2 border-purple-400/30 border-t-purple-400 rounded-full animate-spin" />
                          <span className="text-sm text-purple-300">Connecting to release server...</span>
                        </motion.div>
                      )}

                      {downloadState === 'downloading' && (
                        <motion.div
                          key="downloading"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          className="space-y-3"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-blue-300">Downloading AVORA...</span>
                            <span className="text-xs text-gray-400">{Math.round(downloadProgress)}%</span>
                          </div>
                          <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                            <motion.div
                              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                              style={{ width: `${downloadProgress}%` }}
                              transition={{ duration: 0.3 }}
                            />
                          </div>
                          <p className="text-[10px] text-gray-600">
                            {platform?.size} · Please wait while we prepare your download
                          </p>
                        </motion.div>
                      )}

                      {downloadState === 'ready' && (
                        <motion.div
                          key="ready"
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          className="space-y-3"
                        >
                          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                            <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                              <Check size={14} className="text-emerald-400" />
                            </div>
                            <div>
                              <p className="text-sm font-medium text-emerald-300">Download Complete</p>
                              <p className="text-xs text-gray-500">
                                AVORA {activeVersion.version} is ready
                              </p>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="primary"
                              className="flex-1"
                              onClick={() => window.open(platform?.url || '#', '_blank')}
                            >
                              <Download size={14} />
                              Save Installer
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={resetDownload}
                            >
                              Reset
                            </Button>
                          </div>
                        </motion.div>
                      )}

                      {downloadState === 'error' && (
                        <motion.div
                          key="error"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          className="flex items-center gap-3 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20"
                        >
                          <span className="text-sm text-red-300">Download failed. Please try again.</span>
                          <Button size="sm" variant="ghost" onClick={resetDownload}>
                            Retry
                          </Button>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </div>
            </div>

            {/* Version info sidebar */}
            <div className="lg:col-span-2 space-y-6">
              {/* Quick info */}
              <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
                <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-4">
                  About This Release
                </h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Version</span>
                    <span className="text-white font-medium">{activeVersion.version}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Release Date</span>
                    <span className="text-gray-300">{activeVersion.releaseDate}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Platform</span>
                    <span className="text-gray-300 capitalize">{selectedPlatform}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Size</span>
                    <span className="text-gray-300">{platform?.size || 'TBD'}</span>
                  </div>
                </div>

                <motion.button
                  onClick={() => setShowReleaseNotes(true)}
                  className="flex items-center gap-2 mt-4 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                  whileHover={{ x: 2 }}
                >
                  <FileText size={12} />
                  View Release Notes
                </motion.button>
              </div>

              {/* Version selector */}
              <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6">
                <motion.button
                  onClick={() => setShowVersionHistory(!showVersionHistory)}
                  className="flex items-center justify-between w-full"
                >
                  <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                    Version History
                  </h4>
                  {showVersionHistory ? (
                    <ChevronUp size={14} className="text-gray-500" />
                  ) : (
                    <ChevronDown size={14} className="text-gray-500" />
                  )}
                </motion.button>

                <AnimatePresence>
                  {showVersionHistory && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="space-y-2 mt-4">
                        {versions.map((v) => (
                          <motion.button
                            key={v.version}
                            onClick={() => {
                              setActiveVersion(v);
                              setShowVersionHistory(false);
                              resetDownload();
                            }}
                            className={cn(
                              'w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all duration-200',
                              activeVersion.version === v.version
                                ? 'bg-blue-500/10 border border-blue-500/20'
                                : 'hover:bg-white/[0.03] border border-transparent'
                            )}
                            whileHover={{ x: 2 }}
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <span className="text-white font-medium">v{v.version}</span>
                                <span className={cn(
                                  'ml-2 text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded',
                                  v.label === 'stable' ? 'text-emerald-400 bg-emerald-500/10' :
                                  v.label === 'beta' ? 'text-blue-400 bg-blue-500/10' :
                                  'text-yellow-400 bg-yellow-500/10'
                                )}>
                                  {v.label}
                                </span>
                              </div>
                              <span className="text-xs text-gray-500">{v.releaseDate}</span>
                            </div>
                          </motion.button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Release Notes Modal */}
      <AnimatePresence>
        {showReleaseNotes && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={() => setShowReleaseNotes(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              className="relative w-full max-w-lg max-h-[80vh] overflow-y-auto rounded-2xl border border-white/[0.08] bg-[#0a0a0f] backdrop-blur-xl p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">Release Notes</h3>
                  <p className="text-xs text-gray-500">
                    Version {activeVersion.version} · {activeVersion.releaseDate}
                  </p>
                </div>
                <motion.button
                  onClick={() => setShowReleaseNotes(false)}
                  className="w-8 h-8 rounded-full bg-white/[0.06] flex items-center justify-center hover:bg-white/[0.1] transition-colors"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <X size={14} className="text-gray-400" />
                </motion.button>
              </div>

              <div className="space-y-4">
                {activeVersion.features.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">New Features</h4>
                    <ul className="space-y-1.5">
                      {activeVersion.features.map((f) => (
                        <li key={f} className="flex items-start gap-2 text-sm text-gray-300">
                          <span className="text-emerald-400 mt-0.5">+</span>
                          {f}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {activeVersion.improvements.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2">Improvements</h4>
                    <ul className="space-y-1.5">
                      {activeVersion.improvements.map((imp) => (
                        <li key={imp} className="flex items-start gap-2 text-sm text-gray-300">
                          <span className="text-blue-400 mt-0.5">↑</span>
                          {imp}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {activeVersion.bugFixes.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-2">Bug Fixes</h4>
                    <ul className="space-y-1.5">
                      {activeVersion.bugFixes.map((fix) => (
                        <li key={fix} className="flex items-start gap-2 text-sm text-gray-300">
                          <span className="text-purple-400 mt-0.5">✓</span>
                          {fix}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

export default DownloadCenter;