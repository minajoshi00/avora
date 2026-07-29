/**
 * Device Capabilities Detection
 * 
 * Comprehensive detection of device hardware and software capabilities
 * to ensure compatibility across all supported platforms.
 */

export interface DeviceCapabilities {
  isTouchDevice: boolean;
  maxTouchPoints: number;
  screenResolution: {
    width: number;
    height: number;
  };
  pixelRatio: number;
  deviceMemory: number;
  hardwareConcurrency: number;
  isLowEndDevice: boolean;
  canHover: boolean;
  supportsWebGL: boolean;
  supportsWebGPU: boolean;
  performanceLevel: 'low' | 'medium' | 'high' | 'very-high';
}

export interface DisplayCapabilities {
  isHighDPI: boolean;
  effectivePixelRatio: number;
  preferredColorScheme?: 'dark' | 'light' | 'no-preference';
  supportsReducedMotion: boolean;
  matchesReducedMotion: boolean;
  matchesDarkMode: boolean;
}

export interface SystemCapabilities {
  isWindows: boolean;
  isMacOS: boolean;
  isLinux: boolean;
  isAppleSilicon: boolean;
  processorArchitecture: 'x64' | 'arm64' | 'unknown';
  browser: string;
  browserVersion: string;
  supportsWebAssembly: boolean;
  supportsServiceWorkers: boolean;
  supportsIndexedDB: boolean;
}

export class CapabilitiesDetector {
  private static instance: CapabilitiesDetector;
  private capabilities: DeviceCapabilities | null = null;
  private displayCapabilities: DisplayCapabilities | null = null;
  private systemCapabilities: SystemCapabilities | null = null;

  static getInstance(): CapabilitiesDetector {
    if (!CapabilitiesDetector.instance) {
      CapabilitiesDetector.instance = new CapabilitiesDetector();
    }
    return CapabilitiesDetector.instance;
  }

  detectDeviceCapabilities(): DeviceCapabilities {
    if (this.capabilities) {
      return this.capabilities;
    }

    const nav = navigator;
    const screen = window.screen;

    const isTouchDevice = 'ontouchstart' in window || nav.maxTouchPoints > 0;
    const maxTouchPoints = nav.maxTouchPoints || 0;

    const screenResolution = {
      width: screen.width,
      height: screen.height,
    };

    const pixelRatio = window.devicePixelRatio || 1;
    const deviceMemory = (nav as any).deviceMemory || 4;
    const hardwareConcurrency = nav.hardwareConcurrency || 2;

    const isLowEndDevice = this.detectLowEndDevice(
      deviceMemory,
      hardwareConcurrency,
      pixelRatio
    );

    const canHover = !isTouchDevice && window.matchMedia('(hover: hover)').matches;

    const capabilities = {
      isTouchDevice,
      maxTouchPoints,
      screenResolution,
      pixelRatio,
      deviceMemory,
      hardwareConcurrency,
      isLowEndDevice,
      canHover,
      supportsWebGL: this.detectWebGLSupport(),
      supportsWebGPU: this.detectWebGPUSupport(),
      performanceLevel: this.detectPerformanceLevel(),
    };

    this.capabilities = capabilities;
    return capabilities;
  }

  detectDisplayCapabilities(): DisplayCapabilities {
    if (this.displayCapabilities) {
      return this.displayCapabilities;
    }

    const prefersColorScheme = window.matchMedia('(prefers-color-scheme: dark)')
      .matches
      ? 'dark'
      : window.matchMedia('(prefers-color-scheme: light)').matches
        ? 'light'
        : 'no-preference';

    const supportsReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches;

    const effectivePixelRatio = window.devicePixelRatio || 1;
    const isHighDPI = effectivePixelRatio > 1;

    const displayCapabilities = {
      isHighDPI,
      effectivePixelRatio,
      preferredColorScheme: prefersColorScheme,
      supportsReducedMotion,
      matchesReducedMotion: window.matchMedia(
        '(prefers-reduced-motion: reduce)'
      ).matches,
      matchesDarkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
    };

    this.displayCapabilities = displayCapabilities;
    return displayCapabilities;
  }

