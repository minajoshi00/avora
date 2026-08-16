/*
 * Platform Detection and System Information
 * 
 * Detects operating system, processor architecture, and hardware capabilities
 * to ensure optimal performance and compatibility across all platforms.
 */

export interface PlatformInfo {
  // Operating System Detection
  isWindows: boolean;
  isMacOS: boolean;
  isLinux: boolean;
  isAppleSilicon: boolean;
  
  // Processor Architecture
  processorArchitecture: 'x64' | 'arm64' | 'unknown';
  
  // Memory and Performance
  deviceMemory: number; // GB
  hardwareConcurrency: number; // CPU cores
  
  // Display Information
  screenWidth: number;
  screenHeight: number;
  pixelRatio: number;
  colorDepth: number;
  
  // Touch and Input
  maxTouchPoints: number;
  isTouchDevice: boolean;
  canHover: boolean;
  
  // Browser Information
  browser: string;
  browserVersion: string;
  
  // Feature Support
  supportsWebGL: boolean;
  supportsWebGPU: boolean;
  supportsWebAssembly: boolean;
  supportsServiceWorkers: boolean;
  supportsIndexedDB: boolean;
  
  // Accessibility
  prefersReducedMotion: boolean;
  prefersColorScheme: 'dark' | 'light' | 'no-preference';
  
  // Performance tier
  performanceLevel: 'low' | 'medium' | 'high' | 'very-high';
}

export class PlatformDetector {
  private static instance: PlatformDetector;
  private platformInfo: PlatformInfo | null = null;

  static getInstance(): PlatformDetector {
    if (!PlatformDetector.instance) {
      PlatformDetector.instance = new PlatformDetector();
    }
    return PlatformDetector.instance;
  }

  detectPlatform(): PlatformInfo {
    if (this.platformInfo) {
      return this.platformInfo;
    }

    const userAgent = navigator.userAgent;
    const screen = window.screen;
    const nav = navigator;

    // Operating System Detection
    const isWindows = userAgent.includes('Windows');
    const isMacOS = userAgent.includes('Macintosh') || userAgent.includes('Mac OS');
    const isLinux = userAgent.includes('Linux');
    
    // Apple Silicon Detection
    const isAppleSilicon = this.detectAppleSilicon(userAgent);
    
    // Processor Architecture Detection
    const processorArchitecture = this.detectProcessorArchitecture(userAgent);
    
    // Memory and Performance
    const deviceMemory = (nav as any).deviceMemory || 4;
    const hardwareConcurrency = nav.hardwareConcurrency || 2;
    
    // Display Information
    const screenWidth = screen.width;
    const screenHeight = screen.height;
    const pixelRatio = window.devicePixelRatio || 1;
    const colorDepth = screen.colorDepth;
    
    // Touch and Input
    const maxTouchPoints = nav.maxTouchPoints || 0;
    const isTouchDevice = 'ontouchstart' in window || maxTouchPoints > 0;
    const canHover = !isTouchDevice && window.matchMedia('(hover: hover)').matches;
    
    // Browser Information
    const browser = this.detectBrowser(userAgent);
    const browserVersion = this.detectBrowserVersion(userAgent);
    
    // Feature Support
    const supportsWebGL = this.detectWebGLSupport();
    const supportsWebGPU = 'gpu' in nav || false;
    const supportsWebAssembly = this.detectWebAssemblySupport();
    const supportsServiceWorkers = 'serviceWorker' in navigator;
    const supportsIndexedDB = 'indexedDB' in window;
    
    // Accessibility
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const prefersColorScheme = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : window.matchMedia('(prefers-color-scheme: light)').matches
        ? 'light'
        : 'no-preference';
    
    // Performance tier calculation
    const performanceLevel = this.calculatePerformanceLevel(
      deviceMemory,
      hardwareConcurrency,
      pixelRatio
    );

    this.platformInfo = {
      isWindows,
      isMacOS,
      isLinux,
      isAppleSilicon,
      processorArchitecture,
      deviceMemory,
      hardwareConcurrency,
      screenWidth,
      screenHeight,
      pixelRatio,
      colorDepth,
      maxTouchPoints,
      isTouchDevice,
      canHover,
      browser,
      browserVersion,
      supportsWebGL,
      supportsWebGPU,
      supportsWebAssembly,
      supportsServiceWorkers,
      supportsIndexedDB,
      prefersReducedMotion,
      prefersColorScheme,
      performanceLevel,
    };

    return this.platformInfo;
  }

