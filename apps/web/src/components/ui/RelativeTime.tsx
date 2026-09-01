'use client';

import { useState, useEffect } from 'react';

interface RelativeTimeProps {
  date: string | Date;
  className?: string;
}

export function RelativeTime({ date, className }: RelativeTimeProps) {
  const [relative, setRelative] = useState('');

  useEffect(() => {
    const updateRelative = () => {
      const now = new Date();
      const then = new Date(date);
      const diffMs = now.getTime() - then.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) setRelative('Just now');
      else if (diffMins < 60) setRelative(`${diffMins}m ago`);
      else if (diffHours < 24) setRelative(`${diffHours}h ago`);
      else if (diffDays < 7) setRelative(`${diffDays}d ago`);
      else setRelative(new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      }));
    };

    updateRelative();
    const interval = setInterval(updateRelative, 60000);
    return () => clearInterval(interval);
  }, [date]);

  return <span className={className}>{relative || '...'}</span>;
}