import React from 'react';

interface TierBadgeProps {
  tier: string;
  className?: string;
}

export const TierBadge: React.FC<TierBadgeProps> = ({ tier, className = '' }) => {
  const getTierStyles = (tier: string) => {
    switch (tier) {
      case 'AI-Ready':
        return 'tier-badge-ready';
      case 'AI-Buildable':
        return 'tier-badge-buildable';
      case 'AI-Emerging':
        return 'tier-badge-emerging';
      case 'AI-Limited':
        return 'tier-badge-limited';
      default:
        return 'bg-gray-100 text-gray-700 border border-gray-300';
    }
  };

  return (
    <span className={`tier-badge ${getTierStyles(tier)} ${className}`}>
      {tier}
    </span>
  );
};

export default TierBadge;
