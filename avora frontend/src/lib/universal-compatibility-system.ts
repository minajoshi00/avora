/**
 * Universal Desktop Compatibility System
 * 
 * Comprehensive platform detection, feature testing, and graceful degradation
 * for maximum compatibility across all modern desktop and laptop computers.
 */

export interface UniversalCompatibilityInfo {
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

export interface FallbackStrategy {
  onWebGLError: 'fallback-canvas' | 'disable' | 'enable-2d';
  onWebGPUError: 'fallback-canvas' | 'disable';
  onWebAssemblyError: 'disable' | 'fallback-em' | 'enable';
  onServiceWorkerError: 'disable' | 'enable';
  onNetworkError: 'retry-later' | 'use-cache' | 'graceful-degradation';
  onIndexingError: 'disable' | 'enable';
}

export interface ErrorHandlingState {
  hasWebGLError: boolean;
  hasWebGPUError: boolean;
  hasWebAssemblyError: boolean;
  hasServiceWorkerError: boolean;
  hasNetworkError: boolean;
  hasIndexingError: boolean;
  lastNetworkError?: string;
  consecutiveNetworkErrors: number;
}

export class UniversalCompatibilitySystem {
  private static instance: UniversalCompatibilitySystem;
  private compatibilityInfo: UniversalCompatibilityInfo | null = null;
  private fallbackStrategy: FallbackStrategy;
  private errorHandlingState: ErrorHandlingState;
  private isInitialized = false;

  static getInstance(): UniversalCompatibilitySystem {
    if (!UniversalCompatibilitySystem.instance) {
      UniversalCompatibilitySystem.instance = new UniversalCompatibilitySystem();
    }
    return UniversalCompatibilitySystem.instance;
  }

  constructor() {
    this.fallbackStrategy = {
      onWebGLError: 'fallback-canvas',
      onWebGPUError: 'fallback-canvas',
      onWebAssemblyError: 'disable',
      onServiceWorkerError: 'disable',
      onNetworkError: 'graceful-degradation',
      onIndexingError: 'enable',
    };
    this.errorHandlingState = {
      hasWebGLError: false,
      hasWebGPUError: false,
      hasWebAssemblyError: false,
      hasServiceWorkerError: false,
      hasNetworkError: false,
      hasIndexingError: false,
      lastNetworkError: undefined,
      consecutiveNetworkErrors: 0,
    };
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Detect platform
      this.detectCompatibility();
      
      // Test critical features with fallbacks
      await this.testWebGLSupport();
      await this.testWebGPUSupport();
      await this.testWebAssemblySupport();
      await this.testServiceWorkerSupport();
      await this.testIndexedDBSupport();
      
      this.isInitialized = true;
      console.log('Universal Compatibility System initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Universal Compatibility System:', error);
      this.handleInitializationError(error as Error);
    }
  }

  private detectCompatibility(): void {
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

    this.compatibilityInfo = {
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
      supportsWebGL: true, // Will be tested
      supportsWebGPU: true, // Will be tested
      supportsWebAssembly: true, // Will be tested
      supportsServiceWorkers: true, // Will be tested
      supportsIndexedDB: true, // Will be tested
      prefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      prefersColorScheme: window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : window.matchMedia('(prefers-color-scheme: light)').matches
          ? 'light'
          : 'no-preference',
      performanceLevel: this.calculatePerformanceLevel(deviceMemory, hardwareConcurrency, pixelRatio),
    };
  }

  private detectAppleSilicon(userAgent: string): boolean {
    if (!navigator.platform) return false;
    
    const isApplePlatform = userAgent.includes('Macintosh') || userAgent.includes('Mac OS');
    
    if (!isApplePlatform) return false;
    
    if ('cpuClass' in navigator) {
      return navigator.cpuClass === 'Apple ';
    }
    
    if (userAgent.includes('ARM64') || userAgent.includes('aarch64')) {
      return true;
    }
    
    if (userAgent.includes('iPhone') || userAgent.includes('iPad')) {
      return false; // Not desktop
    }
    
    return false;
  }

