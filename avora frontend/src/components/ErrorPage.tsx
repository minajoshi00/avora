'use client';

import { motion } from 'framer-motion';
import { Home, RefreshCw, AlertTriangle } from 'lucide-react';
import { Button } from './ui/Button';

interface ErrorPageProps {
  statusCode?: number;
  message?: string;
  onRetry?: () => void;
}

export function ErrorPage({ statusCode = 404, message, onRetry }: ErrorPageProps) {
  const getStatusContent = () => {
    switch (statusCode) {
      case 404:
        return {
          title: 'Page Not Found',
          description: 'The page you\'re looking for doesn\'t exist or has been moved.',
          icon: Home,
        };
      case 500:
        return {
          title: 'Server Error',
          description: 'Something went wrong on our end. Please try again later.',
          icon: AlertTriangle,
        };
      case 403:
        return {
          title: 'Access Denied',
          description: 'You don\'t have permission to access this page.',
          icon: AlertTriangle,
        };
      default:
        return {
          title: 'Error',
          description: message || 'An unexpected error occurred.',
          icon: AlertTriangle,
        };
    }
  };

  const { title, description, icon: Icon } = getStatusContent();

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="text-center max-w-md"
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 300, damping: 25 }}
          className="mb-8"
        >
          <div className="w-24 h-24 mx-auto rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-400/30 flex items-center justify-center">
            <Icon size={48} className="text-blue-400" />
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-4xl font-bold text-white mb-4"
        >
          {statusCode}
        </motion.h1>

        <motion.h2
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="text-xl font-semibold text-white mb-3"
        >
          {title}
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-gray-400 mb-8 leading-relaxed"
        >
          {description}
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Button
            size="lg"
            icon={<Home size={18} />}
            onClick={() => window.location.hash = ''}
          >
            Go Home
          </Button>
          {onRetry && (
            <Button
              size="lg"
              variant="outline"
              icon={<RefreshCw size={18} />}
              onClick={onRetry}
            >
              Try Again
            </Button>
          )}
        </motion.div>
      </motion.div>
    </div>
  );
}

export default ErrorPage;