import React, { useEffect, useState } from 'react';
import { jobsApi, Job } from '../api/client';

interface JobStatusProps {
  jobId: string;
  onComplete?: () => void;
}

export const JobStatus: React.FC<JobStatusProps> = ({ jobId, onComplete }) => {
  const [job, setJob] = useState<Job | null>(null);
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    const connection = jobsApi.subscribe(jobId);

    connection.onopen = () => {
      console.log('WebSocket connected');
    };

    connection.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'status' || message.type === 'progress') {
        setJob({
          id: message.job_id,
          job_type: 'research',
          status: message.status,
          progress: message.progress,
          total_companies: message.total_companies,
          completed_companies: message.completed_companies,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });

        if (message.message) {
          setMessages((prev) => [...prev, message.message]);
        }

        if (message.status === 'completed' || message.status === 'failed') {
          onComplete?.();
          connection.close();
        }
      }
    };

    connection.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      connection.close();
    };
  }, [jobId, onComplete]);

  if (!job) {
    return <div className="loading">Connecting to job stream...</div>;
  }

  return (
    <div className="card p-6 space-y-4">
      <h3 className="text-lg font-semibold">Job Progress</h3>

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Progress</span>
          <span>{job.progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-teal h-2 rounded-full transition-all duration-300"
            style={{ width: `${job.progress}%` }}
          ></div>
        </div>
      </div>

      <div className="text-sm text-gray-600">
        <p>Completed: {job.completed_companies} / {job.total_companies}</p>
        <p>Status: <span className="font-semibold">{job.status}</span></p>
      </div>

      {messages.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4 max-h-40 overflow-y-auto">
          <p className="text-xs font-semibold text-gray-600 mb-2">Activity Log</p>
          <div className="space-y-1">
            {messages.slice(-5).map((msg, idx) => (
              <p key={idx} className="text-xs text-gray-600">{msg}</p>
            ))}
          </div>
        </div>
      )}

      {job.status === 'failed' && job.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm error-text">Error: {job.error_message}</p>
        </div>
      )}
    </div>
  );
};

export default JobStatus;