  private detectProcessorArchitecture(userAgent: string): 'x64' | 'arm64' | 'unknown' {
    const ua = userAgent.toLowerCase();
    
    if (ua.includes('x64') || 
        ua.includes('win64') || 
        ua.includes('macintel') || 
        ua.includes('wow64')) {
      return 'x64';
    }
    
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

  private async testWebGLSupport(): Promise<void> {
    try {
      const canvas = document.createElement('canvas');
      const gl = (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')) as WebGLRenderingContext | null;
      
      if (!gl) {
        this.errorHandlingState.hasWebGLError = true;
        console.warn('WebGL not supported - will use fallback canvas');
        return;
      }
      
      // Test basic WebGL capabilities
      const glExt = gl.getExtension('OES_vertex_array_object');
      const supportsExtensions = !!(gl.getParameter(gl.MAX_VERTEX_TEXTURE_IMAGE_UNITS) > 0);
      
      if (!glExt || !supportsExtensions) {
        console.warn('Limited WebGL support - will use fallback');
        this.errorHandlingState.hasWebGLError = true;
      }
    } catch (error) {
      this.errorHandlingState.hasWebGLError = true;
      console.error('WebGL test failed:', error);
    }
  }

  private async testWebGPUSupport(): Promise<void> {
    try {
      if ('GPU' in navigator) {
        const gpu = await (navigator as any).gpu?.requestAdapter();
        if (gpu) {
          console.log('WebGPU supported');
          return;
        }
      }
      this.errorHandlingState.hasWebGPUError = true;
      console.warn('WebGPU not available - will use fallback');
    } catch (error) {
      this.errorHandlingState.hasWebGPUError = true;
      console.error('WebGPU test failed:', error);
    }
  }

  private async testWebAssemblySupport(): Promise<void> {
    try {
      if (typeof WebAssembly === 'object' && WebAssembly.validate) {
        const test = WebAssembly.validate(new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0]));
        if (!test) {
          this.errorHandlingState.hasWebAssemblyError = true;
          console.warn('WebAssembly validation failed - will use fallback');
        }
      } else {
        this.errorHandlingState.hasWebAssemblyError = true;
        console.warn('WebAssembly not supported - will use fallback');
      }
    } catch (error) {
      this.errorHandlingState.hasWebAssemblyError = true;
      console.error('WebAssembly test failed:', error);
    }
  }

  private async testServiceWorkerSupport(): Promise<void> {
    try {
      if ('serviceWorker' in navigator) {
        console.log('Service Worker API available');
      } else {
        this.errorHandlingState.hasServiceWorkerError = true;
        console.warn('Service Workers not supported - offline capabilities limited');
      }
    } catch (error) {
      this.errorHandlingState.hasServiceWorkerError = true;
      console.error('Service Worker test failed:', error);
    }
  }

  private async testIndexedDBSupport(): Promise<void> {
    try {
      if ('indexedDB' in window) {
        console.log('IndexedDB API available');
      } else {
        this.errorHandlingState.hasIndexingError = true;
        console.warn('IndexedDB not supported - local storage unavailable');
      }
    } catch (error) {
      this.errorHandlingState.hasIndexingError = true;
      console.error('IndexedDB test failed:', error);
    }
  }

