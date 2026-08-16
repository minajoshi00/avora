/**
 * AVORA Download Version Data Architecture
 * 
 * To add a new version, simply add an entry to the `versions` array.
 * The UI will automatically pick up the changes.
 */

export interface VersionReleaseNote {
  type: 'feature' | 'improvement' | 'fix' | 'note';
  text: string;
}

export interface VersionPlatform {
  platform: 'windows' | 'macos' | 'linux';
  url: string; // Direct download URL for the installer
  size: string;
  type: 'installer' | 'portable';
  checksum?: string; // SHA256 checksum for integrity verification
  fileName?: string; // Optional: filename for the installer
}

export interface Version {
  version: string;
  releaseDate: string;
  label: 'stable' | 'beta' | 'experimental';
  isLatest?: boolean;
  title: string;
  description: string;
  systemRequirements: string[];
  features: string[];
  improvements: string[];
  bugFixes: string[];
  platforms: VersionPlatform[];
  releaseNotes: VersionReleaseNote[];
}

export const versions: Version[] = [
  {
    version: '1.0.0',
    releaseDate: '2026-07-20',
    label: 'stable',
    isLatest: true,
    title: 'AVORA Desktop',
    description:
      'The first stable release of AVORA. Experience a new kind of personal intelligence that understands, remembers, and evolves with you.',
    systemRequirements: [
      'Windows 10 / 11 (64-bit)',
      'Intel Core i5 or equivalent (AMD equivalent supported)',
      'Apple Silicon M1 or equivalent (Macs only)',
      '8GB RAM (16GB recommended)',
      '4GB available storage',
      'Internet connection for initial setup',
    ],
    features: [
      'Natural conversational AI with context memory',
      'Real-time adaptive intelligence engine',
      'Voice input and natural language understanding',
      'Multi-session context persistence',
      'Local-first architecture with optional cloud sync',
      'Privacy-focused with end-to-end encryption',
      'Dark mode and customizable themes',
      'Offline mode for core features',
    ],
    improvements: [
      'Optimized neural response time - 40% faster than beta',
      'Improved memory retention across sessions',
      'Enhanced natural language understanding',
      'Better resource management and lower RAM usage',
      'Refined UI/UX with smoother animations',
    ],
    bugFixes: [
      'Fixed intermittent connectivity issues',
      'Resolved memory leak in long-running sessions',
      'Fixed voice recognition accuracy improvements',
      'Addressed UI glitches on high-DPI displays',
      'Fixed export functionality for chat history',
    ],
    platforms: [
      {
        platform: 'windows',
        url: 'https://github.com/minajoshi00/avora/releases/download/v1.0.0/AVORA-Setup.exe',
        size: '245 MB',
        type: 'installer',
        checksum: 'SHA256: a3f5b8c1d2e4f7...',
      },
      {
        platform: 'windows',
        url: 'https://github.com/minajoshi00/avora/releases/download/v1.0.0/AVORA-Setup.exe',
        size: '238 MB',
        type: 'portable',
      },
      {
        platform: 'macos',
        url: '#',
        size: 'TBD',
        type: 'installer',
      },
      {
        platform: 'linux',
        url: '#',
        size: 'TBD',
        type: 'installer',
      },
    ],
    releaseNotes: [
      { type: 'feature', text: 'First stable release of AVORA Desktop' },
      { type: 'feature', text: 'Natural conversational AI with memory' },
      { type: 'improvement', text: '40% faster response times' },
      { type: 'fix', text: 'Memory leak and connectivity fixes' },
    ],
  },
  {
    version: '0.9.0',
    releaseDate: '2026-06-15',
    label: 'beta',
    title: 'AVORA Desktop Beta',
    description:
      'Beta release introducing major improvements to the intelligence engine and user experience.',
    systemRequirements: [
      'Windows 10 / 11 (64-bit)',
      'Intel Core i5 or equivalent',
      '8GB RAM',
      '1.5GB available storage',
    ],
    features: [
      'Conversational AI with context awareness',
      'Voice input support (beta)',
      'Multi-turn conversation memory',
      'Real-time response streaming',
      'Basic customization options',
    ],
    improvements: [
      'Reduced response latency by 25%',
      'Improved conversation coherence',
      'Better error handling and recovery',
    ],
    bugFixes: [
      'Fixed crash on long conversations',
      'Fixed UI scaling issues',
      'Fixed text rendering on some displays',
    ],
    platforms: [
      {
        platform: 'windows',
        url: '#',
        size: '220 MB',
        type: 'installer',
      },
    ],
    releaseNotes: [
      { type: 'feature', text: 'Beta release with major improvements' },
      { type: 'improvement', text: '25% faster response latency' },
      { type: 'fix', text: 'Crash fixes and stability improvements' },
    ],
  },
  {
    version: '0.8.0',
    releaseDate: '2026-05-01',
    label: 'beta',
    title: 'AVORA Desktop Beta',
    description:
      'Second beta introducing voice support and improved memory systems.',
    systemRequirements: [
      'Windows 10 / 11 (64-bit)',
      'Intel Core i5 or equivalent',
      '8GB RAM',
      '1GB available storage',
    ],
    features: [
      'Initial conversational AI engine',
      'Text-based interaction with context',
      'Basic memory and recall',
      'Session management',
    ],
    improvements: [
      'Improved response quality',
      'Better context understanding',
      'Optimized performance',
    ],
    bugFixes: [
      'Fixed installation issues on some systems',
      'Fixed text input handling',
    ],
    platforms: [
      {
        platform: 'windows',
        url: '#',
        size: '195 MB',
        type: 'installer',
      },
    ],
    releaseNotes: [
      { type: 'feature', text: 'Voice support and improved memory' },
      { type: 'improvement', text: 'Better response quality and context' },
    ],
  },
  {
    version: '0.7.0',
    releaseDate: '2026-04-01',
    label: 'experimental',
    title: 'AVORA Desktop Preview',
    description:
      'The very first experimental preview of AVORA. A glimpse into the future of personal AI.',
    systemRequirements: [
      'Windows 10 / 11 (64-bit)',
      'Intel Core i5 or equivalent',
      '8GB RAM',
      '1GB available storage',
    ],
    features: [
      'Experimental AI conversation engine',
      'Basic text interaction',
      'Simple response system',
      'Minimal UI',
    ],
    improvements: [],
    bugFixes: [],
    platforms: [
      {
        platform: 'windows',
        url: '#',
        size: '180 MB',
        type: 'installer',
      },
    ],
    releaseNotes: [
      { type: 'note', text: 'First experimental preview release' },
    ],
  },
];

export function getLatestVersion(): Version {
  return versions.find((v) => v.isLatest) || versions[0];
}

export function getVersionByNumber(version: string): Version | undefined {
  return versions.find((v) => v.version === version);
}

export function getStableVersions(): Version[] {
  return versions.filter((v) => v.label === 'stable');
}

export function getDownloadUrl(version: Version, platform: 'windows' | 'macos' | 'linux'): string | null {
  const p = version.platforms.find((pl) => pl.platform === platform);
  return p?.url || null;
}