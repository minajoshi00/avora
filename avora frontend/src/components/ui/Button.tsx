import { type ButtonHTMLAttributes, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';
import { useSound } from '../../hooks/useSound';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
  magnetic?: boolean;
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'right',
  loading = false,
  className,
  disabled,
  magnetic = false,
  ...props
}: ButtonProps) {
  const { play } = useSound();
  const baseStyles =
    'inline-flex items-center justify-center gap-2 font-medium transition-all duration-300 rounded-full select-none';

  const variants = {
    primary:
      'bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:shadow-[0_8px_30px_rgba(96,165,250,0.4)] shadow-[0_4px_20px_rgba(96,165,250,0.3)] relative overflow-hidden',
    secondary:
      'bg-white/5 text-white border border-white/10 hover:bg-white/10 hover:border-white/20 backdrop-blur-sm hover:shadow-[0_8px_30px_rgba(255,255,255,0.1)]',
    ghost:
      'text-text-secondary hover:text-text-primary hover:bg-white/5',
    outline:
      'border border-white/10 text-text-primary hover:border-blue-500/50 hover:text-blue-400 bg-transparent hover:shadow-[0_4px_20px_rgba(96,165,250,0.2)]',
  };

  const sizes = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
  };

  return (
    <motion.button
      whileHover={magnetic ? { scale: 1.05, y: -2, x: 0 } : { scale: disabled ? 1 : 1.05, y: -2 }}
      whileTap={{ scale: disabled ? 1 : 0.95, y: 0 }}
      onHoverStart={() => play('hover')}
      onTap={() => play('click')}
      transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      className={cn(
        baseStyles,
        variants[variant],
        sizes[size],
        loading && 'opacity-70 cursor-not-allowed',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={disabled || loading}
      {...(props as React.ComponentProps<typeof motion.button>)}
    >
      {variant === 'primary' && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
          initial={{ x: '-100%' }}
          whileHover={{ x: '100%' }}
          transition={{ duration: 0.6, ease: 'easeInOut' }}
        />
      )}
      <span className="relative z-10 flex items-center gap-2">
        {loading ? (
          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <>
            {icon && iconPosition === 'left' && icon}
            {children}
            {icon && iconPosition === 'right' && icon}
          </>
        )}
      </span>
    </motion.button>
  );
}
