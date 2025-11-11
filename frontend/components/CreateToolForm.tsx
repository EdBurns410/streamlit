import JSZip from 'jszip';
import { FormEvent, useState } from 'react';
import api from '../lib/api';
import { useAuth } from './AuthContext';

interface CreateToolFormProps {
  onCreated: (toolId: number) => void;
}

export function CreateToolForm({ onCreated }: CreateToolFormProps) {
  const { token } = useAuth();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [uploadMode, setUploadMode] = useState<'paste' | 'file'>('paste');
  const [appSource, setAppSource] = useState('');
  const [requirements, setRequirements] = useState('streamlit>=1.32.0');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createTool = async () => {
    const { data } = await api.post(
      '/v1/tools',
      { name, description },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return data.id as number;
  };

  const uploadVersion = async (toolId: number) => {
    const formData = new FormData();
    if (uploadMode === 'paste') {
      const archive = new JSZip();
      archive.file('app.py', appSource);
      if (requirements.trim().length > 0) {
        archive.file('requirements.txt', requirements);
      }
      const blob = await archive.generateAsync({ type: 'blob' });
      formData.append('file', blob, 'bundle.zip');
    } else if (file) {
      formData.append('file', file, file.name);
    }
    await api.post(`/v1/tools/${toolId}/versions`, formData, {
      headers: { Authorization: `Bearer ${token}` }
    });
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!token) {
      setError('Please sign in first.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const toolId = await createTool();
      await uploadVersion(toolId);
      onCreated(toolId);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Unable to create tool');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-xl">
      <h2 className="text-lg font-semibold text-white mb-4">Create a Streamlit Tool</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        {!token && (
          <div className="rounded-md border border-amber-500/60 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
            Sign in to save and deploy your tools.
          </div>
        )}
        <div className="grid gap-4 md:grid-cols-2">
          <label className="flex flex-col text-sm text-slate-300">
            Tool Name
            <input
              className="mt-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </label>
          <label className="flex flex-col text-sm text-slate-300">
            Description
            <input
              className="mt-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>
        </div>
        <div className="flex space-x-3 text-sm">
          <button
            type="button"
            className={`rounded-md px-3 py-1.5 ${uploadMode === 'paste' ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-slate-300'}`}
            onClick={() => setUploadMode('paste')}
          >
            Paste Code
          </button>
          <button
            type="button"
            className={`rounded-md px-3 py-1.5 ${uploadMode === 'file' ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-slate-300'}`}
            onClick={() => setUploadMode('file')}
          >
            Upload File
          </button>
        </div>
        {uploadMode === 'paste' ? (
          <div className="grid gap-3 md:grid-cols-2">
            <label className="flex flex-col text-sm text-slate-300">
              app.py
              <textarea
                className="mt-1 h-48 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm text-white focus:border-indigo-500 focus:outline-none"
                value={appSource}
                onChange={(event) => setAppSource(event.target.value)}
                placeholder="import streamlit as st\n..."
                required
              />
            </label>
            <label className="flex flex-col text-sm text-slate-300">
              requirements.txt (optional)
              <textarea
                className="mt-1 h-48 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm text-white focus:border-indigo-500 focus:outline-none"
                value={requirements}
                onChange={(event) => setRequirements(event.target.value)}
              />
            </label>
          </div>
        ) : (
          <label className="flex flex-col text-sm text-slate-300">
            Upload .py or .zip
            <input
              type="file"
              accept=".py,.zip"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
              className="mt-2"
              required
            />
          </label>
        )}
        {error && <div className="rounded-md bg-red-900/40 border border-red-500 px-3 py-2 text-sm text-red-200">{error}</div>}
        <button
          type="submit"
          disabled={loading || !token}
          className="rounded-md bg-emerald-500 px-4 py-2 font-semibold text-white hover:bg-emerald-400 disabled:opacity-50"
        >
          {loading ? 'Creating…' : 'Create Tool'}
        </button>
      </form>
    </div>
  );
}
