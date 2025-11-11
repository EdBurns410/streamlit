import Link from 'next/link';
import { useRouter } from 'next/router';
import useSWR from 'swr';
import { useMemo, useState } from 'react';
import api from '../../lib/api';
import { useAuth } from '../../components/AuthContext';

interface Build {
  id: number;
  status: string;
  logs?: string;
  image_ref?: string;
  created_at: string;
}

interface Run {
  id: number;
  status: string;
  url?: string;
  logs?: string;
}

interface Version {
  id: number;
  created_at: string;
  builds: Build[];
}

interface ToolDetail {
  id: number;
  name: string;
  description?: string;
  status: string;
  current_image_ref?: string;
  versions: Version[];
  runs: Run[];
}

const fetcher = async (url: string, token: string) => {
  const { data } = await api.get<ToolDetail>(url, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return data;
};

export default function ToolDetailPage() {
  const router = useRouter();
  const { id } = router.query as { id?: string };
  const { token } = useAuth();
  const [busy, setBusy] = useState(false);

  if (!token) {
    return (
      <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
        <div className="mx-auto max-w-xl rounded-xl border border-slate-800 bg-slate-900/60 p-6 text-center">
          <p className="text-sm text-slate-300">Sign in to manage this tool.</p>
        </div>
      </main>
    );
  }

  const { data: tool, mutate } = useSWR(id && token ? [`/v1/tools/${id}`, token] : null, ([url, t]) => fetcher(url, t), {
    refreshInterval: 4000
  });

  const latestVersion = useMemo(() => {
    if (!tool?.versions?.length) return undefined;
    return [...tool.versions].sort((a, b) => b.id - a.id)[0];
  }, [tool]);

  const latestBuild = useMemo(() => {
    if (!latestVersion?.builds?.length) return undefined;
    return [...latestVersion.builds].sort((a, b) => b.id - a.id)[0];
  }, [latestVersion]);

  const latestRun = useMemo(() => {
    if (!tool?.runs?.length) return undefined;
    return [...tool.runs].sort((a, b) => b.id - a.id)[0];
  }, [tool]);

  const triggerBuild = async () => {
    if (!token || !id || !latestVersion) return;
    setBusy(true);
    try {
      await api.post(
        `/v1/tools/${id}/build`,
        { version_id: latestVersion.id },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await mutate();
    } finally {
      setBusy(false);
    }
  };

  const triggerRun = async () => {
    if (!token || !id) return;
    setBusy(true);
    try {
      await api.post(`/v1/tools/${id}/run`, {}, { headers: { Authorization: `Bearer ${token}` } });
      await mutate();
    } finally {
      setBusy(false);
    }
  };

  const triggerStop = async () => {
    if (!token || !id) return;
    setBusy(true);
    try {
      await api.post(`/v1/tools/${id}/stop`, {}, { headers: { Authorization: `Bearer ${token}` } });
      await mutate();
    } finally {
      setBusy(false);
    }
  };

  const shareUrl = latestRun?.url ? `${process.env.NEXT_PUBLIC_TOOL_HOST || 'http://localhost'}${latestRun.url}` : null;

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <div className="mx-auto flex max-w-5xl flex-col gap-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">{tool?.name || 'Loading…'}</h1>
            <p className="text-sm text-slate-400">{tool?.description}</p>
          </div>
          <Link href="/" className="text-sm text-indigo-300 hover:text-indigo-200">
            ← Back to dashboard
          </Link>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 md:col-span-2">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Build logs</h2>
              <button
                onClick={triggerBuild}
                disabled={busy || !latestVersion}
                className="rounded-md bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-400 disabled:opacity-50"
              >
                Queue build
              </button>
            </div>
            <div className="mt-4 h-64 overflow-y-auto rounded-md border border-slate-800 bg-slate-950 p-4 text-sm font-mono">
              {latestBuild?.logs ? latestBuild.logs : 'Build logs will appear here after the first build runs.'}
            </div>
            {latestBuild && (
              <p className="mt-3 text-xs text-slate-400">
                Build #{latestBuild.id} • Status: {latestBuild.status}
              </p>
            )}
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <div>
              <p className="text-sm text-slate-400">Current status</p>
              <p className="text-xl font-semibold text-white">{tool?.status ?? 'unknown'}</p>
            </div>
            <button
              onClick={triggerRun}
              disabled={busy || !tool?.current_image_ref}
              className="w-full rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-400 disabled:opacity-50"
            >
              Start tool
            </button>
            <button
              onClick={triggerStop}
              disabled={busy}
              className="w-full rounded-md bg-rose-500 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-400 disabled:opacity-50"
            >
              Stop tool
            </button>
            {shareUrl && (
              <div className="rounded-md border border-slate-800 bg-slate-950 p-3 text-xs">
                <p className="text-slate-400">Share URL</p>
                <a className="break-all text-indigo-300" href={shareUrl} target="_blank" rel="noreferrer">
                  {shareUrl}
                </a>
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="text-lg font-semibold text-white">Run history</h2>
          <div className="mt-3 space-y-2">
            {tool?.runs?.length ? (
              tool.runs.map((run) => (
                <div key={run.id} className="rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">Run #{run.id}</span>
                    <span className="rounded-full bg-slate-800 px-3 py-1 text-xs uppercase tracking-wide text-slate-300">
                      {run.status}
                    </span>
                  </div>
                  {run.logs && <pre className="mt-2 whitespace-pre-wrap text-xs text-slate-400">{run.logs}</pre>}
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-400">No runs yet. Start the tool to generate a deployment.</p>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