  private detectAppleSilicon(userAgent: string): boolean {
    if (!navigator.platform) return false;
    
    // Check for Apple Silicon indicators
    const isApplePlatform = userAgent.includes('Macintosh') || userAgent.includes('Mac OS');
    
    if (!isApplePlatform) return false;
    
    // Check CPU class for Apple Silicon
    if ('cpuClass' in navigator) {
      return navigator.cpuClass === 'Apple ';
    }
    
    // Check for ARM64 architecture on macOS
    if (userAgent.includes('ARM64') || userAgent.includes('aarch64')) {
      return true;
    }
    
    // Legacy check for iOS devices (should not be desktop)
    if (userAgent.includes('iPhone') || userAgent.includes('iPad')) {
      return false; // Not desktop
    }
    
    return false;
  }

  private detectProcessorArchitecture(userAgent: string): 'x64' | 'arm64' | 'unknown' {
    const ua = userAgent.toLowerCase();
    
    // Check for x64 indicators
    if (ua.includes('x64') || 
        ua.includes('win64') || 
        ua.includes('macintel') || 
        ua.includes('wow64')) {
      return 'x64';
    }
    
    // Check for ARM64 indicators
    if (ua.includes('arm') || 
        ua.includes('aarch64') || 
        ua.includes('iphone') || 
        ua.includes('ipad')) {
      return 'arm64';
    }
    
    return 'unknown';
  }

  private detectBrowser(userAgent: string): string {
    const ua = userAgent.toLowerCase();
    
    if (ua.includes('firefox')) {
      return 'firefox';
    } else if (ua.includes('edg')) {
      return 'edge';
    } else if (ua.includes('chrome')) {
      return 'chrome';
    } else if (ua.includes('safari')) {
      return 'safari';
    } else if (ua.includes('opera')) {
      return 'opera';
    }
    
    return 'unknown';
  }

  private detectBrowserVersion(userAgent: string): string {
    const versionMatch = userAgent.match(/(?:Firefox|Edge|Chrome|Safari|Opera)\/?\s*(\d+\.\d+)/);
    return versionMatch ? versionMatch[1] : '0';
  }

  private detectWebGLSupport(): boolean {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      return !!gl;
    }

  private detectWebAssemblySupport(): boolean {
      if (typeof WebAssembly === 'object' && WebAssembly.validate) {
        return WebAssembly.validate(new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0]));
      }
      
      return false;
    }

  private calculatePerformanceLevel(
    deviceMemory: number,
    hardwareConcurrency: number,
    pixelRatio: number
  ): 'low' | 'medium' | 'high' | 'very-high' {
    // Weight factors for different hardware metrics
    const memoryScore = Math.min(deviceMemory / 8, 2); // 8GB max rating
    const cpuScore = Math.min(hardwareConcurrency / 12, 2); // 12 cores max rating
    const dpiScore = Math.min(pixelRatio / 2, 2); // 2x DPI max rating
    
    // Calculate total score (max 6.0)
    const totalScore = memoryScore + cpuScore + dpiScore;
    
    // Map to performance levels
    if (totalScore < 1.5) {
      return 'low';
    } else if (totalScore < 3.0) {
      return 'medium';
    } else if (totalScore < 4.5) {
      return 'high';
    } else {
      return 'very-high';
    }
  }

  reset(): void {
    this.platformInfo = null;
  }
}

export const platformDetector = PlatformDetector.getInstance();