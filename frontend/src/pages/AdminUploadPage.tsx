import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2, ArrowLeft, Shield } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../lib/api';

interface DocumentInfo {
  id: string;
  insurer_name: string | null;
  title: string | null;
  source_url: string | null;
  chunk_count: number;
  uploaded_at: string;
}

export default function AdminUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [insurerName, setInsurerName] = useState('');
  const [title, setTitle] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const qc = useQueryClient();

  const { data: documents, isLoading: docsLoading } = useQuery({
    queryKey: ['admin-documents'],
    queryFn: () => api.get<DocumentInfo[]>('/admin/documents').then((r) => r.data),
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('Please select a PDF file');
      const formData = new FormData();
      formData.append('file', file);
      formData.append('insurer_name', insurerName);
      formData.append('title', title);
      if (sourceUrl) formData.append('source_url', sourceUrl);

      const res = await api.post('/admin/ingest-document', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    },
    onSuccess: (data: { chunk_count: number }) => {
      setStatusMsg({
        type: 'success',
        text: `Successfully ingested document and generated ${data.chunk_count} vector chunks.`,
      });
      setFile(null);
      setInsurerName('');
      setTitle('');
      setSourceUrl('');
      qc.invalidateQueries({ queryKey: ['admin-documents'] });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail;
      setStatusMsg({
        type: 'error',
        text: msg || 'Failed to ingest document. Ensure you have admin privileges and valid API keys.',
      });
    },
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setStatusMsg(null);
    uploadMutation.mutate();
  };

  return (
    <div className="animated-bg min-h-screen p-6 sm:p-10 flex flex-col items-center">
      <div className="w-full max-w-4xl flex flex-col gap-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Link
            to="/chat"
            className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
          >
            <ArrowLeft size={16} /> Back to Advisor
          </Link>
          <div className="flex items-center gap-2">
            <Shield size={18} className="text-blue-400" />
            <span className="text-sm font-semibold">Admin Document Ingestion</span>
          </div>
        </div>

        {/* Upload Card */}
        <div className="glass p-6 sm:p-8 fade-in">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <Upload size={20} className="text-blue-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold">Ingest Policy Document</h2>
              <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>
                Upload insurer policy PDFs to chunk and index in pgvector for RAG citations.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium mb-1" style={{ color: 'var(--c-text-muted)' }}>
                  Insurer Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Haven Life, Northwestern Mutual"
                  value={insurerName}
                  onChange={(e) => setInsurerName(e.target.value)}
                  className="chat-input w-full px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1" style={{ color: 'var(--c-text-muted)' }}>
                  Document Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sample Term Policy Provisions"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="chat-input w-full px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: 'var(--c-text-muted)' }}>
                Source URL (Optional)
              </label>
              <input
                type="url"
                placeholder="https://..."
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                className="chat-input w-full px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: 'var(--c-text-muted)' }}>
                Policy PDF File *
              </label>
              <input
                type="file"
                accept="application/pdf"
                required
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600/20 file:text-blue-300 hover:file:bg-blue-600/30 file:cursor-pointer"
              />
            </div>

            {statusMsg && (
              <div
                className={`flex items-center gap-2 text-xs p-3 rounded-lg ${
                  statusMsg.type === 'success'
                    ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
                    : 'bg-red-500/10 border border-red-500/20 text-red-300'
                }`}
              >
                {statusMsg.type === 'success' ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
                {statusMsg.text}
              </div>
            )}

            <button
              type="submit"
              disabled={uploadMutation.isPending || !file}
              className="btn-primary w-full py-2.5 text-sm flex items-center justify-center gap-2"
            >
              {uploadMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
              {uploadMutation.isPending ? 'Processing & Embedding…' : 'Upload & Index Policy'}
            </button>
          </form>
        </div>

        {/* Existing Documents List */}
        <div className="glass p-6 fade-in">
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <FileText size={16} className="text-blue-400" />
            Ingested Documents Catalog
          </h3>

          {docsLoading ? (
            <div className="flex justify-center p-6">
              <Loader2 size={20} className="animate-spin text-blue-400" />
            </div>
          ) : !documents || documents.length === 0 ? (
            <p className="text-xs text-center py-6" style={{ color: 'var(--c-text-muted)' }}>
              No documents ingested yet. Upload your first PDF above.
            </p>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 rounded-lg"
                  style={{ background: 'var(--c-surface-2)', border: '1px solid var(--c-border)' }}
                >
                  <div>
                    <p className="text-sm font-medium">{doc.title}</p>
                    <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>
                      {doc.insurer_name} · {doc.chunk_count} chunks · {new Date(doc.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-1 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
                    Active
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
