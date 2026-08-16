/*
 * Downloads Component - Platform-Aware Download Manager
 * 
 * Handles platform-specific download requirements with robust error handling
 * and graceful degradation for maximum compatibility across all systems.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, CheckCircle, AlertCircle, Loader2, X, Zap } from 'lucide-react';
import { cn } from '../../lib/utils';
import { platformDetector } from '../../lib/platform-detection';

interface DownloadInfo {
  id: string;
  platform: 'windows' | 'macos' | 'linux';
  version: string;
  name: string;
  size: string;
  type: 'installer' | 'portable';
  description: string;
  requirements: string[];
  checksum?: string;
  status: 'available' | 'downloading' | 'completed' | 'error' | 'unsupported';
  error?: string;
}

export function Downloads() {
  const [downloads, setDownloads] = useState<DownloadInfo[]>([]);
  const [networkStatus, setNetworkStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [currentDownload, setCurrentDownload] = useState<string | null>(null);
  const [compatibility, setCompatibility] = useState<any>(null);
  const [showRequirements, setShowRequirements] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState<boolean>(true);

  // Network monitoring
  const setupNetworkMonitoring = useCallback(() => {
    const updateNetworkStatus = () => {
      setNetworkStatus(navigator.onLine ? 'online' : 'offline');
    };
    
    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);
    
    return () => {
      window.removeEventListener('online', updateNetworkStatus);
      window.removeEventListener('offline', updateNetworkStatus);
    };
  }, []);

  // Initialize platform detection
  useEffect(() => {
    const init = async () => {
      try {
        const platformInfo = platformDetector.detectPlatform();
        setCompatibility(platformInfo);
        
        // Check if current platform is supported
        setIsSupported(isPlatformSupported(platformInfo));
        
        // Initialize downloads based on platform
        initializeDownloads(platformInfo);
        
        // Set up network monitoring
        setupNetworkMonitoring();
        
      } catch (error) {
        console.error('Failed to initialize downloads:', error);
        // Fallback to manual initialization
        initializeDownloadsFallback();
      }
    };
    
    init();
  }, []);

  // Platform detection helper
  const isPlatformSupported = (platform: any): boolean => {
    if (platform.isWindows) {
      return true; // Windows always supported
    }
    if (platform.isMacOS) {
      // Check minimum OS version for macOS
      const userAgent = navigator.userAgent;
      return userAgent.includes('Mac OS') && !userAgent.includes('Mac OS X 10.');
    }
    if (platform.isLinux) {
      return true; // Linux always supported
    }
    return false;
  };

  // Initialize downloads based on platform
  const initializeDownloads = (platform: any) => {
    const windowsDownload: DownloadInfo = {
      id: 'windows-installer',
      platform: 'windows',
      version: '1.0.0',
      name: 'AVORA Desktop Setup',
      size: '245 MB',
      type: 'installer',
      description: 'Recommended installer for Windows systems',
      requirements: [
        'Windows 10 / 11 (64-bit)',
        'Intel Core i5 or equivalent (AMD equivalent supported)',
        '8GB RAM (16GB recommended)',
        '4GB available storage',
      ],
      checksum: 'SHA256: a3f5b8c1d2e4f7...',
      status: platform.isWindows && isPlatformSupported(platform) ? 'available' : 'unsupported',
      error: platform.isWindows ? undefined : 'Not available for your platform',
    };
    
    const windowsPortable: DownloadInfo = {
      id: 'windows-portable',
      platform: 'windows',
      version: '1.0.0',
      name: 'AVORA Desktop Portable',
      size: '238 MB',
      type: 'portable',
      description: 'Portable version for USB drives and removable media',
      requirements: [
        'Windows 10 / 11 (64-bit)',
        'Intel Core i5 or equivalent (AMD equivalent supported)',
        '8GB RAM (16GB recommended)',
        '4GB available storage',
      ],
      status: platform.isWindows && isPlatformSupported(platform) ? 'available' : 'unsupported',
      error: platform.isWindows ? undefined : 'Not available for your platform',
    };
    
    const macosDownload: DownloadInfo = {
      id: 'macos-installer',
      platform: 'macos',
      version: '1.0.0',
      name: 'AVORA Desktop Installer',
      size: 'TBD',
      type: 'installer',
      description: 'macOS installer with Apple Silicon optimization',
      requirements: [
        'macOS 11 Big Sur or later',
        'Intel Core i5 or equivalent',
        'Apple Silicon M1 or equivalent',
        '8GB RAM (16GB recommended)',
        '4GB available storage',
      ],
      status: platform.isMacOS && platform.isAppleSilicon ? 'available' : 
              platform.isMacOS ? 'available' : 'unsupported',
      error: platform.isMacOS ? undefined : 'Not available for your platform',
    };
    
    const linuxDownload: DownloadInfo = {
      id: 'linux-installer',
      platform: 'linux',
      version: '1.0.0',
      name: 'AVORA Desktop Linux',
      size: 'TBD',
      type: 'installer',
      description: 'Linux distribution package',
      requirements: [
        'Ubuntu 20.04 LTS or later',
        'Debian 10 or later',
        'Red Hat Enterprise Linux 8 or later',
        'Intel Core i5 or equivalent',
        '8GB RAM (16GB recommended)',
        '4GB available storage',
      ],
      status: platform.isLinux ? 'available' : 'unsupported',
      error: platform.isLinux ? undefined : 'Not available for your platform',
    };

    setDownloads([windowsDownload, windowsPortable, macosDownload, linuxDownload]);
  };

  // Fallback initialization for browsers without proper API support
  const initializeDownloadsFallback = () => {
    const downloads: DownloadInfo[] = [
      {
        id: 'windows-installer',
        platform: 'windows',
        version: '1.0.0',
        name: 'AVORA Desktop Setup',
        size: '245 MB',
        type: 'installer',
        description: 'Recommended installer for Windows systems',
        requirements: ['Windows 10 / 11 (64-bit)', '8GB RAM'],
        checksum: 'SHA256: a3f5b8c1d2e4f7...',
        status: 'available',
      },
      {
        id: 'windows-portable',
        platform: 'windows',
        version: '1.0.0',
        name: 'AVORA Desktop Portable',
        size: '238 MB',
        type: 'portable',
        description: 'Portable version for USB drives and removable media',
        requirements: ['Windows 10 / 11 (64-bit)', '8GB RAM'],
        status: 'available',
      },
      {
        id: 'macos-installer',
        platform: 'macos',
        version: '1.0.0',
        name: 'AVORA Desktop Installer',
        size: 'TBD',
        type: 'installer',
        description: 'macOS installer',
        requirements: ['macOS 11 or later', '8GB RAM'],
        status: 'available',
      },
      {
        id: 'linux-installer',
        platform: 'linux',
        version: '1.0.0',
        name: 'AVORA Desktop Linux',
        size: 'TBD',
        type: 'installer',
        description: 'Linux distribution package',
        requirements: ['Linux distribution', '8GB RAM'],
        status: 'available',
      },
    ];
    
    setDownloads(downloads);
    setIsSupported(true);
  };

  // Handle download with error resilience
  const handleDownload = async (downloadId: string) => {
    if (networkStatus === 'offline') {
      setDownloads(prev => prev.map(d => 
        d.id === downloadId 
          ? { ...d, status: 'error', error: 'Cannot download while offline' }
          : d
      ));
      return;
    }

    setCurrentDownload(downloadId);
    
    try {
      setDownloads(prev => prev.map(d => 
        d.id === downloadId ? { ...d, status: 'downloading' } : d
      ));

      // Simulate download process
      await simulateDownload(downloadId);
      
      setDownloads(prev => prev.map(d => 
        d.id === downloadId 
          ? { ...d, status: 'completed' }
          : d
      ));
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Download failed';
      
      setDownloads(prev => prev.map(d => 
        d.id === downloadId 
          ? { ...d, status: 'error', error: errorMessage }
          : d
      ));
    } finally {
      setCurrentDownload(null);
    }
  };

  // Simulate download with progressive updates
  const simulateDownload = async (downloadId: string): Promise<void> => {
    const totalSize = parseFloat(downloads.find(d => d.id === downloadId)?.size || '0 MB') * 1024 * 1024;
    const chunkSize = 5 * 1024 * 1024; // 5MB chunks
    const chunks = Math.ceil(totalSize / chunkSize);
    
    for (let i = 0; i < chunks; i++) {
      // Check if component is still mounted
      if (!document.querySelector('#download')) throw new Error('Component unmounted');
      
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));
      
      // Check for network errors
      if (networkStatus === 'offline') {
        throw new Error('Network connection lost');
      }
      
      // Update progress (this would normally be handled by a real download)
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'downloading':
        return <Loader2 size={16} className="animate-spin text-blue-400" />;
      case 'completed':
        return <CheckCircle size={16} className="text-green-400" />;
      case 'error':
        return <AlertCircle size={16} className="text-red-400" />;
      case 'unsupported':
        return <X size={16} className="text-gray-400" />;
      default:
        return <Download size={16} className="text-blue-400" />;
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'downloading':
        return 'text-blue-400';
      case 'completed':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      case 'unsupported':
        return 'text-gray-400';
      default:
        return 'text-blue-400';
    }
  };

  // Get platform icon
  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'windows':
        return <div className="w-6 h-6 bg-blue-500/20 rounded flex items-center justify-center">
          <span className="text-blue-400 text-xs font-bold">W</span>
        </div>;
      case 'macos':
        return <div className="w-6 h-6 bg-gray-500/20 rounded flex items-center justify-center">
          <span className="text-gray-400 text-xs font-bold">M</span>
        </div>;
      case 'linux':
        return <div className="w-6 h-6 bg-orange-500/20 rounded flex items-center justify-center">
          <span className="text-orange-400 text-xs font-bold">L</span>
        </div>;
      default:
        return null;
    }
  };

  return (
    <section id="download" className="relative py-32 bg-gradient-to-b from-[#0a0a0f] via-[#0d0d14] to-[#0a0a0f]">
      <div className="max-w-6xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Download AVORA
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Get started with AVORA AI on your system. Select the appropriate version for your operating system.
          </p>
        </motion.div>

        {/* Platform Detection Status */}
        {compatibility && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mb-12"
          >
            <div className="max-w-3xl mx-auto bg-white/[0.03] rounded-xl border border-white/[0.08] p-6 backdrop-blur-md">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Platform Detection</h3>
                <div className={cn(
                  "flex items-center gap-2 px-3 py-1 rounded-full text-sm",
                  networkStatus === 'online' ? 'bg-green-500/20 text-green-400' :
                  networkStatus === 'offline' ? 'bg-red-500/20 text-red-400' :
                  'bg-yellow-500/20 text-yellow-400'
                )}>
                  {networkStatus === 'online' ? <Zap size={14} /> :
                   networkStatus === 'offline' ? <AlertCircle size={14} /> :
                   <Loader2 size={14} className="animate-spin" />}
                  <span className="capitalize">{networkStatus}</span>
                </div>
              </div>
              
              {compatibility && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className={cn(
                      "w-3 h-3 rounded-full mx-auto mb-2",
                      compatibility.isWindows ? 'bg-blue-500' : 'bg-gray-600'
                    )} />
                    <span className="text-xs text-gray-400">Windows</span>
                  </div>
                  <div className="text-center">
                    <div className={cn(
                      "w-3 h-3 rounded-full mx-auto mb-2",
                      compatibility.isMacOS ? 'bg-gray-500' : 'bg-gray-600'
                    )} />
                    <span className="text-xs text-gray-400">macOS</span>
                  </div>
                  <div className="text-center">
                    <div className={cn(
                      "w-3 h-3 rounded-full mx-auto mb-2",
                      compatibility.isLinux ? 'bg-orange-500' : 'bg-gray-600'
                    )} />
                    <span className="text-xs text-gray-400">Linux</span>
                  </div>
                  <div className="text-center">
                    <div className={cn(
                      "w-3 h-3 rounded-full mx-auto mb-2",
                      compatibility.processorArchitecture === 'arm64' ? 'bg-purple-500' : 'bg-gray-600'
                    )} />
                    <span className="text-xs text-gray-400">ARM64</span>
                  </div>
                </div>
              )}
              
              {!isSupported && (
                <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                  <p className="text-sm text-yellow-400">
                    ⚠️ This platform may have limited functionality. Some features may not be available.
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Downloads Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <AnimatePresence>
            {downloads.map((download, index) => (
              <motion.div
                key={download.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-100px' }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="group"
              >
                <div className={cn(
                  "relative rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-xl p-6",
                  "transition-all duration-300 hover:border-white/[0.15] hover:bg-white/[0.04]",
                  download.status === 'unsupported' && "opacity-60"
                )}>
                  {/* Status indicator */}
                  <div className="absolute top-4 right-4">
                    {getStatusIcon(download.status)}
                  </div>

                  {/* Platform icon and label */}
                  <div className="flex items-center gap-3 mb-4">
                    {getPlatformIcon(download.platform)}
                    <div>
                      <h3 className="text-lg font-semibold text-white capitalize">
                        {download.platform}
                      </h3>
                      <span className={cn("text-xs", getStatusColor(download.status))}>
                        {download.status === 'available' ? ' Available' :
                         download.status === 'downloading' ? ' Downloading...' :
                         download.status === 'completed' ? ' Ready' :
                         download.status === 'error' ? ' Error' :
                         ' Not Supported'}
                      </span>
                    </div>
                  </div>

                  {/* Version and size */}
                  <div className="space-y-2 mb-4">
                    <p className="text-sm text-gray-300">
                      <span className="text-gray-500">Version:</span> {download.version}
                    </p>
                    <p className="text-sm text-gray-300">
                      <span className="text-gray-500">Size:</span> {download.size}
                    </p>
                    <p className="text-sm text-gray-300">
                      <span className="text-gray-500">Type:</span> {download.type}
                    </p>
                  </div>

                  {/* Description */}
                  <p className="text-sm text-gray-400 mb-4">
                    {download.description}
                  </p>

                  {/* Requirements button */}
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setShowRequirements(download.id)}
                    className="w-full mb-4 px-3 py-2 text-xs text-gray-400 hover:text-white border border-white/[0.08] rounded-lg hover:border-white/[0.15] transition-colors"
                  >
                    View Requirements
                  </motion.button>

                  {/* Download button */}
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleDownload(download.id)}
                    disabled={download.status === 'downloading' || download.status === 'completed' || download.status === 'unsupported'}
                    className={cn(
                      "w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium transition-all duration-300",
                      "disabled:opacity-50 disabled:cursor-not-allowed",
                      download.status === 'available' 
                        ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:shadow-[0_0_30px_rgba(96,165,250,0.3)]"
                        : download.status === 'completed'
                        ? "bg-green-500/20 text-green-400 border border-green-500/30"
                        : download.status === 'error'
                        ? "bg-red-500/20 text-red-400 border border-red-500/30"
                        : "bg-white/[0.03] text-gray-400 border border-white/[0.06]"
                    )}
                  >
                    {download.status === 'downloading' ? (
                      <>
                        <Loader2 size={16} className="animate-spin" />
                        <span>Downloading...</span>
                      </>
                    ) : download.status === 'completed' ? (
                      <>
                        <CheckCircle size={16} />
                        <span>Installed</span>
                      </>
                    ) : download.status === 'error' ? (
                      <>
                        <AlertCircle size={16} />
                        <span>Retry</span>
                      </>
                    ) : download.status === 'unsupported' ? (
                      <>
                        <X size={16} />
                        <span>Not Available</span>
                      </>
                    ) : (
                      <>
                        <Download size={16} />
                        <span>Download</span>
                      </>
                    )}
                  </motion.button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Requirements Modal */}
        <AnimatePresence>
          {showRequirements && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={() => setShowRequirements(null)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-[#0d0d14] border border-white/[0.1] rounded-2xl p-6 max-w-2xl w-full max-h-[80vh] overflow-auto"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold text-white">System Requirements</h3>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => setShowRequirements(null)}
                    className="p-2 hover:bg-white/[0.05] rounded-lg transition-colors"
                  >
                    <X size={20} className="text-gray-400" />
                  </motion.button>
                </div>
                
                {downloads.filter(d => d.id === showRequirements)[0] && (
                  <div>
                    <h4 className="text-lg font-medium text-white mb-3">
                      {downloads.filter(d => d.id === showRequirements)[0].name}
                    </h4>
                    <div className="space-y-2">
                      {downloads.filter(d => d.id === showRequirements)[0].requirements.map((req, index) => (
                        <div key={index} className="flex items-center gap-2">
                          <CheckCircle size={14} className="text-green-400" />
                          <span className="text-sm text-gray-300">{req}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Current Download Indicator */}
        <AnimatePresence>
          {currentDownload && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="fixed bottom-4 right-4 bg-[#0d0d14] border border-white/[0.1] rounded-xl p-4 backdrop-blur-md z-50"
            >
              <div className="flex items-center gap-3">
                <Loader2 size={20} className="animate-spin text-blue-400" />
                <div>
                  <p className="text-sm font-medium text-white">Downloading...</p>
                  <p className="text-xs text-gray-400">
                    {downloads.find(d => d.id === currentDownload)?.name}
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}

export default Downloads;