  private calculatePerformanceLevel(
    deviceMemory: number,
    hardwareConcurrency: number,
    pixelRatio: number
  ): 'low' | 'medium' | 'high' | 'very-high' {
    const memoryScore = Math.min(deviceMemory / 8, 2);
    const cpuScore = Math.min(hardwareConcurrency / 12, 2);
    const dpiScore = Math.min(pixelRatio / 2, 2);
    
    const totalScore = memoryScore + cpuScore + dpiScore;
    
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

  public async testNetworkConnectivity(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const response = await fetch('/api/health', { 
        method: 'HEAD',
        signal: controller.signal,
        cache: 'no-store'
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        this.resetNetworkErrors();
        return true;
      }
      
      this.handleNetworkError('HTTP Error: ' + response.status);
      return false;
    } catch (error) {
      this.handleNetworkError(String(error));
      return false;
    }
  }

  private handleNetworkError(error: string): void {
    this.errorHandlingState.hasNetworkError = true;
    this.errorHandlingState.lastNetworkError = error;
    this.errorHandlingState.consecutiveNetworkErrors++;
    
    console.warn('Network error:', error, 'Consecutive errors:', this.errorHandlingState.consecutiveNetworkErrors);
    
    // Graceful degradation after multiple failures
    if (this.errorHandlingState.consecutiveNetworkErrors >= 3) {
      console.warn('Multiple network errors detected - implementing graceful degradation');
    }
  }

  private resetNetworkErrors(): void {
    if (this.errorHandlingState.consecutiveNetworkErrors >= 3) {
      console.log('Network connection restored - clearing error state');
    }
    this.errorHandlingState.hasNetworkError = false;
    this.errorHandlingState.lastNetworkError = undefined;
    this.errorHandlingState.consecutiveNetworkErrors = 0;
  }

  public shouldUseFallback(fallbackType: keyof FallbackStrategy): boolean {
    return this.errorHandlingState[`has${fallbackType.charAt(0).toUpperCase() + fallbackType.slice(1)}Error`] as boolean;
  }

  public getFallbackStrategy(): FallbackStrategy {
    return this.fallbackStrategy;
  }

  public getErrorState(): ErrorHandlingState {
    return { ...this.errorHandlingState };
  }

  public getCompatibilityInfo(): UniversalCompatibilityInfo | null {
    return this.compatibilityInfo ? { ...this.compatibilityInfo } : null;
  }

  public shouldEnableFeature(feature: string): boolean {
    if (!this.compatibilityInfo) return true;

    switch (feature) {
      case 'webgl':
        return !this.shouldUseFallback('onWebGLError') && this.compatibilityInfo.supportsWebGL;
      case 'webgpu':
        return !this.shouldUseFallback('onWebGPUError') && this.compatibilityInfo.supportsWebGPU;
      case 'webassembly':
        return !this.shouldUseFallback('onWebAssemblyError') && this.compatibilityInfo.supportsWebAssembly;
      case 'serviceworker':
        return !this.shouldUseFallback('onServiceWorkerError') && this.compatibilityInfo.supportsServiceWorkers;
      case 'indexeddb':
        return !this.shouldUseFallback('onIndexingError') && this.compatibilityInfo.supportsIndexedDB;
      default:
        return true;
    }
  }

  public async getOptimalConfiguration(): Promise<Record<string, any>> {
    await this.initialize();
    
    const config: Record<string, any> = {
      quality: 'high',
      animations: true,
      webgl: false,
      webgpu: false,
      webassembly: false,
      serviceworker: false,
      indexeddb: false,
    };

    // Apply fallback strategy
    if (this.shouldUseFallback('onWebGLError')) {
      config.webgl = this.fallbackStrategy.onWebGLError === 'disable';
    } else {
      config.webgl = true;
    }

    if (this.shouldUseFallback('onWebGPUError')) {
      config.webgpu = this.fallbackStrategy.onWebGPUError === 'disable';
    } else {
      config.webgpu = true;
    }

    if (this.shouldUseFallback('onWebAssemblyError')) {
      config.webassembly = this.fallbackStrategy.onWebAssemblyError === 'disable';
    } else {
      config.webassembly = true;
    }

    if (this.shouldUseFallback('onServiceWorkerError')) {
      config.serviceworker = this.fallbackStrategy.onServiceWorkerError === 'disable';
    } else {
      config.serviceworker = true;
    }

    if (this.shouldUseFallback('onIndexingError')) {
      config.indexeddb = this.fallbackStrategy.onIndexingError === 'disable';
    } else {
      config.indexeddb = true;
    }

    // Adjust quality based on device capabilities
    if (this.compatibilityInfo?.performanceLevel === 'low') {
      config.quality = 'medium';
      config.animations = false;
    } else if (this.compatibilityInfo?.performanceLevel === 'medium') {
      config.quality = 'medium';
      config.animations = true;
    }

    // Adjust for touch devices
    if (this.compatibilityInfo?.isTouchDevice) {
      config.animations = false;
    }

    // Adjust for reduced motion preference
    if (this.compatibilityInfo?.prefersReducedMotion) {
      config.animations = false;
    }

    return config;
  }

  private handleInitializationError(error: Error): void {
    console.error('Universal Compatibility System initialization failed:', error);
    
    // Fallback configuration
    this.isInitialized = true;
    this.compatibilityInfo = {
      isWindows: true,
      isMacOS: false,
      isLinux: false,
      isAppleSilicon: false,
      processorArchitecture: 'unknown',
      deviceMemory: 4,
      hardwareConcurrency: 4,
      screenWidth: 1920,
      screenHeight: 1080,
      pixelRatio: 1,
      colorDepth: 8,
      maxTouchPoints: 0,
      isTouchDevice: false,
      canHover: true,
      browser: 'unknown',
      browserVersion: '0',
      supportsWebGL: false,
      supportsWebGPU: false,
      supportsWebAssembly: false,
      supportsServiceWorkers: false,
      supportsIndexedDB: false,
      prefersReducedMotion: false,
      prefersColorScheme: 'dark',
      performanceLevel: 'low',
    };
  }

  reset(): void {
    this.compatibilityInfo = null;
    this.isInitialized = false;
    this.errorHandlingState = {
      hasWebGLError: false,
      hasWebGPUError: false,
      hasWebAssemblyError: false,
      hasServiceWorkerError: false,
      hasNetworkError: false,
      hasIndexingError: false,
      lastNetworkError: undefined,
      consecutiveNetworkErrors: 0,
    };
  }
}

export const universalCompatibilitySystem = UniversalCompatibilitySystem.getInstance();