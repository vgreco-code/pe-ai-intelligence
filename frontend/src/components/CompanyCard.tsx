import React from 'react';
import { Company, Score } from '../api/client';
import TierBadge from './TierBadge';
import { ExternalLink } from 'lucide-react';

interface CompanyCardProps {
  company: Company;
  score?: Score | null;
  onClick?: () => void;
  onDelete?: () => void;
}

export const CompanyCard: React.FC<CompanyCardProps> = ({ company, score, onClick, onDelete }) => {
  return (
    <div className="card p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={onClick}>
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-navy">{company.name}</h3>
          <p className="text-sm text-gray-600">{company.vertical}</p>
        </div>
        {score && (
          <div className="text-right">
            <div className="text-2xl font-bold text-teal">{score.composite_score.toFixed(2)}</div>
            <TierBadge tier={score.tier} className="text-xs mt-2" />
          </div>
        )}
      </div>

      {company.description && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">{company.description}</p>
      )}

      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        {company.employee_count && (
          <div>
            <span className="text-gray-500">Employees</span>
            <p className="font-semibold">{company.employee_count}</p>
          </div>
        )}
        {company.founded_year && (
          <div>
            <span className="text-gray-500">Founded</span>
            <p className="font-semibold">{company.founded_year}</p>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="flex space-x-2">
          {company.website && (
            <a
              href={`https://${company.website}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-teal hover:text-teal/80"
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink size={16} />
            </a>
          )}
        </div>

        {onDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="btn-danger text-xs py-1 px-2"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
};

export default CompanyCard;