  detectSystemCapabilities(): SystemCapabilities {
    if (this.systemCapabilities) {
      return this.systemCapabilities;
    }

    const userAgent = navigator.userAgent;

    const isWindows = userAgent.includes('Windows');
    const isMacOS = userAgent.includes('Macintosh') || userAgent.includes('Mac OS');
    const isLinux = userAgent.includes('Linux');
    const isAppleSilicon =
      isMacOS &&
      (userAgent.includes('ARM64') ||
        userAgent.includes('aarch64') ||
        (navigator as any).platform.includes('iPhone') ||
        (navigator as any).platform.includes('Mac')) &&
      window.navigator?.cpuClass === 'Apple '
        ? true
        : false;

    const processorArchitecture = this.detectProcessorArchitecture();

    const browser = this.detectBrowser();
    const browserVersion = this.detectBrowserVersion();

    const systemCapabilities = {
      isWindows,
      isMacOS,
      isLinux,
      isAppleSilicon,
      processorArchitecture,
      browser,
      browserVersion,
      supportsWebAssembly: this.detectWebAssemblySupport(),
      supportsServiceWorkers: 'serviceWorker' in navigator,
      supportsIndexedDB: 'indexedDB' in window,
    };

    this.systemCapabilities = systemCapabilities;
    return systemCapabilities;
  }

  private detectLowEndDevice(
    deviceMemory: number,
    hardwareConcurrency: number,
    pixelRatio: number
  ): boolean {
    return (
      deviceMemory < 4 ||
      hardwareConcurrency < 4 ||
      pixelRatio > 2 ||
      (deviceMemory < 6 && hardwareConcurrency < 6)
    );
  }

  private detectWebGLSupport(): boolean {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      return !!gl;
    } catch (e) {
      return false;
    }
  }

  private detectWebGPUSupport(): boolean {
    return 'gpu' in navigator || false;
  }

  private detectPerformanceLevel(): DeviceCapabilities['performanceLevel'] {
    const capabilities = this.detectDeviceCapabilities();

    if (capabilities.deviceMemory >= 8 && capabilities.hardwareConcurrency >= 8) {
      return 'very-high';
    } else if (capabilities.deviceMemory >= 4 && capabilities.hardwareConcurrency >= 4) {
      return 'high';
    } else if (capabilities.deviceMemory >= 2 && capabilities.hardwareConcurrency >= 2) {
      return 'medium';
    } else {
      return 'low';
    }
  }

  private detectProcessorArchitecture(): SystemCapabilities['processorArchitecture'] {
    const userAgent = navigator.userAgent.toLowerCase();

    if (userAgent.includes('x64') || userAgent.includes('win64') || userAgent.includes('macintel')) {
      return 'x64';
    } else if (userAgent.includes('arm') || userAgent.includes('aarch64') || userAgent.includes('iphone')) {
      return 'arm64';
    }

    return 'unknown';
  }

  private detectBrowser(): string {
    const userAgent = navigator.userAgent;

    if (userAgent.includes('Firefox')) {
      return 'firefox';
    } else if (userAgent.includes('Edg')) {
      return 'edge';
    } else if (userAgent.includes('Chrome') || userAgent.includes('Safari')) {
      return 'chrome';
    } else if (userAgent.includes('Opera')) {
      return 'opera';
    }

    return 'unknown';
  }

  private detectBrowserVersion(): string {
    const userAgent = navigator.userAgent;

    const versionMatch = userAgent.match(/(?:Firefox|Edge|Chrome|Safari|Opera)\/?\s*(\d+\.\d+)/);
    return versionMatch ? versionMatch[1] : '0';
  }

  private detectWebAssemblySupport(): boolean {
    try {
      if (typeof WebAssembly === 'object' && WebAssembly.validate) {
        return WebAssembly.validate(new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0]));
      }
    } catch (e) {}

    return false;
  }

  reset(): void {
    this.capabilities = null;
    this.displayCapabilities = null;
    this.systemCapabilities = null;
  }
}

export const capabilitiesDetector = CapabilitiesDetector.getInstance();