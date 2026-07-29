import { cn } from '../../lib/utils';

interface AvoraLogoProps {
  className?: string;
  width?: number;
  height?: number;
}

export function AvoraLogo({ className, width = 120, height = 32 }: AvoraLogoProps) {
  return (
    <img
      src="/nova-logo.svg.png"
      alt="AVORA"
      className={cn('select-none', className)}
      width={width}
      height={height}
      draggable={false}
    />
  );
}

export default AvoraLogo;
